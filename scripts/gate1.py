"""Audit the locked cohort and run small validation-only fits in a separate workspace."""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from phishshield.data.prepare import CACHE, FEATURES, INDEX, read_json, save_frame
from phishshield.data.splits import LOCK, SPLIT
from phishshield.evaluation.metrics import choose
from phishshield.features.pipeline import VERSION, schema
from phishshield.training.runs import MEMBERS, config, partitions, train
from phishshield.utils.storage import (
    publish,
    restore_checkpoint_from_drive,
    save_json,
    sha256,
    verify_saved_artifact,
)

FROZEN = {
    SPLIT: "d3ecbd33e6597b3c75f036c8c58a86f84addf4790743b467666d83d903cdd3e5",
    INDEX: "ef1e5b04d40da1dfe6e37d71481ad40810fa2753b3e9fd78688bf4b5d99a0deb",
    FEATURES[
        "url_only"
    ]: "5bc9d715d4016ea09c860768e832dae5e5c3940df350b1fed9f7e3152db8c691",
    FEATURES[
        "url_html"
    ]: "04534af7288f13e76cb06c685b19c3d8e982522dfd0de487e6b9b94bb7cb8ef0",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def official_artifacts(root):
    return {
        p.relative_to(root).as_posix(): sha256(p)
        for folder in ("experiments", "checkpoints")
        for p in (root / folder).rglob("*")
        if p.is_file()
    }


def audit(root, out):
    catalog = read_json(root / "configs/compphish_v4.json")
    manifest = read_json(root / "manifests/dataset_manifest.json")
    cache = read_json(root / CACHE)
    lock = read_json(root / LOCK)
    require(
        manifest["version"] == 4 and len(catalog) == 8 and manifest["files"] == catalog,
        "CompPhish v4 inventory",
    )
    require(cache["identity"]["version"] == VERSION == "1.0.0", "Feature version")
    require(cache["identity"]["policy"] == "paired-cohort-v1", "Cache policy")
    require(
        config(root, "experiments")["train_seeds"] == [42, 43, 44], "Training seeds"
    )
    source = {f["name"]: f["sha256"] for f in catalog}
    require(source == cache["identity"]["input"], "Cached dataset identity")
    for f in catalog:
        path = root / "data/raw/compphish" / f["name"]
        require(path.stat().st_size == f["size"], f["name"])
        verify_saved_artifact(path, f["sha256"])
    for rel, digest in {**cache["artifacts"], **FROZEN}.items():
        verify_saved_artifact(root / rel, digest)
    require(
        lock["sha256"] == FROZEN[SPLIT]
        and lock["cohort_sha256"] == FROZEN[INDEX]
        and lock["seed"] == 2026,
        "Split lock",
    )
    s = pd.read_csv(root / SPLIT)
    c = pd.read_csv(root / INDEX)
    require(
        c.serial_number.is_unique
        and s.serial_number.is_unique
        and len(c) == len(s) == 15327,
        "Cohort size/IDs",
    )
    joined = c.merge(s, validate="one_to_one")
    require(
        len(joined) == len(c) and joined.label.isin([0, 1]).all(),
        "Label domain or split IDs",
    )
    counts = pd.crosstab(joined.split, joined.label)
    expected = {"train": [5703, 5026], "validation": [1222, 1077], "test": [1222, 1077]}
    require(
        all(counts.loc[k, [0, 1]].tolist() == v for k, v in expected.items()),
        "Label/split counts",
    )
    for key in ["url", "domain", "html_sha256"]:
        require(joined.groupby(key).split.nunique().max() == 1, "Cross-split " + key)
    for mode, rel in FEATURES.items():
        x = pd.read_csv(root / rel)
        columns = schema(mode)
        require(
            list(x) == ["serial_number", *columns]
            and columns == cache["schemas"][mode],
            "Feature columns " + mode,
        )
        require(len(columns) == (17 if mode == "url_only" else 34), "Width " + mode)
        require(
            len(x) == len(c) and set(x.serial_number) == set(c.serial_number),
            "Feature IDs " + mode,
        )
        require(np.isfinite(x[columns].to_numpy()).all(), "Nonfinite features " + mode)
    evidence = {
        "source_sha256": source,
        "artifacts": FROZEN,
        "cohort_rows": len(c),
        "schema": VERSION,
        "labels_by_split": expected,
        "official_artifacts": official_artifacts(root),
        "feature_manifest_sha256": sha256(root / CACHE),
        "split_lock_sha256": sha256(root / LOCK),
    }
    save_json(out / "audit.json", evidence)


def smoke(root, out):
    require(
        read_json(out / "audit.json")["artifacts"] == FROZEN, "Missing Gate 1 audit"
    )
    # Only these 96 real train/validation records can reach any smoke model.
    sets = partitions(root, "url_only", ["train", "validation"])
    selected = pd.concat(
        [
            v.groupby("label", group_keys=False).sample(n=24, random_state=42)
            for v in sets.values()
        ],
        ignore_index=True,
    )
    records = []
    with tempfile.TemporaryDirectory(prefix="phishshield-gate1-") as folder:
        runtime = Path(folder)
        work = runtime / "smoke_workspace"
        shutil.copytree(root / "configs", work / "configs")
        idx = save_frame(selected[["serial_number", "label"]], INDEX, work, runtime)
        split = save_frame(selected[["serial_number", "split"]], SPLIT, work, runtime)
        save_json(work / LOCK, {"cohort_sha256": idx, "sha256": split})
        artifacts = {INDEX: idx}
        for mode, rel in FEATURES.items():
            x = selected[["serial_number"]].merge(
                pd.read_csv(root / rel), validate="one_to_one"
            )
            artifacts[rel] = save_frame(x, rel, work, runtime)
        save_json(
            work / CACHE,
            {
                "identity": {"version": VERSION},
                "artifacts": artifacts,
                "schemas": {m: schema(m) for m in FEATURES},
                "audit": {"mapping_differences": 0},
            },
        )
        hp = config(work, "models")
        hp["random_forest"]["n_estimators"] = 5
        hp["xgboost"]["n_estimators"] = 5
        hp["mlp"].update(epochs=3, patience=2, batch_size=16)
        (work / "configs/models.yaml").write_text(yaml.safe_dump(hp), "utf8")
        for model in MEMBERS:
            for mode in FEATURES:
                meta = train(work, runtime, model, mode, 42, device="cpu")
                location = out / "smoke" / model / mode
                dest = location / "checkpoint.joblib"
                digest = publish(work / meta["checkpoint"], dest)
                require(digest == meta["checkpoint_sha256"], "Published checkpoint")
                restored = runtime / "restored.joblib"
                restore_checkpoint_from_drive(dest, restored, digest)
                v = partitions(work, mode, ["validation"])["validation"]
                x = v[schema(mode)].to_numpy()
                p = joblib.load(restored)["estimator"].predict_proba(x)[:, 1]
                ref = joblib.load(work / meta["checkpoint"])["estimator"].predict_proba(
                    x
                )[:, 1]
                np.testing.assert_array_equal(p, ref)
                t, metrics = choose(
                    v.label.to_numpy(), p, config(work, "experiments")["thresholds"]
                )
                require(
                    t == meta["threshold"] and metrics == meta["metrics"],
                    "Restored validation result",
                )
                metrics_hash = save_json(location / "validation.json", metrics)
                verify_saved_artifact(location / "validation.json", metrics_hash)
                records.append(
                    dict(
                        model=model,
                        modality=mode,
                        seed=42,
                        threshold=t,
                        f2=metrics["f2"],
                        pr_auc=metrics["pr_auc"],
                        average_precision=metrics["average_precision"],
                        checkpoint=dest.relative_to(out).as_posix(),
                        sha256=digest,
                        metrics_sha256=metrics_hash,
                        train_rows=48,
                        validation_rows=48,
                        device=meta["device"],
                        software=meta["software"],
                    )
                )
                save_json(out / "smoke.json", records)
                print(model, mode, "PASS", flush=True)
        # Use a smoke bundle only inside the temporary workspace for explanation checks.
        from phishshield.explainability.report import explain
        from phishshield.inference.service import predict

        save_json(
            work / "checkpoints/selected_model/primary/selection.json",
            {**meta, "artifact": meta["checkpoint"]},
        )
        explain(work, runtime)
        local = read_json(work / "results/explanations/local_vi.json")
        contributions = pd.read_csv(work / "results/explanations/contributions.csv")
        row = contributions.set_index("serial_number").loc[local["serial_number"]]
        delta = abs(local["base"] + float(row.sum()) - local["score"])
        require(delta < 1e-5, "SHAP additivity")
        response = predict(
            work, "https://example.org/", "<title>Demo</title>", "snapshot"
        )
        method = response["explanation"]["method"]
        require(
            "SHAP" not in method.upper() and "trung vị" in method,
            "API explanation label",
        )
        save_json(
            out / "explanation.json",
            {
                "shap_method": "permutation",
                "model": meta["model"],
                "modality": meta["modality"],
                "rows": len(contributions),
                "additivity_error": delta,
                "api_method": method,
                "scope": "isolated smoke checkpoint",
            },
        )


def verify(root, out):
    before = read_json(out / "audit.json")
    for rel, digest in FROZEN.items():
        verify_saved_artifact(root / rel, digest)
    verify_saved_artifact(root / CACHE, before["feature_manifest_sha256"])
    verify_saved_artifact(root / LOCK, before["split_lock_sha256"])
    require(
        official_artifacts(root) == before["official_artifacts"],
        "Official workspace changed",
    )
    records = read_json(out / "smoke.json")
    require(
        read_json(out / "explanation.json")["additivity_error"] < 1e-5, "SHAP evidence"
    )
    require(
        {(r["model"], r["modality"]) for r in records}
        == {(m, k) for m in MEMBERS for k in FEATURES}
        and len(records) == 6,
        "Incomplete smoke matrix",
    )
    for r in records:
        verify_saved_artifact(out / r["checkpoint"], r["sha256"])
        verify_saved_artifact(
            (out / r["checkpoint"]).parent / "validation.json", r["metrics_sha256"]
        )
    save_json(
        out / "verification.json",
        {
            "status": "PASS",
            "smoke_runs": 6,
            "official_artifacts_unchanged": True,
            "locked_inputs_unchanged": True,
            "python": sys.version,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["audit", "smoke", "verify"])
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    root = Path(os.environ["PHISHSHIELD_DRIVE_ROOT"]).resolve(strict=True)
    out = args.out.resolve(strict=True)
    require(
        out.is_relative_to(root / "reports/setup/gate1"),
        "Invalid gate output directory",
    )
    {"audit": audit, "smoke": smoke, "verify": verify}[args.phase](root, out)
