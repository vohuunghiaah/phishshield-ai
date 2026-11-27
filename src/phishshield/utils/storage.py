"""Verified Drive mounts and content-checked artifact publication."""

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

DRIVE_FOLDER_ID = os.environ.get("PHISHSHIELD_DRIVE_FOLDER_ID", "")
DRIVE_ROOT = None
RUNTIME_ROOT = "/content/phishshield-ai-run"
TRAIN_SEEDS = [42, 43, 44]
SPLIT_SEED = 2026


def resolve_drive_root(candidate=None, service=None):
    candidate = candidate or os.environ.get("PHISHSHIELD_DRIVE_ROOT")
    if not candidate:
        raise ValueError("Chọn đường dẫn mount thực tế hoặc shortcut trong My Drive.")
    root = Path(candidate).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Cần chọn thư mục Drive.")
    try:
        actual = (
            Path(str(root) + ":user.drive.id").read_text()
            if os.name == "nt"
            else os.getxattr(root, "user.drive.id").decode()
        )
    except (AttributeError, OSError):
        actual = None
    if actual == DRIVE_FOLDER_ID:
        return root
    if not service:
        raise ValueError(
            "Chưa xác minh được Folder ID. Cấp quyền Drive API trong notebook."
        )
    # Prove the mount points to the API parent by reading a unique API-created file.
    from googleapiclient.http import MediaInMemoryUpload
    import time

    files = service.files()
    meta = files.get(
        fileId=DRIVE_FOLDER_ID,
        fields="mimeType,capabilities(canAddChildren)",
        supportsAllDrives=True,
    ).execute()
    if (
        meta["mimeType"] != "application/vnd.google-apps.folder"
        or not meta["capabilities"]["canAddChildren"]
    ):
        raise PermissionError("Cần quyền ghi trong folder chính thức.")
    key = ".phishshield-probe-" + uuid.uuid4().hex
    value = os.urandom(32)
    probe = files.create(
        body={"name": key, "parents": [DRIVE_FOLDER_ID]},
        media_body=MediaInMemoryUpload(value),
        supportsAllDrives=True,
        fields="id",
    ).execute()
    try:
        for _ in range(30):
            if (root / key).is_file() and (root / key).read_bytes() == value:
                return root
            time.sleep(1)
        raise ValueError(
            "Sai đường dẫn hoặc mount chưa đồng bộ. Kiểm tra shortcut trong My Drive."
        )
    finally:
        files.delete(fileId=probe["id"], supportsAllDrives=True).execute()


def validate_drive_access(root):
    with tempfile.NamedTemporaryFile(
        dir=root, prefix=".phishshield-test-", delete=False
    ) as probe:
        path = Path(probe.name)
        value = os.urandom(32)
        probe.write(value)
    try:
        if path.read_bytes() != value:
            raise IOError("Drive readback failed")
    finally:
        path.unlink()


def sha256(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify_saved_artifact(path, digest):
    if sha256(path) != digest:
        raise IOError(f"SHA-256 mismatch: {path}")
    return digest


def publish(source, destination):
    source, destination = Path(source), Path(destination)
    digest = sha256(source)
    if destination.is_file() and sha256(destination) == digest:
        return digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
    try:
        shutil.copyfile(source, tmp)
        verify_saved_artifact(tmp, digest)
        tmp.replace(destination)
        return verify_saved_artifact(destination, digest)
    except OSError as exc:
        raise IOError(
            f"Chưa xác minh {destination}. Bản nguồn còn tại {source}"
        ) from exc
    finally:
        tmp.unlink(missing_ok=True)


def save_json(path, data):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf8", delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    digest = publish(f.name, path)
    Path(f.name).unlink()
    return digest


def sync_source_to_runtime(root, runtime):
    for name in ("src", "configs", "tests", "scripts", "pyproject.toml", "uv.lock"):
        base = root / name
        for p in base.rglob("*") if base.is_dir() else [base]:
            if p.is_file() and "__pycache__" not in p.parts:
                publish(p, runtime / p.relative_to(root))


def stage_dataset_to_runtime(root, runtime):
    manifest = json.loads((root / "manifests/dataset_manifest.json").read_text("utf8"))
    for item in manifest["files"]:
        rel = Path("data/raw/compphish") / item["name"]
        verify_saved_artifact(root / rel, item["sha256"])
        publish(root / rel, runtime / rel)
    return runtime / "data/raw/compphish"


save_checkpoint_to_drive = publish
save_metrics_to_drive = save_json
save_experiment_manifest = save_json


def restore_checkpoint_from_drive(source, destination, digest):
    verify_saved_artifact(source, digest)
    return publish(source, destination)
