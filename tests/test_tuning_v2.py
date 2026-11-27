import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from phishshield.data.prepare import read_json
from phishshield.data.splits import connected_groups
from phishshield.features.pipeline import schema
from phishshield.training import runs
from phishshield.tuning import design as d
from phishshield.tuning import evaluator, reporting
from phishshield.tuning import search as engine
from phishshield.utils.storage import save_json, sha256

PROJECT = Path(__file__).resolve().parents[1]


def test_reporting_import_with_unavailable_notebook_backend():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from phishshield.tuning.reporting import plt\n"
            "assert plt.get_backend().lower() == 'agg'",
        ],
        cwd=PROJECT / "src",
        env={**os.environ, "MPLBACKEND": "module://unavailable_notebook_backend"},
        check=True,
    )


@pytest.mark.parametrize(
    "model,axis,sweep",
    [
        ("random_forest", "n_estimators", [50, 100, 200, 300, 500]),
        ("xgboost", "n_estimators", [100, 200, 250, 300, 500]),
        ("mlp", "hidden", [32, 64, 128, 256]),
    ],
)
def test_locked_candidates(model, axis, sweep):
    base, candidates = d.design(PROJECT, model)
    assert len(candidates) == len({d.digest(v) for v in candidates.values()}) == 24
    assert list(candidates.values()).count(base) == 1
    assert list(candidates.values())[: len(sweep)] == [{**base, axis: v} for v in sweep]
    assert (base, candidates) == d.design(PROJECT, model)


def test_bad_search_budget(tmp_path):
    shutil.copytree(PROJECT / "configs", tmp_path / "configs")
    file = tmp_path / "configs/tuning/experiment.yaml"
    file.write_text(file.read_text("utf8").replace("budget: 24", "budget: 2"), "utf8")
    with pytest.raises(ValueError, match="budget"):
        d.design(tmp_path, "random_forest")


def synthetic():
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(rng.normal(size=(120, 17)), columns=schema("url_only"))
    frame = frame.assign(
        serial_number=np.arange(120),
        label=np.arange(120) % 2,
        domain=[str(i // 3) for i in range(120)],
        html_sha256=[str(i // 3) for i in range(120)],
    )
    frame.loc[3, "html_sha256"] = "0"
    frame["group"] = connected_groups(frame)
    frame["url"] = "https://" + frame.domain + "/"
    return frame


def test_groups_and_candidate_ranking():
    frame = synthetic()
    assert frame.group.iloc[0] == frame.group.iloc[4]
    cv = d.folds(frame, 3, 2026)
    assert cv.equals(d.folds(frame, 3, 2026))
    assert set(cv.fold) == {0, 1, 2} and cv.serial_number.is_unique
    assert cv.groupby("group").fold.nunique().max() == 1
    rows = [
        dict(trial_id=i, f2=0.8, precision=0.5, fpr=0.1)
        for i in ("C001", "C002", "C003")
    ]
    assert d.winner(rows, "C002")["trial_id"] == "C002"
    assert d.winner(rows, "absent")["trial_id"] == "C001"
    for updates in ({"f2": 0.800000000001}, {"precision": 0.6}, {"fpr": 0.09}):
        assert (
            d.winner([*rows, {**rows[0], **updates, "trial_id": "winner"}], "C002")[
                "trial_id"
            ]
            == "winner"
        )


def test_mlp_inner_isolation(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    pytest.importorskip("pyarrow")
    frame = synthetic()
    frame["fold"] = d.folds(frame, 3, 2026).fold
    actual = evaluator.fit
    calls = []

    def observe(x, y, v, vy, seed, hp, save, device):
        fold = len(calls)
        outer = frame.loc[frame.fold == fold, schema("url_only")[0]]
        assert not set(x[:, 0]) & set(outer) and not set(v[:, 0]) & set(outer)
        group = dict(zip(frame[schema("url_only")[0]], frame.group))
        assert not {group[k] for k in x[:, 0]} & {group[k] for k in v[:, 0]}

        def checked(est, trace):
            np.testing.assert_allclose(est.scaler.mean_, x.mean(axis=0))
            save(est, trace)

        calls.append(fold)
        return actual(x, y, v, vy, seed, hp, checked, device)

    monkeypatch.setattr(evaluator, "fit", observe)
    metrics, folds, history = evaluator.evaluate(
        frame,
        "url_only",
        "mlp",
        dict(
            hidden=8,
            batch_size=32,
            epochs=2,
            learning_rate=0.001,
            patience=8,
            dropout=0.1,
            weight_decay=0.001,
        ),
        d.protocol(PROJECT),
        "cpu",
        tmp_path,
    )
    assert len(folds) == len(history) == len(calls) == 3
    assert pd.read_parquet(tmp_path / "oof_predictions.parquet").serial_number.is_unique
    assert np.isfinite(metrics["log_loss"])


@pytest.mark.parametrize("model", ["random_forest", "xgboost"])
def test_search_resume_train_and_tamper(tmp_path, monkeypatch, model):
    pytest.importorskip("pyarrow")
    if model == "xgboost":
        pytest.importorskip("xgboost")
    frame = synthetic()
    mode = "url_only"
    hp = dict(n_estimators=2, n_jobs=1)
    if model == "xgboost":
        hp.update(tree_method="hist", learning_rate=0.06, max_depth=3)
    candidates = {"C001": hp, "C002": {**hp, "n_estimators": 3}}
    plan = {**d.protocol(PROJECT), "budget": 2}
    spec = dict(
        phase="TUNING_V2",
        model=model,
        modality=mode,
        device="cpu",
        protocol=plan,
        dataset_version=4,
        feature_schema="1.0.0",
        cv_hash="synthetic",
        baseline_id="C001",
        search_space={"sensitivity": "n_estimators", "space": {"n_estimators": [2, 3]}},
        candidates=candidates,
    )
    cv = d.folds(frame, 3, 2026)
    (tmp_path / d.CV).parent.mkdir(parents=True)
    cv.to_csv(tmp_path / d.CV, index=False)
    train_frame = frame.drop(columns=["group"])
    access = []

    def read_train(root, mode, names):
        assert names == ["train"]
        access.append(1)
        return {"train": train_frame}

    monkeypatch.setattr(engine, "definition", lambda *args: deepcopy(spec))
    monkeypatch.setattr(engine, "partitions", read_train)
    sentinel = runs.run_dir(tmp_path, model, mode, 42) / "best.joblib"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"immutable V1 fixture")
    digest = sha256(sentinel)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    real_eval = engine.evaluate
    calls = []

    def interrupt(*args):
        calls.append(1)
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return real_eval(*args)

    monkeypatch.setattr(engine, "evaluate", interrupt)
    with pytest.raises(KeyboardInterrupt):
        engine.search(tmp_path, runtime, model, mode, "cpu")
    folder = engine.search_folder(tmp_path, model, mode)
    first = sha256(folder / "C001/trial_manifest.json")
    assert read_json(folder / "C002/trial_manifest.json")["status"] == "INTERRUPTED"
    lock = engine.search(tmp_path, runtime, model, mode, "cpu")
    assert len(calls) == 3 and len(access) == 2
    assert first == sha256(folder / "C001/trial_manifest.json")
    assert engine.search(tmp_path, runtime, model, mode, "cpu") == lock
    assert len(calls) == 3
    assert (folder / "sensitivity.csv").is_file()
    predictions = pd.read_parquet(folder / "C001/oof_predictions.parquet")
    assert sorted(predictions.serial_number) == sorted(frame.serial_number)
    assert predictions.probability.between(0, 1).all()

    monkeypatch.setattr(
        runs, "read_locked_split", lambda root: {"sha256": plan["split_hash"]}
    )
    monkeypatch.setattr(
        runs,
        "config",
        lambda root, name: {"train_seeds": [42], "thresholds": plan["thresholds"]},
    )
    monkeypatch.setattr(
        runs,
        "partitions",
        lambda *args: {"train": frame.iloc[:80], "validation": frame.iloc[80:]},
    )
    m = runs.train(tmp_path, runtime, model, mode, 42, "cpu", "TUNED_V2")
    assert reporting.tuned_run(tmp_path, model, mode, 42, lock) == m
    assert m["hyperparameters"] == lock["selected_hyperparameters"]
    bundle = joblib.load(tmp_path / m["checkpoint"])
    assert bundle["phase"] == "TUNED_V2" and bundle["estimator"].predict(
        frame[schema(mode)].to_numpy()
    ).shape == (120,)
    assert sha256(sentinel) == digest
    (folder / "C001/trial_metrics.json").write_bytes(b"{}")
    with pytest.raises(IOError, match="SHA-256"):
        engine.locked(tmp_path, model, mode)


def test_phase_and_device_guards(tmp_path):
    with pytest.raises(ValueError, match="Device"):
        engine.search(tmp_path, tmp_path, "mlp", "url_only", "cpu")
    with pytest.raises(ValueError, match="phase"):
        runs.train(tmp_path, tmp_path, "mlp", "url_only", 42, phase="TUNING_V2")
    with pytest.raises(FileNotFoundError):
        runs.train(
            tmp_path, tmp_path, "mlp", "url_only", 42, device="cuda", phase="TUNED_V2"
        )


def test_paired_statistics_and_decline(tmp_path):
    out = tmp_path / "reports"
    out.mkdir()
    checkpoint = tmp_path / "model.joblib"
    checkpoint.write_bytes(b"fixture")

    def record(seed, value):
        return dict(
            model="mlp",
            modality="url_only",
            seed=seed,
            checkpoint=checkpoint.name,
            metrics={
                k: value
                for k in reporting.MEASURES
                if k not in ("training_seconds", "inference_ms_per_row", "model_bytes")
            },
        )

    bases = [record(s, v) for s, v in zip((42, 43, 44), (0.5, 0.6, 0.7))]
    tuned = [record(s, v) for s, v in zip((42, 43, 44), (0.4, 0.6, 0.65))]
    lines = reporting.performance(tmp_path, bases, tuned, out)
    summary = pd.read_csv(out / "paired_summary.csv").iloc[0]
    assert summary.f2_baseline_std == pytest.approx(
        0.1
    ) and summary.f2_delta_pp == pytest.approx(-5)
    assert summary.f2_tuned_min == 0.4 and summary.f2_tuned_max == 0.65
    assert "Project Leader review required" in "\n".join(lines)
    assert "NOT_AVAILABLE" in (out / "paired_seeds.csv").read_text()


def test_registered_v1_cannot_be_retrained(tmp_path, monkeypatch):

    save_json(tmp_path / "manifests/baseline_v1.json", {"runs": []})
    with pytest.raises((ValueError, KeyError)):
        runs.train(tmp_path, tmp_path, "random_forest", "url_only", 42)
    assert not (tmp_path / "experiments").exists()


def test_report_updates_all_six_tables_and_protocol(tmp_path, monkeypatch):
    shutil.copytree(PROJECT / "configs", tmp_path / "configs")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/EXPERIMENT_PROTOCOL.md").write_text("Protocol V2", "utf8")
    (tmp_path / "reports/experiments").mkdir(parents=True)
    (tmp_path / "model.joblib").write_bytes(b"synthetic")
    baseline = []
    evidence = {}
    for model in runs.MEMBERS:
        base, candidates = d.design(PROJECT, model)
        bid = next(k for k, v in candidates.items() if v == base)
        for mode in runs.FEATURES:
            evidence[f"{model}/{mode}/42"] = {"estimator": {}}
            folder = engine.search_folder(tmp_path, model, mode)
            save_json(
                folder / "tuning_lock.json",
                dict(selected_trial=bid, selected_hyperparameters=base),
            )
            measures = {k: 0.7 for k in reporting.MEASURES}
            save_json(folder / bid / "trial_metrics.json", dict(**measures))
            for seed in (42, 43, 44):
                record = dict(
                    model=model,
                    modality=mode,
                    seed=seed,
                    checkpoint="model.joblib",
                    metrics=measures,
                )
                baseline.append(record)
                save_json(
                    tmp_path
                    / "results/tuned_v2"
                    / model
                    / mode
                    / f"seed_{seed}"
                    / "run_manifest.json",
                    {**record, "status": "COMPLETED"},
                )
    save_json(tmp_path / "results/baseline_v1/effective_parameters.json", evidence)
    monkeypatch.setattr(reporting, "verify_cv", lambda root: {"sha256": "synthetic"})
    monkeypatch.setattr(reporting, "baseline_runs", lambda root: baseline)
    monkeypatch.setattr(
        reporting,
        "locked",
        lambda root, m, mode: read_json(
            engine.search_folder(root, m, mode) / "tuning_lock.json"
        ),
    )
    monkeypatch.setattr(
        reporting,
        "tuned_run",
        lambda root, m, mode, seed, lock: read_json(
            root / "results/tuned_v2" / m / mode / f"seed_{seed}" / "run_manifest.json"
        ),
    )
    assert reporting.reports(tmp_path) == {"baseline": 18, "tuned": 18}
    doc = (tmp_path / "reports/experiments/hyperparameter_comparison.md").read_text(
        "utf8"
    )
    assert (
        doc.count("| Hyperparameter | Baseline V1 |") == 6
        and "UNCHANGED" in doc
        and "PENDING" not in doc
    )
    assert "selected-hyperparameters-v2" in (
        tmp_path / "docs/EXPERIMENT_PROTOCOL.md"
    ).read_text("utf8")
    assert len(list((tmp_path / "results/comparisons/v2").glob("*.png"))) == 7


@pytest.mark.skipif(
    os.getenv("PHISHSHIELD_GPU_SMOKE") != "1", reason="Explicit real CUDA smoke only"
)
def test_real_cuda_mlp_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    from phishshield.utils.hardware import check_hardware

    hardware = check_hardware("mlp", "cuda")
    assert (
        hardware["actual_device"] == "cuda"
        and hardware["hardware_check_status"] == "READY"
    )
    frame = synthetic()
    frame["fold"] = d.folds(frame, 3, 2026).fold
    hp = dict(
        hidden=32,
        batch_size=16,
        epochs=3,
        learning_rate=0.001,
        patience=8,
        dropout=0.1,
        weight_decay=0.0001,
    )
    _, costs, _ = evaluator.evaluate(
        frame, "url_only", "mlp", hp, d.protocol(PROJECT), "cuda", tmp_path
    )
    assert len(costs) == 3 and pd.read_parquet(
        tmp_path / "oof_predictions.parquet"
    ).shape[0] == len(frame)
    model = joblib.load(tmp_path / "fold_0.joblib")["estimator"]
    assert model.training_device.startswith("cuda")
    print(hardware["gpu_name"], hardware["library_version"], hardware["nvidia_driver"])


def test_frozen_design_rejects_drift(tmp_path, monkeypatch):
    spec = {
        "candidates": {"C001": {"hidden": 64}},
        "protocol": {"budget": 1},
        "search_space": {"hidden": [64]},
    }
    path = tmp_path / "manifests/baseline_v1.json"
    save_json(path, {"runs": []})
    save_json(
        tmp_path / "manifests/tuning_design_v2.json",
        dict(
            plans={"mlp/url_only": d.digest(spec)},
            candidates={"mlp": spec["candidates"]},
            protocol=spec["protocol"],
            spaces={"mlp": spec["search_space"]},
            baseline_registry_sha256=sha256(path),
        ),
    )
    monkeypatch.setattr(engine, "planned_definition", lambda *args: spec)
    assert engine.definition(tmp_path, "mlp", "url_only") == spec
    spec["protocol"]["budget"] = 2
    with pytest.raises(ValueError, match="frozen"):
        engine.definition(tmp_path, "mlp", "url_only")


def test_f2_and_threshold_tie():
    from phishshield.evaluation.metrics import choose

    labels = np.array([1, 1, 0, 0])
    t, s = choose(labels, np.array([0.9, 0.1, 0.8, 0.1]), [0.3, 0.4])
    assert t == 0.4 and s["confusion_matrix"] == [[1, 1], [1, 1]]
    assert s["f2"] == pytest.approx(
        5 * s["precision"] * s["recall"] / (4 * s["precision"] + s["recall"])
    )
