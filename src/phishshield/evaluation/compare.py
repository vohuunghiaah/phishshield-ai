import joblib
import pandas as pd

from phishshield.data.prepare import FEATURES, read_json, save_frame
from phishshield.data.splits import read_locked_split
from phishshield.evaluation.metrics import scores
from phishshield.features.pipeline import VERSION
from phishshield.training.runs import MEMBERS, partitions
from phishshield.tuning.design import exclusive
from phishshield.tuning.reporting import tuned_run
from phishshield.tuning.search import locked, search_folder
from phishshield.utils.storage import publish, save_json, sha256, verify_saved_artifact


def collect(root):
    """Verify all six search locks and all eighteen matched tuned slots."""
    rows, artifacts = [], {}
    for model in MEMBERS:
        for mode in FEATURES:
            lock = locked(root, model, mode)
            path = search_folder(root, model, mode) / "tuning_lock.json"
            artifacts[path.relative_to(root).as_posix()] = sha256(path)
            for seed in (42, 43, 44):
                run = tuned_run(root, model, mode, seed, lock)
                rows.append(run)
                path = (
                    root
                    / "results/tuned_v2"
                    / model
                    / mode
                    / f"seed_{seed}"
                    / "run_manifest.json"
                )
                artifacts[path.relative_to(root).as_posix()] = sha256(path)
    return rows, artifacts


def compare(root, runtime):
    with exclusive(root / "manifests/selection_writer"):
        return select_models(root, runtime)


def select_models(root, runtime):
    lock = read_locked_split(root)
    rows = []
    runs, artifacts = collect(root)
    for m in runs:
        rows.append(
            {
                **{
                    k: m[k]
                    for k in (
                        "model",
                        "modality",
                        "seed",
                        "checkpoint",
                        "checkpoint_sha256",
                        "threshold",
                    )
                },
                **{k: v for k, v in m["metrics"].items() if k != "confusion_matrix"},
            }
        )
    df = pd.DataFrame(rows)
    save_frame(df, "results/comparisons/v2/per_seed.csv", root, runtime)
    metrics = [k for k in m["metrics"] if k != "confusion_matrix"]
    agg = df.groupby(["model", "modality"])[metrics].agg(["mean", "std"])
    agg.columns = ["_".join(x) for x in agg.columns]
    agg = agg.reset_index().sort_values(
        ["f2_mean", "precision_mean", "fpr_mean", "model", "modality"],
        ascending=[False, False, True, True, True],
    )
    save_frame(agg, "results/comparisons/v2/validation.csv", root, runtime)
    folder = root / "checkpoints/selected_model"

    def install(group, name):
        row = group.sort_values(
            ["f2", "precision", "fpr", "seed"], ascending=[False, False, True, True]
        ).iloc[0]
        fields = ("model", "modality", "threshold", "checkpoint", "checkpoint_sha256")
        info = {k: row[k] for k in fields}
        info.update(
            phase="TUNED_V2",
            seed=int(row.seed),
            split_hash=lock["sha256"],
            feature_version=VERSION,
        )
        directory = folder / name
        dest = directory / "model.joblib"
        info["artifact"] = dest.relative_to(root).as_posix()
        if (directory / "selection.json").exists() and read_json(
            directory / "selection.json"
        ) != info:
            raise RuntimeError("Selection already locked")
        verify_saved_artifact(root / info["checkpoint"], info["checkpoint_sha256"])
        publish(root / info["checkpoint"], dest)
        save_json(directory / "selection.json", info)
        return info

    def best(subset, name):
        group = subset.iloc[0]
        return install(
            df[(df.model == group.model) & (df.modality == group.modality)], name
        )

    fallback = best(agg[agg.modality == "url_only"], "url_fallback")
    info = best(agg, "primary")
    path = root / "manifests/model_selection_v2.json"
    selection = dict(
        phase="TUNED_V2",
        primary=info,
        url_fallback=fallback,
        artifacts=artifacts,
        feature_manifest_sha256=sha256(root / "manifests/features.json"),
    )
    if path.exists() and read_json(path) != selection:
        raise ValueError("Conflicting locked selection")
    if not path.exists():
        save_json(path, selection)
    return selection


def evaluate_test(root, runtime):
    with exclusive(root / "manifests/test_writer"):
        return approved_test(root, runtime)


def approved_test(root, runtime):
    path = root / "manifests/model_selection_v2.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Chưa có {path.name}. Chạy bước select để khóa mô hình trước khi chấm Test."
        )
    selection_hash = sha256(path)
    approval_path = root / "manifests/project_leader_approval.json"
    try:
        approval = read_json(approval_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Thiếu {approval_path}. Sau khi xem báo cáo Validation, Project Leader "
            f"cần duyệt selection có SHA-256 {selection_hash} trước khi chấm Test."
        ) from None
    if (
        approval.get("decision") != "APPROVED"
        or not approval.get("reviewer")
        or approval.get("selection_sha256") != selection_hash
        or approval.get("validation_comparison_reviewed") is not True
    ):
        raise PermissionError(
            f"Kiểm tra {approval_path.name}: cần decision=APPROVED, họ tên reviewer, "
            f"validation_comparison_reviewed=true và selection_sha256={selection_hash}."
        )
    selection = read_json(path)
    runs, fingerprints = collect(root)
    if (
        len(runs) != 18
        or selection["phase"] != "TUNED_V2"
        or fingerprints != selection["artifacts"]
    ):
        raise ValueError("Selection inputs changed")
    verify_saved_artifact(
        root / "manifests/features.json", selection["feature_manifest_sha256"]
    )
    for name in ("primary", "url_fallback"):
        info = selection[name]
        if info != read_json(
            root / "checkpoints/selected_model" / name / "selection.json"
        ):
            raise ValueError("Selection changed")
        chosen = next(
            m
            for m in runs
            if all(m[k] == info[k] for k in ("model", "modality", "seed"))
        )
        if any(
            info[k] != chosen[k]
            for k in (
                "threshold",
                "checkpoint",
                "checkpoint_sha256",
                "feature_version",
                "split_hash",
            )
        ):
            raise ValueError("Selected threshold or checkpoint changed")
        verify_saved_artifact(root / info["artifact"], info["checkpoint_sha256"])
    info = selection["primary"]
    prior = root / "results/metrics/locked_test.json"
    if prior.exists():
        result = read_json(prior)
        if result["selection"] != info:
            raise ValueError("Prior Test result belongs to another selection")
        return result
    bundle = joblib.load(root / info["artifact"])
    test = partitions(root, info["modality"], ["test"])["test"]
    p = bundle["estimator"].predict_proba(test[bundle["columns"]].to_numpy())[:, 1]
    save_frame(
        pd.DataFrame(
            {
                "serial_number": test.serial_number,
                "label": test.label,
                "probability": p,
                "prediction": (p >= info["threshold"]).astype(int),
            }
        ),
        "results/predictions/locked_test.csv",
        root,
        runtime,
    )
    save_json(
        root / "results/metrics/locked_test.json",
        {"selection": info, "metrics": scores(test.label, p, info["threshold"])},
    )
    return info
