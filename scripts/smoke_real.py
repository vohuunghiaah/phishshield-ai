"""Integration check on a small verified train/validation sample. No holdout evaluation."""

from pathlib import Path
import json
import shutil
import tempfile
import yaml
import pandas as pd
from fastapi.testclient import TestClient
from phishshield.api.app import create_app
from phishshield.data.prepare import INDEX, CACHE, FEATURES, read_json, save_frame
from phishshield.data.splits import SPLIT, LOCK, lock_split
from phishshield.features.pipeline import VERSION
from phishshield.training.runs import partitions, selected_rows, train, run_dir
from phishshield.utils.storage import (
    publish,
    restore_checkpoint_from_drive,
    save_json,
    verify_saved_artifact,
)


def smoke(root, report_path="reports/setup/real_data_smoke.json"):
    with tempfile.TemporaryDirectory(prefix="phishshield-smoke-") as work:
        base = Path(work)
        workspace = base / "workspace"
        runtime = base / "runtime"
        shutil.copytree(root / "configs", workspace / "configs")
        original_lock = lock_split(root, runtime)
        cache = read_json(root / CACHE)
        for name in (INDEX, *FEATURES.values()):
            verify_saved_artifact(root / name, cache["artifacts"][name])
        parts = partitions(root, "url_only", ["train", "validation"])
        options = pd.concat(
            [frame[["serial_number", "label", "split"]] for frame in parts.values()],
            ignore_index=True,
        )
        subset = options.groupby(["split", "label"], group_keys=False).sample(
            n=24, random_state=42
        )
        idx = save_frame(subset.drop(columns="split"), INDEX, workspace, runtime)
        split = save_frame(
            subset[["serial_number", "split"]], SPLIT, workspace, runtime
        )
        save_json(workspace / LOCK, dict(cohort_sha256=idx, sha256=split))
        artifacts = {INDEX: idx}
        for mode, path in FEATURES.items():
            features = subset[["serial_number"]].merge(
                selected_rows(root / path, subset.serial_number), validate="one_to_one"
            )
            artifacts[path] = save_frame(features, path, workspace, runtime)
        save_json(
            workspace / CACHE,
            dict(
                identity={"version": VERSION},
                artifacts=artifacts,
                schemas=cache["schemas"],
                audit={"mapping_differences": 0},
            ),
        )
        hp = yaml.safe_load((workspace / "configs/models.yaml").read_text("utf8"))
        hp["random_forest"]["n_estimators"] = 5
        hp["xgboost"]["n_estimators"] = 5
        hp["mlp"].update(epochs=3, patience=2, batch_size=16)
        (workspace / "configs/models.yaml").write_text(yaml.safe_dump(hp), "utf8")
        records = {}
        for model in hp:
            mode = "url_only" if model == "random_forest" else "url_html"
            meta = train(workspace, runtime, model, mode, 42)
            assert (
                train(workspace, runtime, model, mode, 42)["attempt"] == meta["attempt"]
            )
            # Check the failure/restart path for MLP; the old attempt stays intact.
            if model == "mlp":
                old = meta.copy()
                save_json(
                    run_dir(workspace, model, mode, 42) / "run_manifest.json",
                    {**meta, "status": "FAILED"},
                )
                meta = train(workspace, runtime, model, mode, 42)
                assert old["attempt"] != meta["attempt"]
                verify_saved_artifact(
                    workspace / old["checkpoint"], old["checkpoint_sha256"]
                )
            name = "url_fallback" if mode == "url_only" else "primary"
            dest = workspace / "checkpoints/selected_model" / name
            ckpt = workspace / meta["checkpoint"]
            digest = publish(ckpt, dest / "model.joblib")
            save_json(
                dest / "selection.json",
                {
                    **meta,
                    "artifact": (dest / "model.joblib")
                    .relative_to(workspace)
                    .as_posix(),
                },
            )
            records[model] = dict(
                verified=digest == meta["checkpoint_sha256"], reopened=True
            )
        with tempfile.TemporaryDirectory(
            dir=root / "reports/setup", prefix=".checkpoint-probe-"
        ) as probe:
            dest = Path(probe) / "smoke.joblib"
            publish(ckpt, dest)
            restore_checkpoint_from_drive(dest, runtime / "restored.joblib", digest)
            verify_saved_artifact(runtime / "restored.joblib", digest)
        client = TestClient(create_app(workspace))
        assert client.post("/predict", json={"url": "https://example.org/"}).is_success
        assert client.post(
            "/predict-from-html",
            json={
                "url": "https://example.org/",
                "html": "<form><input type=password></form>",
            },
        ).is_success
        from phishshield.explainability.report import explain

        explain(workspace, runtime)
        local = read_json(workspace / "results/explanations/local_vi.json")
        table = pd.read_csv(workspace / "results/explanations/contributions.csv")
        assert (
            abs(
                local["base"]
                + table.iloc[0].drop("serial_number").sum()
                - local["score"]
            )
            < 1e-5
        )
        report = dict(
            source_split=original_lock["sha256"],
            rows=len(subset),
            per_class_per_partition=24,
            partitions=["train", "validation"],
            models=records,
            checkpoint_roundtrip=True,
            mlp_failed_run_restarted=True,
            smoke_api=True,
            shap_additivity=True,
            official_runs=0,
        )
        save_json(root / report_path, report)
        return report


if __name__ == "__main__":
    from phishshield.utils.storage import resolve_drive_root

    print(json.dumps(smoke(resolve_drive_root()), indent=2))
