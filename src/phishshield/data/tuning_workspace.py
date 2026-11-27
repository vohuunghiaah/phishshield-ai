"""Prepare a runtime-only cohort when Colab cannot read the locked CSV on Drive."""

from contextlib import contextmanager
import errno
import hashlib
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pandas as pd
import yaml

from phishshield.data.download import download
from phishshield.data.prepare import CACHE, INDEX, archive_index, read_json
from phishshield.data.splits import LOCK, SPLIT
from phishshield.features.url_features import host_info, parse_url
from phishshield.utils.storage import publish, sha256, verify_saved_artifact


def _unreadable_on_mount(error):
    return error.errno in (errno.ENOENT, errno.EACCES, errno.EPERM, errno.EIO)


def _rebuild_cohort(root, stage, lock):
    verify_saved_artifact(root / SPLIT, lock["sha256"])
    ids = pd.read_csv(root / SPLIT, usecols=["serial_number"]).serial_number
    raw_dir = Path("data/raw/compphish")
    raw = stage / raw_dir
    raw.mkdir(parents=True)
    catalog = root / "configs/compphish_v4.json"
    hashes = {f["name"]: f["sha256"] for f in read_json(catalog)}
    for name in ("Mapping_File.xlsx", "All_HTML.zip"):
        try:
            shutil.copyfile(root / raw_dir / name, raw / name)
        except OSError as exc:
            if not _unreadable_on_mount(exc):
                raise
            (raw / name).unlink(missing_ok=True)
            (stage / "configs").mkdir()
            shutil.copyfile(catalog, stage / "configs" / catalog.name)
            download(stage)
            break
        verify_saved_artifact(raw / name, hashes[name])

    mapping = pd.read_excel(raw / "Mapping_File.xlsx")
    cohort = mapping.loc[mapping.serial_number.isin(ids)].copy()
    cohort["domain"] = [host_info(parse_url(url).hostname)[0] for url in cohort.url]
    cfg = yaml.safe_load((root / "configs/dataset.yaml").read_text("utf8"))
    with ZipFile(raw / "All_HTML.zip") as archive:
        members = archive_index(archive, cfg)
        snapshots = [members[sid] for sid in cohort.serial_number]
        cohort["html_sha256"] = [
            hashlib.sha256(archive.read(info)).hexdigest() for info in snapshots
        ]
        cohort["html_bytes"] = [info.file_size for info in snapshots]
    path = stage / "cohort.csv"
    cohort.to_csv(path, index=False, lineterminator="\n")
    verify_saved_artifact(path, lock["cohort_sha256"])
    return path


@contextmanager
def tuning_workspace(root, runtime):
    lock = read_json(root / LOCK)
    expected = read_json(root / CACHE)["artifacts"][INDEX]
    if expected != lock["cohort_sha256"]:
        raise ValueError("Checksum cohort trong manifest và split lock khác nhau.")
    try:
        digest = sha256(root / INDEX)
    except OSError as exc:
        if not _unreadable_on_mount(exc):
            raise
    else:
        if digest != expected:
            raise ValueError(f"SHA-256 mismatch: {root / INDEX}")
        yield root
        return

    with TemporaryDirectory(dir=runtime) as tmp:
        view = Path(tmp)
        local = runtime / "locked-cohort" / expected / "cohort.csv"
        if not local.exists():
            print(
                "Colab chưa đọc được cohort.csv. Đang tái tạo trong runtime từ CompPhish v4.",
                flush=True,
            )
            with TemporaryDirectory(dir=runtime) as scratch:
                publish(_rebuild_cohort(root, Path(scratch), lock), local)
        verify_saved_artifact(local, expected)
        (view / INDEX).parent.mkdir(parents=True)
        shutil.copyfile(local, view / INDEX)
        # Use the original inputs, trial locks and output directories for both modalities.
        (root / "results").mkdir(exist_ok=True)
        for rel in ("configs", "manifests", "data/features", "data/splits", "results"):
            source = (root / rel).resolve()
            if os.name == "nt":
                # A local directory junction works without elevated symlink privileges.
                from _winapi import CreateJunction

                CreateJunction(str(source), str(view / rel))
            else:
                (view / rel).symlink_to(source, target_is_directory=True)
        yield view
