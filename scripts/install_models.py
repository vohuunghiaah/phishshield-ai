"""Install exactly the release-pinned inference files from a local archive or mounted folder."""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def install(source, root=ROOT):
    release = json.loads((ROOT / "MODEL_MANIFEST.json").read_text("utf8"))
    with ExitStack() as stack:
        stage = Path(stack.enter_context(TemporaryDirectory(dir=root)))
        archive = None if source.is_dir() else stack.enter_context(ZipFile(source))
        if archive:
            names = archive.namelist()
            allowed = set(release["files"]) | {"MODEL_CARD.md", "SHA256SUMS.txt", "MODEL_MANIFEST.json"}
            if len(names) != len(set(names)) or set(names) != allowed:
                raise ValueError("Unexpected archive contents")
        for name, record in release["files"].items():
            if archive and archive.getinfo(name).file_size != record["bytes"]:
                raise ValueError("Incorrect release file size: " + name)
            with (archive.open(name) if archive else (source / name).open("rb")) as data:
                payload = data.read(record["bytes"] + 1)
            if len(payload) != record["bytes"] or hashlib.sha256(payload).hexdigest() != record["sha256"]:
                raise ValueError("Incorrect release digest: " + name)
            dest = stage / name
            dest.parent.mkdir(exist_ok=True, parents=True)
            dest.write_bytes(payload)
        for name in release["files"]:
            dest = root / name
            dest.parent.mkdir(exist_ok=True, parents=True)
            os.replace(stage / name, dest)
    print("Installed two verified Random Forest checkpoints.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    install(parser.parse_args().source)

