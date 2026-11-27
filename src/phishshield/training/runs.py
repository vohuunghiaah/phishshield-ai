import os
import platform
import uuid
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import yaml
from phishshield.data.prepare import FEATURES, INDEX, CACHE, read_json
from phishshield.data.splits import SPLIT, read_locked_split
from phishshield.evaluation.metrics import choose
from phishshield.features.pipeline import VERSION, schema
from phishshield.models.mlp import fit
from phishshield.utils.hardware import booster_device, check_hardware
from phishshield.utils.storage import publish, save_json, verify_saved_artifact

MEMBERS = {
    "random_forest": "member_01_random_forest",
    "xgboost": "member_02_xgboost",
    "mlp": "member_03_mlp",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def config(root, name):
    return yaml.safe_load((root / f"configs/{name}.yaml").read_text("utf8"))


def selected_rows(path, ids, columns=None):
    identifiers = pd.read_csv(path, usecols=["serial_number"]).serial_number
    skipped = np.flatnonzero(~identifiers.isin(ids)) + 1
    return pd.read_csv(path, usecols=columns, skiprows=skipped.tolist())


def partitions(root, modality, names):
    cache = read_json(root / CACHE)
    path = FEATURES[modality]
    verify_saved_artifact(root / path, cache["artifacts"][path])
    verify_saved_artifact(root / INDEX, cache["artifacts"][INDEX])
    split = pd.read_csv(root / SPLIT)
    ids = split[split.split.isin(names)]
    # Locate rows using only IDs. Skip holdout records at CSV parsing time.
    labels = selected_rows(root / INDEX, ids.serial_number, ["serial_number", "label"])
    df = ids.merge(labels, validate="one_to_one")
    df = df.merge(
        selected_rows(root / path, ids.serial_number),
        on="serial_number",
        validate="one_to_one",
    )
    if (
        len(df) != len(ids)
        or cache["schemas"][modality] != schema(modality)
        or cache["identity"]["version"] != VERSION
    ):
        raise ValueError("Feature schema or sample mismatch")
    return {key: df[df.split == key] for key in names}


def run_dir(root, model, modality, seed):
    return root / "experiments" / MEMBERS[model] / modality / f"seed_{seed}"


def verified_run(root, folder):
    meta = read_json(folder / "run_manifest.json")
    if meta["status"] != "COMPLETED":
        raise RuntimeError(f"Run chưa hoàn tất: {folder}")
    verify_saved_artifact(root / meta["checkpoint"], meta["checkpoint_sha256"])
    verify_saved_artifact(folder / "metrics.json", meta["metrics_sha256"])
    if read_json(folder / "metrics.json") != meta["metrics"]:
        raise ValueError(
            "Validation metrics differ between manifest and verified artifact"
        )
    verify_saved_artifact(folder / "config.json", meta["config_sha256"])
    return meta


def train(root, runtime, model, modality, seed, device="cpu", phase="BASELINE_V1"):
    if phase not in ("BASELINE_V1", "TUNED_V2"):
        raise ValueError("Invalid training phase")
    tuned = phase == "TUNED_V2"
    if not tuned and (root / "manifests/baseline_v1.json").is_file():
        from phishshield.tuning.audit import baseline_runs

        matches = [
            m
            for m in baseline_runs(root)
            if (m["model"], m["modality"], m["seed"], m["device"])
            == (model, modality, seed, device)
        ]
        if len(matches) != 1:
            raise ValueError(
                "Requested slot differs from the immutable Baseline V1 registry"
            )
        return matches[0]
    provenance = {}
    if tuned:
        from phishshield.tuning.search import locked, search_folder
        from phishshield.tuning.design import DEVICE
        from phishshield.utils.storage import sha256

        if device != DEVICE[model]:
            raise ValueError("Device differs from tuning protocol")
        selection = locked(root, model, modality)
        hp = selection["selected_hyperparameters"]
        provenance = dict(
            phase=phase,
            selected_trial=selection["selected_trial"],
            tuning_lock_sha256=sha256(
                search_folder(root, model, modality) / "tuning_lock.json"
            ),
        )
    if model == "mlp" and device == "cuda":
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    hardware = check_hardware(model, device)
    cfg = config(root, "experiments")
    if tuned and (
        cfg["thresholds"] != selection["definition"]["protocol"]["thresholds"]
        or seed not in (42, 43, 44)
    ):
        raise ValueError("Tuned training differs from locked seeds or threshold grid")
    if seed not in cfg["train_seeds"] or modality not in FEATURES:
        raise ValueError("Unknown seed/modality")
    lock = read_locked_split(root)
    if tuned:
        folder = root / "results/tuned_v2" / model / modality / f"seed_{seed}"
    else:
        hp = config(root, "models")[model]
        folder = run_dir(root, model, modality, seed)
    folder.mkdir(parents=True, exist_ok=True)
    guard = folder / ".active"
    try:
        guard.mkdir()
    except FileExistsError:
        raise RuntimeError(
            f"Seed đang chạy hoặc phiên cũ bị ngắt: {guard}. Xem TEAM_WORKFLOW."
        )
    manifest = folder / "run_manifest.json"
    try:
        previous = read_json(manifest) if manifest.exists() else None
        if previous is not None:
            if any(previous.get(k) != v for k, v in provenance.items()):
                raise ValueError("Run and tuning lock differ")
            recorded = previous.get("hardware", {})
            if recorded:
                matches = (
                    recorded.get("actual_device")
                    == recorded.get("requested_device")
                    == device
                )
            else:
                # Gate 1 recorded a device, but did not verify it after fit.
                matches = previous.get("device") == device == "cpu"
            if not matches:
                raise RuntimeError(
                    "Run hiện có dùng thiết bị khác hoặc thiếu bằng chứng thiết bị."
                )
        if previous is not None and previous["status"] == "COMPLETED":
            meta = verified_run(root, folder)
            if (
                meta["split_hash"],
                meta["feature_version"],
                meta["hyperparameters"],
            ) != (lock["sha256"], VERSION, hp):
                raise RuntimeError("Completed run differs from current protocol")
            if not previous.get("hardware"):
                print(
                    "Dùng lại run CPU cũ theo trường device; manifest cũ chưa có hardware check."
                )
            return meta
        attempt = uuid.uuid4().hex
        stage = runtime / "runs" / attempt
        stage.mkdir(parents=True)
        path = (
            (Path("checkpoints/tuned_v2") if tuned else Path("checkpoints"))
            / model
            / modality
            / f"seed_{seed}"
            / attempt
            / "best.joblib"
        )
        versions = {}
        for pkg in (
            "numpy",
            "pandas",
            "joblib",
            "tldextract",
            "lxml",
        ):
            try:
                versions[pkg] = version(pkg)
            except PackageNotFoundError:
                pass
        meta = dict(
            **provenance,
            status="RUNNING",
            model=model,
            modality=modality,
            seed=seed,
            attempt=attempt,
            dataset_version=4,
            split_hash=lock["sha256"],
            feature_version=VERSION,
            hyperparameters=hp,
            software={**versions, hardware["library"]: hardware["library_version"]},
            python=platform.python_version(),
            device=hardware["actual_device"],
            hardware=hardware,
            cpu=hardware["cpu_name"],
            start=now(),
            checkpoint=path.as_posix(),
            recovery="fresh fit from epoch 1",
        )
        meta["config_sha256"] = save_json(
            folder / "config.json",
            dict(
                **provenance,
                settings=hp,
                experiment=cfg,
                seed=seed,
                modality=modality,
                device=device,
            ),
        )
        save_json(manifest, meta)
        try:
            data = partitions(root, modality, ["train", "validation"])
            cols = schema(modality)
            x, v = (data[k][cols].to_numpy() for k in ("train", "validation"))
            y, vy = (data[k].label.to_numpy() for k in ("train", "validation"))
            baseline = np.median(x, axis=0)

            started = time.perf_counter()

            def checkpoint(estimator, history=None):
                if model == "mlp":
                    hardware["parameter_device"] = estimator.training_device
                bundle = dict(
                    **(dict(phase=phase, architecture=hp) if tuned else {}),
                    estimator=estimator,
                    columns=cols,
                    baseline=baseline,
                    version=VERSION,
                    model=model,
                    modality=modality,
                )
                joblib.dump(bundle, stage / "best.joblib", compress=3)
                meta["checkpoint_sha256"] = publish(stage / "best.joblib", root / path)
                if history:
                    save_json(folder / "history.json", history)
                save_json(manifest, meta)

            if model == "mlp":
                history = fit(x, y, v, vy, seed, hp, checkpoint, device)
                save_json(folder / "history.json", history)
            else:
                from phishshield.tuning.evaluator import tree

                estimator = tree(model, hp, seed, device).fit(x, y)
                if model == "xgboost":
                    hardware["booster_device"] = booster_device(estimator, device)
                checkpoint(estimator)
            if tuned:
                meta["training_seconds"] = time.perf_counter() - started
            verify_saved_artifact(root / path, meta["checkpoint_sha256"])
            estimator = joblib.load(stage / "best.joblib")["estimator"]
            started = time.perf_counter()
            probs = estimator.predict_proba(v)[:, 1]
            if tuned:
                meta["inference_ms_per_row"] = (
                    1000 * (time.perf_counter() - started) / len(v)
                )
                meta["model_bytes"] = (stage / "best.joblib").stat().st_size
            threshold, metrics = choose(vy, probs, cfg["thresholds"])
            meta["metrics_sha256"] = save_json(folder / "metrics.json", metrics)
            meta.update(
                status="COMPLETED", end=now(), threshold=threshold, metrics=metrics
            )
            save_json(manifest, meta)
            return verified_run(root, folder)
        except BaseException as exc:
            meta.update(
                status="FAILED", end=now(), error=str(exc), runtime_artifacts=str(stage)
            )
            save_json(manifest, meta)
            raise
    finally:
        guard.rmdir()
