import numpy as np
import pytest
from phishshield.evaluation.metrics import choose
from phishshield.models.mlp import fit


def test_threshold():
    t, m = choose(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.3, 0.8]), [0.25, 0.5])
    assert t == 0.25 and m["f2"] == 1 and m["fnr"] == 0


def test_pr_area_and_average_precision():
    from phishshield.evaluation.metrics import scores
    from sklearn.metrics import average_precision_score, auc, precision_recall_curve

    labels = np.array([1, 0, 1, 0])
    probs = np.array([0.9, 0.8, 0.7, 0.1])
    result = scores(labels, probs, 0.5)
    precision, recall, _ = precision_recall_curve(labels, probs)
    assert result["pr_auc"] == auc(recall, precision)
    assert result["average_precision"] == average_precision_score(labels, probs)
    assert result["pr_auc"] != result["average_precision"]


@pytest.mark.parametrize(
    "requested,skipped", [(["train", "validation"], [2]), (["train"], [2, 3])]
)
def test_training_label_reader_skips_test_rows(
    tmp_path, monkeypatch, requested, skipped
):
    import pandas as pd
    from phishshield.training.runs import partitions
    from phishshield.data.prepare import INDEX, CACHE, FEATURES
    from phishshield.data.splits import SPLIT
    from phishshield.features.pipeline import schema, VERSION
    from phishshield.utils.storage import save_json, sha256

    mode = "url_only"
    cols = schema(mode)
    ids = [80, 10, 30]
    frames = {
        INDEX: pd.DataFrame({"serial_number": ids, "label": [1, 0, 1]}),
        SPLIT: pd.DataFrame(
            {"serial_number": ids[::-1], "split": ["validation", "test", "train"]}
        ),
        FEATURES[mode]: pd.DataFrame(
            {"serial_number": ids, **{c: [0, 1, 2] for c in cols}}
        ),
    }
    for rel, frame in frames.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(tmp_path / rel, index=False)
    save_json(
        tmp_path / CACHE,
        {
            "artifacts": {k: sha256(tmp_path / k) for k in frames},
            "identity": {"version": VERSION},
            "schemas": {mode: cols},
        },
    )
    original = pd.read_csv
    label_reads = []

    def checked(path, **kwargs):
        if path == tmp_path / INDEX and "label" in kwargs.get("usecols", []):
            assert kwargs["skiprows"] == skipped
            label_reads.append(path)
        if path == tmp_path / FEATURES[mode] and kwargs.get("usecols") != [
            "serial_number"
        ]:
            assert kwargs["skiprows"] == skipped
        return original(path, **kwargs)

    monkeypatch.setattr(pd, "read_csv", checked)
    data = partitions(tmp_path, mode, requested)
    assert label_reads == [tmp_path / INDEX]
    assert data["train"].serial_number.tolist() == [80]
    assert set(data) == set(requested)
    if "validation" in requested:
        assert data["validation"].serial_number.tolist() == [30]


def test_mlp_checkpoint():
    pytest.importorskip("torch")
    x = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0], [3.0, 4.0]])
    y = np.array([0, 0, 1, 1])
    best = []

    def saved(net, history):
        best.append((net, history[-1]["val_loss"]))

    history = fit(
        x,
        y,
        x,
        y,
        42,
        dict(batch_size=2, epochs=2, patience=2, hidden=4, learning_rate=0.01),
        saved,
        "cpu",
    )
    assert len(history) == 2 and best[-1][1] == min(h["val_loss"] for h in history)
    assert np.isfinite(best[-1][0].predict_proba(x)).all()


def test_compare_locks_validation_choice_before_holdout(tmp_path, monkeypatch):
    """Ranking fixture with an outlier seed and a precision/FPR/seed tie."""
    import importlib
    import joblib
    from phishshield.data.prepare import read_json
    from phishshield.features.pipeline import VERSION
    from phishshield.utils.storage import sha256

    module = importlib.import_module("phishshield.evaluation.compare")
    runtime = tmp_path / "runtime"
    root = tmp_path / "workspace"
    root.mkdir()
    root.joinpath("checkpoints").mkdir()
    ckpt = root / "checkpoints/fixture.joblib"
    joblib.dump({"columns": []}, ckpt)
    digest = sha256(ckpt)
    monkeypatch.setattr(
        module, "read_locked_split", lambda root: {"sha256": "fixture-split"}
    )

    def validation_run(root, folder):
        seed = int(folder.name.split("_")[-1])
        mode = folder.parent.name
        member = folder.parent.parent.name
        model = next(k for k, v in module.MEMBERS.items() if v == member)
        f2 = {
            "random_forest": [0.85, 0.85, 0.85],
            "xgboost": [0.99, 0.70, 0.70],
            "mlp": [0.83, 0.83, 0.83],
        }[model][seed - 42]
        return dict(
            seed=seed,
            model=model,
            modality=mode,
            feature_version=VERSION,
            split_hash="fixture-split",
            checkpoint="checkpoints/fixture.joblib",
            checkpoint_sha256=digest,
            threshold=0.35,
            metrics={
                "f2": f2,
                "precision": 0.8 if mode == "url_html" else 0.75,
                "fpr": 0.2 if seed == 42 else 0.1,
            },
        )

    from phishshield.training.runs import run_dir
    from phishshield.utils.storage import save_json

    save_json(root / "manifests/features.json", {})
    fixture_runs = [
        validation_run(root, run_dir(root, m, mode, seed))
        for m in module.MEMBERS
        for mode in module.FEATURES
        for seed in (42, 43, 44)
    ]
    monkeypatch.setattr(module, "collect", lambda root: (fixture_runs, {}))

    def forbidden(*args):
        pytest.fail("Selection accessed holdout")

    monkeypatch.setattr(module, "partitions", forbidden)
    selection = module.compare(root, runtime)
    chosen = selection["primary"]
    assert (chosen["model"], chosen["modality"], chosen["seed"]) == (
        "random_forest",
        "url_html",
        43,
    )
    assert (chosen["threshold"], chosen["checkpoint_sha256"]) == (0.35, digest)
    assert selection["url_fallback"]["modality"] == "url_only"
    assert read_json(root / "manifests/model_selection_v2.json") == selection
    with pytest.raises(FileNotFoundError):
        module.evaluate_test(root, runtime)
    save_json(
        root / "manifests/project_leader_approval.json",
        dict(
            decision="APPROVED",
            reviewer="fixture",
            validation_comparison_reviewed=True,
            selection_sha256="wrong-hash",
        ),
    )
    with pytest.raises(PermissionError):
        module.evaluate_test(root, runtime)
