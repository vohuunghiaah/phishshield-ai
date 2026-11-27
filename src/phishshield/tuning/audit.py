"""Read-only V1 replay. The registry fingerprints historical manifests as well as artifacts."""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from phishshield.data.prepare import FEATURES, read_json
from phishshield.data.splits import read_locked_split
from phishshield.evaluation.metrics import choose
from phishshield.features.pipeline import VERSION, schema
from phishshield.training.runs import MEMBERS, config, partitions, run_dir, verified_run
from phishshield.utils.storage import save_json, sha256, verify_saved_artifact

from .design import DEVICE, protocol


def baseline_runs(root):
    registry = read_json(root / "manifests/baseline_v1.json")
    rows = registry["runs"]
    expected = {
        (m, mode, s) for m in MEMBERS for mode in FEATURES for s in (42, 43, 44)
    }
    if (
        registry["phase"] != "BASELINE_V1"
        or len(rows) != 18
        or {(r["model"], r["modality"], r["seed"]) for r in rows} != expected
    ):
        raise ValueError("Invalid baseline registry")
    for row in rows:
        folder = run_dir(root, row["model"], row["modality"], row["seed"])
        verify_saved_artifact(folder / "run_manifest.json", row["manifest_sha256"])
        if row.get("history_sha256"):
            verify_saved_artifact(folder / "history.json", row["history_sha256"])
        yield verified_run(root, folder)


def audit(root):
    settings = config(root, "experiments")
    split = read_locked_split(root)
    if split["sha256"] != protocol(root)["split_hash"]:
        raise ValueError("Unexpected split")
    expected = {
        run_dir(root, m, mode, s) / "run_manifest.json"
        for m in MEMBERS
        for mode in FEATURES
        for s in settings["train_seeds"]
    }
    if (
        set((root / "experiments").rglob("run_manifest.json")) != expected
        or len(expected) != 18
    ):
        raise ValueError("Duplicate, unexpected or missing baseline slot")
    rows, evidence, table = [], {}, []
    for mode in FEATURES:
        val = partitions(root, mode, ["validation"])["validation"]
        for model in MEMBERS:
            for seed in settings["train_seeds"]:
                folder = run_dir(root, model, mode, seed)
                meta = verified_run(root, folder)
                cfg = read_json(folder / "config.json")
                hw = meta["hardware"]
                hp = config(root, "models")[model]
                if (
                    (
                        meta["model"],
                        meta["modality"],
                        meta["seed"],
                        meta["dataset_version"],
                        meta["feature_version"],
                        meta["split_hash"],
                    )
                    != (model, mode, seed, 4, VERSION, split["sha256"])
                    or cfg
                    != dict(
                        settings=hp,
                        experiment=settings,
                        seed=seed,
                        modality=mode,
                        device=DEVICE[model],
                    )
                    or meta["hyperparameters"] != hp
                    or hw["requested_device"] != hw["actual_device"]
                    or hw["actual_device"] != DEVICE[model]
                    or hw["hardware_check_status"] != "READY"
                    or hw["smoke_test"] != "PASS"
                ):
                    raise ValueError(f"Baseline identity/config/hardware: {folder}")
                bundle = joblib.load(root / meta["checkpoint"])
                cols = schema(mode)
                if (
                    bundle["columns"],
                    bundle["model"],
                    bundle["modality"],
                    bundle["version"],
                ) != (cols, model, mode, VERSION):
                    raise ValueError("Unexpected checkpoint schema")
                est = bundle["estimator"]
                p = est.predict_proba(val[cols].to_numpy())[:, 1]
                t, scores = choose(val.label, p, settings["thresholds"])
                ranking = {"roc_auc", "pr_auc", "average_precision"}
                differences = {
                    k: float(scores[k] - meta["metrics"][k]) for k in sorted(ranking)
                }
                if t != meta["threshold"] or any(
                    not np.allclose(
                        v,
                        meta["metrics"][k],
                        rtol=0,
                        atol=1e-5 if k in ranking else 1e-12,
                    )
                    for k, v in scores.items()
                ):
                    raise ValueError(
                        f"Validation replay mismatch: {folder} {t} {scores}"
                    )
                key = f"{model}/{mode}/{seed}"
                details = dict(
                    probability_sha256=hashlib.sha256(p.tobytes()).hexdigest(),
                    replay_ranking_deltas=differences,
                    explicit=hp,
                    software=meta["software"],
                    hardware=hw,
                    threshold=t,
                )
                if model == "mlp":
                    hist = read_json(folder / "history.json")
                    details.update(
                        best_epoch=min(hist, key=lambda e: e["val_loss"])["epoch"],
                        epochs_run=len(hist),
                        weight_shapes=[list(w.shape) for w in est.weights],
                        scaler=type(est.scaler).__name__,
                        parameter_device=est.training_device,
                    )
                else:
                    params = est.get_params(deep=True)
                    if params["random_state"] != seed:
                        raise ValueError("Estimator seed mismatch")
                    details["estimator"] = {
                        k: ("NaN" if isinstance(v, float) and np.isnan(v) else v)
                        for k, v in params.items()
                    }
                    if model == "xgboost":
                        details["booster"] = json.loads(est.get_booster().save_config())
                        details["tree_dump_sha256"] = hashlib.sha256(
                            "\n".join(est.get_booster().get_dump()).encode()
                        ).hexdigest()
                evidence[key] = details
                row = dict(
                    phase="BASELINE_V1",
                    model=model,
                    modality=mode,
                    seed=seed,
                    manifest=(folder / "run_manifest.json")
                    .relative_to(root)
                    .as_posix(),
                    manifest_sha256=sha256(folder / "run_manifest.json"),
                    history_sha256=sha256(folder / "history.json")
                    if (folder / "history.json").exists()
                    else None,
                    **{
                        k: meta[k]
                        for k in (
                            "checkpoint",
                            "checkpoint_sha256",
                            "config_sha256",
                            "metrics_sha256",
                            "attempt",
                            "threshold",
                        )
                    },
                )
                rows.append(row)
                table.append(
                    dict(
                        model=model,
                        modality=mode,
                        seed=seed,
                        threshold=t,
                        **meta["metrics"],
                    )
                )
    for field in ("checkpoint", "attempt"):
        if len({row[field] for row in rows}) != 18:
            raise ValueError(f"Reused {field}")
    registry = dict(phase="BASELINE_V1", split_hash=split["sha256"], runs=rows)
    target = root / "manifests/baseline_v1.json"
    if target.exists() and read_json(target) != registry:
        raise ValueError("Historical baseline differs from registry")
    if not target.exists():
        save_json(target, registry)
    out = root / "results/baseline_v1"
    save_json(out / "effective_parameters.json", evidence)
    pd.DataFrame(table).to_csv(out / "validation.csv", index=False)
    report = root / "reports/experiments/baseline_v1_audit.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline V1 audit",
        "",
        "18/18 distinct slots, attempts and paths. All checkpoint, config and metric hashes match. Validation replay used each checkpoint, the locked feature order and all 19 thresholds. Classification metrics and threshold match (absolute tolerance 1e-12). Rank metrics use a 1e-5 absolute cross-platform tolerance after observing small cross-platform MLP and parallel RF ranking differences; signed per-run differences are recorded in effective_parameters.json. Historical hardware checks READY.",
        "",
        "| Model | Modality | Seed | Device | F2 | Threshold | Best epoch |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for row in table:
        key = "{model}/{modality}/{seed}".format(**row)
        lines.append(
            f"| {key.replace('/', ' | ')} | {DEVICE[row['model']]} | {row['f2']:.8f} | {row['threshold']} | {evidence[key].get('best_epoch', '—')} |"
        )
    lines.append(
        "\nMaximum absolute MLP replay differences: "
        + ", ".join(
            f"{k} {max(abs(v['replay_ranking_deltas'][k]) for v in evidence.values() if 'weight_shapes' in v):.9g}"
            for k in sorted(ranking)
        )
        + "."
    )
    for mode in FEATURES:
        xrows = [r for r in rows if r["model"] == "xgboost" and r["modality"] == mode]
        trees = {
            evidence[f"xgboost/{mode}/{r['seed']}"]["tree_dump_sha256"] for r in xrows
        }
        lines.append(
            f"\nXGBoost {mode}: {len(trees)} distinct tree dumps, {len({evidence['xgboost/' + mode + '/' + str(r['seed'])]['probability_sha256'] for r in xrows})} distinct Validation probability arrays across three distinct attempts. Estimator random_state matches each seed. Full row/column sampling and CPU hist are consistent with these results."
        )
    lines.append(
        "\nPer-run estimator parameters, native booster settings, versions, hardware and MLP epochs: results/baseline_v1/effective_parameters.json. Manifest and history fingerprints: manifests/baseline_v1.json."
    )
    report.write_text("\n".join(lines) + "\n", "utf8")
