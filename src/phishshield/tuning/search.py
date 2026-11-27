import os
import platform
import time
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from phishshield.data.prepare import FEATURES, read_json
from phishshield.features.pipeline import VERSION
from phishshield.training.runs import config, now, partitions
from phishshield.utils.hardware import check_hardware
from phishshield.utils.storage import publish, save_json, sha256, verify_saved_artifact

from .design import CV, DEVICE, design, digest, exclusive, protocol, verify_cv, winner
from .evaluator import evaluate


def search_folder(root, model, mode):
    if model not in DEVICE or mode not in FEATURES:
        raise ValueError("Unknown search identity")
    return root / "results/tuning_v2" / model / mode


def planned_definition(root, model, mode):
    plan = protocol(root)
    cv = verify_cv(root)
    base, candidates = design(root, model)
    package = Path(__file__).resolve().parents[1]
    sources = [
        "tuning/design.py",
        "tuning/evaluator.py",
        "tuning/search.py",
        "evaluation/metrics.py",
        "training/runs.py",
        "models/mlp.py",
        "data/splits.py",
        "features/pipeline.py",
    ]
    implementation = digest(
        {name: (package / name).read_text("utf8") for name in sources}
    )
    return dict(
        implementation_sha256=implementation,
        phase="TUNING_V2",
        model=model,
        modality=mode,
        protocol=plan,
        search_space=config(root, "tuning/" + model),
        dataset_version=4,
        feature_schema=VERSION,
        cv_hash=cv["sha256"],
        feature_manifest_sha256=cv["feature_manifest_sha256"],
        baseline_id=next(k for k, v in candidates.items() if v == base),
        candidates=candidates,
        device=DEVICE[model],
    )


def design_manifest(root):
    plans = {
        f"{model}/{mode}": digest(planned_definition(root, model, mode))
        for model in DEVICE
        for mode in FEATURES
    }
    return dict(
        phase="TUNING_V2",
        plans=plans,
        protocol=protocol(root),
        candidates={model: design(root, model)[1] for model in DEVICE},
        spaces={model: config(root, "tuning/" + model) for model in DEVICE},
        baseline_registry_sha256=sha256(root / "manifests/baseline_v1.json"),
    )


def freeze_design(root):
    path = root / "manifests/tuning_design_v2.json"
    frozen = design_manifest(root)
    if path.exists() and read_json(path) != frozen:
        raise ValueError("Design already frozen with different inputs")
    save_json(path, frozen)


def definition(root, model, mode):
    spec = planned_definition(root, model, mode)
    frozen = read_json(root / "manifests/tuning_design_v2.json")
    if (
        frozen["plans"][f"{model}/{mode}"] != digest(spec)
        or frozen["protocol"] != spec["protocol"]
        or frozen["candidates"][model] != spec["candidates"]
        or frozen["spaces"][model] != spec["search_space"]
    ):
        raise ValueError("Search differs from frozen design")
    verify_saved_artifact(
        root / "manifests/baseline_v1.json", frozen["baseline_registry_sha256"]
    )
    return spec


def verify_trial(folder, identity, hp, cid):
    meta = read_json(folder / "trial_manifest.json")
    required = {
        "trial_config.json",
        "trial_metrics.json",
        "oof_predictions.parquet",
        "fold_metrics.json",
        "resource_usage.json",
    }
    if meta.get("model") == "mlp":
        required.update(
            {"training_history.json", *(f"fold_{fold}.joblib" for fold in range(3))}
        )
    if (
        meta["status"] != "COMPLETED"
        or meta["identity"] != identity
        or meta["hyperparameters"] != hp
        or meta["trial_id"] != cid
        or meta["phase"] != "TUNING_V2"
        or not required.issubset(meta["artifacts"])
    ):
        raise ValueError(f"Incompatible/incomplete trial {folder}")
    for name, value in meta["artifacts"].items():
        verify_saved_artifact(folder / name, value)
    if read_json(folder / "trial_config.json") != hp:
        raise ValueError("Trial config differs from candidate")
    return read_json(folder / "trial_metrics.json")


def locked(root, model, mode):
    folder = search_folder(root, model, mode)
    spec = definition(root, model, mode)
    lock = read_json(folder / "tuning_lock.json")
    if lock["definition"] != spec or set(lock["trial_manifests"]) != set(
        spec["candidates"]
    ):
        raise ValueError("Tuning definition or membership changed")
    rows = []
    for cid, hp in spec["candidates"].items():
        trial = folder / cid
        verify_saved_artifact(
            trial / "trial_manifest.json", lock["trial_manifests"][cid]
        )
        metrics = verify_trial(trial, digest(spec), hp, cid)
        rows.append(dict(trial_id=cid, **metrics))
    best = winner(rows, spec["baseline_id"])["trial_id"]
    if (
        best != lock["selected_trial"]
        or lock["selected_hyperparameters"] != spec["candidates"][best]
    ):
        raise ValueError("Selected trial mismatch")
    for name, value in lock["artifacts"].items():
        verify_saved_artifact(folder / name, value)
    if read_json(folder / "best_hyperparameters.json") != spec["candidates"][best]:
        raise ValueError("Invalid exported configuration")
    return lock


def search(root, runtime, model, mode, device):
    if DEVICE[model] != device:
        raise ValueError("Device differs from protocol")
    if device == "cuda":
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    folder = search_folder(root, model, mode)
    if (folder / "tuning_lock.json").exists():
        return locked(root, model, mode)
    spec = definition(root, model, mode)
    identity = digest(spec)
    hardware = check_hardware(model, device)
    software = {
        pkg: version(pkg)
        for pkg in ("numpy", "pandas", "scikit-learn", "pyarrow", "joblib")
    }
    software.update(python=platform.python_version())
    software[hardware["library"]] = hardware["library_version"]
    plan = spec["protocol"]
    with exclusive(folder):
        design_file = folder / "search_plan.json"
        if design_file.exists() and read_json(design_file) != spec:
            raise ValueError("Conflicting search plan")
        save_json(design_file, spec)
        train = partitions(root, mode, ["train"])["train"]
        cv = pd.read_csv(root / CV)
        frame = train.merge(cv, on="serial_number", validate="one_to_one")
        if len(frame) != len(cv) or len(frame) != len(train):
            raise ValueError("Incomplete CV membership")
        for cid, hp in spec["candidates"].items():
            path = folder / cid / "trial_manifest.json"
            if not path.exists():
                save_json(
                    path,
                    dict(
                        phase="TUNING_V2",
                        identity=identity,
                        trial_id=cid,
                        hyperparameters=hp,
                        model=model,
                        modality=mode,
                        software=software,
                        device=device,
                        status="PENDING",
                    ),
                )
        rows, manifests = [], {}
        for cid, hp in spec["candidates"].items():
            trial = folder / cid
            path = trial / "trial_manifest.json"
            old = read_json(path) if path.exists() else {}
            if old and (old["identity"] != identity or old["software"] != software):
                raise ValueError(f"Incompatible trial {cid}")
            if old.get("status") != "COMPLETED":
                if old.get("status") == "RUNNING":
                    save_json(
                        trial / "interrupted_attempt.json",
                        {**old, "status": "INTERRUPTED", "end": now()},
                    )
                meta = dict(
                    phase="TUNING_V2",
                    identity=identity,
                    trial_id=cid,
                    model=model,
                    modality=mode,
                    hyperparameters=hp,
                    dataset_version=4,
                    feature_schema=VERSION,
                    cv_hash=spec["cv_hash"],
                    cv_seed=plan["cv_seed"],
                    search_seed=plan["search_seed"],
                    training_seed=plan["training_seed"],
                    software=software,
                    device=device,
                    hardware=hardware,
                    start=now(),
                    status="RUNNING",
                    artifacts={},
                )
                save_json(path, meta)
                start = time.perf_counter()
                try:
                    with TemporaryDirectory(dir=runtime) as tmp:
                        stage = Path(tmp)
                        metrics, fold_metrics, history = evaluate(
                            frame, mode, model, hp, plan, device, stage
                        )
                        artifacts = {
                            "trial_config.json": hp,
                            "fold_metrics.json": fold_metrics,
                            "trial_metrics.json": metrics,
                            "resource_usage.json": {
                                k: metrics[k]
                                for k in (
                                    "training_seconds",
                                    "inference_seconds",
                                    "model_bytes",
                                )
                            },
                        }
                        if history:
                            artifacts["training_history.json"] = history
                        for name, data in artifacts.items():
                            meta["artifacts"][name] = save_json(trial / name, data)
                        for file in stage.iterdir():
                            if file.suffix == ".parquet" or model == "mlp":
                                meta["artifacts"][file.name] = publish(
                                    file, trial / file.name
                                )
                    meta["status"] = "COMPLETED"
                except BaseException as exc:
                    meta.update(
                        status="INTERRUPTED"
                        if isinstance(exc, KeyboardInterrupt)
                        else "FAILED",
                        error=str(exc),
                    )
                    raise
                finally:
                    meta.update(end=now(), runtime_seconds=time.perf_counter() - start)
                    save_json(path, meta)
            metrics = verify_trial(trial, identity, hp, cid)
            rows.append(dict(trial_id=cid, **hp, **metrics))
            manifests[cid] = sha256(path)
        selected = winner(rows, spec["baseline_id"])["trial_id"]
        artifacts = {
            "search_plan.json": sha256(design_file),
            "best_hyperparameters.json": save_json(
                folder / "best_hyperparameters.json", spec["candidates"][selected]
            ),
        }
        from .reporting import trial_summary

        for file in trial_summary(folder, rows, spec, selected):
            artifacts[file.name] = sha256(file)
        save_json(
            folder / "tuning_lock.json",
            dict(
                definition=spec,
                selected_trial=selected,
                selected_hyperparameters=spec["candidates"][selected],
                trial_manifests=manifests,
                artifacts=artifacts,
            ),
        )
    return locked(root, model, mode)
