import hashlib
import json
import math
import random
from contextlib import contextmanager

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from phishshield.data.prepare import CACHE, INDEX, read_json
from phishshield.data.splits import SPLIT, connected_groups, read_locked_split
from phishshield.training.runs import config, selected_rows
from phishshield.utils.storage import publish, save_json, sha256, verify_saved_artifact

CV = "data/splits/cv_folds.csv"
CV_LOCK = "manifests/cv_lock.json"
DEVICE = {"random_forest": "cpu", "xgboost": "cpu", "mlp": "cuda"}


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


@contextmanager
def exclusive(folder):
    folder.mkdir(parents=True, exist_ok=True)
    guard = folder / ".active"
    guard.mkdir()  # An interrupted writer must be confirmed offline before recovery.
    try:
        yield
    finally:
        guard.rmdir()


def protocol(root):
    return config(root, "tuning/experiment")


def design(root, model):
    plan = protocol(root)
    spec = config(root, "tuning/" + model)
    base = {**config(root, "models")[model], **spec["baseline_defaults"]}
    space = spec["space"]
    axis = spec["sensitivity"]
    if any(base[k] not in v or len(set(v)) != len(v) for k, v in space.items()):
        raise ValueError("Invalid baseline or duplicate search values")
    budget = plan["budget"]
    if not len(space[axis]) <= budget <= math.prod(map(len, space.values())):
        raise ValueError("Invalid trial budget")
    rng = random.Random(plan["search_seed"])
    candidates = [{**base, axis: v} for v in space[axis]]
    while len(candidates) < budget:
        candidate = {**base, **{k: rng.choice(v) for k, v in space.items()}}
        if candidate not in candidates:
            candidates.append(candidate)
    return base, {f"C{i:03}": hp for i, hp in enumerate(candidates, 1)}


def folds(frame, count, seed):
    splitter = StratifiedGroupKFold(n_splits=count, shuffle=True, random_state=seed)
    result = frame[["serial_number", "group"]].copy()
    result["fold"] = -1
    for fold, (train, valid) in enumerate(
        splitter.split(frame, frame.label, frame.group)
    ):
        if any(frame.iloc[ix].label.nunique() != 2 for ix in (train, valid)):
            raise ValueError("Single-class fold")
        result.iloc[valid, result.columns.get_loc("fold")] = fold
    if (result.fold < 0).any() or result.serial_number.duplicated().any():
        raise ValueError("Invalid OOF membership")
    for key in ("group", "url", "domain", "html_sha256"):
        if key in frame and result.groupby(frame[key]).fold.nunique().max() != 1:
            raise ValueError(f"CV leakage: {key}")
    return result


def verify_cv(root):
    split = read_locked_split(root)
    plan = protocol(root)
    meta = read_json(root / CV_LOCK)
    expected = dict(
        split_hash=split["sha256"],
        cohort_hash=split["cohort_sha256"],
        folds=plan["folds"],
        cv_seed=plan["cv_seed"],
        feature_manifest_sha256=sha256(root / CACHE),
    )
    if split["sha256"] != plan["split_hash"] or any(
        meta[k] != v for k, v in expected.items()
    ):
        raise ValueError("CV lock differs from protocol/data")
    verify_saved_artifact(root / CV, meta["sha256"])
    return meta


def prepare_cv(root, runtime):
    if (root / CV_LOCK).exists():
        return verify_cv(root)
    with exclusive(root / "manifests/cv_build"):
        plan = protocol(root)
        split = read_locked_split(root)
        if split["sha256"] != plan["split_hash"]:
            raise ValueError("Unexpected split")
        membership = pd.read_csv(root / SPLIT)
        ids = membership.loc[membership.split == "train", "serial_number"]
        frame = (
            selected_rows(root / INDEX, ids)
            .sort_values("serial_number")
            .reset_index(drop=True)
        )
        if len(frame) != 10729 or set(frame.serial_number) != set(ids):
            raise ValueError("Unexpected train cohort")
        frame["group"] = connected_groups(frame)
        result = folds(frame, plan["folds"], plan["cv_seed"])
        runtime.mkdir(parents=True, exist_ok=True)
        stage = runtime / "cv_folds.csv"
        result.to_csv(stage, index=False, lineterminator="\n")
        if (root / CV).exists():
            verify_saved_artifact(root / CV, sha256(stage))
        checksum = publish(stage, root / CV)
        stats = pd.crosstab(result.fold, frame.label)
        save_json(
            root / CV_LOCK,
            dict(
                sha256=checksum,
                split_hash=split["sha256"],
                cohort_hash=split["cohort_sha256"],
                folds=plan["folds"],
                cv_seed=plan["cv_seed"],
                feature_manifest_sha256=sha256(root / CACHE),
                counts={
                    str(i): {str(k): int(v) for k, v in row.items()}
                    for i, row in stats.iterrows()
                },
            ),
        )
    return verify_cv(root)


def winner(rows, baseline_id):
    return min(
        rows,
        key=lambda row: (
            -row["f2"],
            -row["precision"],
            row["fpr"],
            row["trial_id"] != baseline_id,
            row["trial_id"],
        ),
    )
