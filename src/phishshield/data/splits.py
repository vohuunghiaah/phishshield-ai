"""Lock connected domain and identical-snapshot groups to one partition."""

import numpy as np
import pandas as pd
from phishshield.data.prepare import INDEX, CACHE, read_json, save_frame
from phishshield.utils.storage import save_json, verify_saved_artifact, SPLIT_SEED

SPLIT = "data/splits/assignments.csv"
LOCK = "data/splits/lock.json"
NAMES = ("train", "validation", "test")


def connected_groups(frame):
    rep = {}

    def find(key):
        rep.setdefault(key, key)
        while rep[key] != key:
            rep[key] = rep[rep[key]]
            key = rep[key]
        return key

    for r in frame.itertuples():
        a, b = find("d:" + r.domain), find("h:" + r.html_sha256)
        if a != b:
            rep[b] = a
    return frame.domain.map(lambda d: find("d:" + d))


def assign(frame):
    groups = connected_groups(frame)
    sizes = pd.crosstab(groups, frame.label).reindex(columns=[0, 1], fill_value=0)
    targets = np.outer([0.70, 0.15, 0.15], sizes.sum(axis=0))
    filled = np.zeros_like(targets)
    allocation = {}
    # Start with largest components. Seed resolves equal-sized components.
    order = (
        sizes.sample(frac=1, random_state=SPLIT_SEED)
        .sum(axis=1)
        .sort_values(ascending=False, kind="stable")
    )
    for key in order.index:
        counts = sizes.loc[key].to_numpy()
        cost = (
            ((filled + counts - targets) ** 2 - (filled - targets) ** 2)
            / np.maximum(targets, 1)
        ).sum(axis=1)
        chosen = int(cost.argmin())
        filled[chosen] += counts
        allocation[key] = NAMES[chosen]
    result = frame[["serial_number"]].assign(split=groups.map(allocation))
    check = frame.merge(result, validate="one_to_one")
    if not all(
        check.groupby(k).split.nunique().max() == 1
        for k in ("url", "domain", "html_sha256")
    ):
        raise ValueError("Leakage between partitions")
    if (filled == 0).any():
        raise ValueError("Thiếu một lớp trong split. Kiểm tra kích thước các nhóm.")
    return result


def read_locked_split(root):
    if not (root / LOCK).is_file() or not (root / SPLIT).is_file():
        raise FileNotFoundError("Locked split required for training and selection")
    cache = read_json(root / CACHE)
    digest = cache["artifacts"][INDEX]
    verify_saved_artifact(root / INDEX, digest)
    if cache["audit"]["mapping_differences"]:
        raise ValueError("Mapping mismatch")
    meta = read_json(root / LOCK)
    if meta["cohort_sha256"] != digest:
        raise ValueError("Cohort đã thay đổi so với split khóa.")
    verify_saved_artifact(root / SPLIT, meta["sha256"])
    return meta


def lock_split(root, runtime):
    if (root / LOCK).exists():
        return read_locked_split(root)
    cache = read_json(root / CACHE)
    digest = cache["artifacts"][INDEX]
    verify_saved_artifact(root / INDEX, digest)
    if cache["audit"]["mapping_differences"]:
        raise ValueError("Mapping mismatch")
    frame = pd.read_csv(root / INDEX)
    result = assign(frame)
    if (root / SPLIT).exists():
        existing = pd.read_csv(root / SPLIT)
        if not existing.equals(result):
            raise RuntimeError(
                "Existing split differs from deterministic reconstruction"
            )
    digest_split = save_frame(result, SPLIT, root, runtime)
    counts = pd.crosstab(result.split, frame.label)
    meta = dict(
        seed=SPLIT_SEED,
        cohort_sha256=digest,
        sha256=digest_split,
        counts={
            k: {str(c): int(v) for c, v in row.items()} for k, row in counts.iterrows()
        },
        fractions=result.split.value_counts(normalize=True).to_dict(),
        cross_domain=0,
        cross_url=0,
        cross_html_hash=0,
    )
    save_json(root / LOCK, meta)
    return meta
