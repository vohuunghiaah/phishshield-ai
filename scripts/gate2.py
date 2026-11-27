"""Audit or prepare the V2 design in an explicitly supplied workspace."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from phishshield.data.prepare import CACHE, read_json
from phishshield.tuning.audit import audit
from phishshield.tuning.design import prepare_cv
from phishshield.tuning.reporting import reports
from phishshield.tuning.search import freeze_design
from phishshield.utils.storage import verify_saved_artifact


def verify_inputs(root):
    dataset = read_json(root / "manifests/dataset_manifest.json")
    cache = read_json(root / CACHE)
    if (dataset["version"], dataset["license"], cache["audit"]["cohort"]) != (
        4,
        "CC BY 4.0",
        15327,
    ):
        raise ValueError("Unexpected dataset identity")
    for item in dataset["files"]:
        verify_saved_artifact(
            root / "data/raw/compphish" / item["name"], item["sha256"]
        )
    for path, checksum in cache["artifacts"].items():
        verify_saved_artifact(root / path, checksum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "prepare", "report"])
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if args.action == "audit":
        verify_inputs(root)
        audit(root)
    elif args.action == "prepare":
        verify_inputs(root)
        with TemporaryDirectory() as stage:
            prepare_cv(root, Path(stage))
        freeze_design(root)
    else:
        print(reports(root))


if __name__ == "__main__":
    main()
