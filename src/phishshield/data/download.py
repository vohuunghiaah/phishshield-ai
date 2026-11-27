"""Download only the official, pinned v4 inventory. Never execute archive contents."""

import json
import re
import shutil
import subprocess
from urllib.error import HTTPError
import time
from urllib.request import Request, urlopen
from phishshield.utils.storage import save_json, verify_saved_artifact

URL = "https://data.mendeley.com/public-api/datasets/fmbs4kp9wz/files?folder_id=root&version=4"
SOURCE = "https://data.mendeley.com/datasets/fmbs4kp9wz/4"


def download(root):
    base = root / "data/raw/compphish"
    base.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((root / "configs/compphish_v4.json").read_text("utf8"))
    try:
        with urlopen(URL, timeout=30) as r:
            remote = json.load(r)
        actual = {
            f["filename"]: (f["content_details"]["sha256_hash"], f["size"])
            for f in remote
        }
        if actual != {f["name"]: (f["sha256"], f["size"]) for f in catalog}:
            raise ValueError(
                "Danh mục v4 đã thay đổi. Kiểm tra phiên bản trước khi tải."
            )
    except OSError:
        print("Dùng danh mục v4 đã ghim. Nếu mạng bị chặn, tải thủ công từ", SOURCE)
    need = sum(
        max(0, f["size"] - (base / (f["name"] + ".part")).stat().st_size)
        if (base / (f["name"] + ".part")).exists()
        else f["size"]
        for f in catalog
        if not (base / f["name"]).exists()
    )
    print("Bytes cần tải tối đa:", need, flush=True)
    if shutil.disk_usage(base).free < need:
        raise OSError("Drive không đủ dung lượng.")
    verified = []
    for item in catalog:
        path = base / item["name"]
        if path.exists():
            verify_saved_artifact(path, item["sha256"])
        else:
            partial = path.with_name(path.name + ".part")
            for attempt in range(4):
                offset = partial.stat().st_size if partial.exists() else 0
                if offset == item["size"]:
                    break
                try:
                    req = Request(
                        item["url"],
                        headers={"Range": f"bytes={offset}-"} if offset else {},
                    )
                    with urlopen(req, timeout=90) as stream:
                        if stream.status == 206 and not re.match(
                            rf"bytes {offset}-\d+/{item['size']}$",
                            stream.headers.get("Content-Range", ""),
                        ):
                            raise ValueError("Content-Range không hợp lệ.")
                        with partial.open(
                            "ab" if stream.status == 206 else "wb"
                        ) as out:
                            shutil.copyfileobj(stream, out, 1024 * 1024)
                    if partial.stat().st_size == item["size"]:
                        break
                except HTTPError as error:
                    if error.code in (403, 429) and shutil.which("curl"):
                        subprocess.run(
                            [
                                "curl",
                                "-fsSL",
                                "--retry",
                                "3",
                                "-C",
                                "-",
                                "-o",
                                str(partial),
                                item["url"],
                            ],
                            check=True,
                        )
                        break
                    raise
                except OSError:
                    if attempt == 3:
                        raise
                    time.sleep(2**attempt)
            verify_saved_artifact(partial, item["sha256"])
            partial.replace(path)
        if path.stat().st_size != item["size"]:
            raise IOError(f"Sai kích thước: {path}")
        verify_saved_artifact(path, item["sha256"])
        verified.append(item)
        print("Verified", path.name, flush=True)
    manifest = root / "manifests/dataset_manifest.json"
    record = json.loads(manifest.read_text("utf8")) if manifest.exists() else {}
    record.update(
        source=SOURCE,
        doi="10.17632/fmbs4kp9wz.4",
        license="CC BY 4.0",
        version=4,
        files=verified,
        bytes=sum(f["size"] for f in verified),
    )
    save_json(manifest, record)
    return record
