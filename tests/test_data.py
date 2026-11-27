import hashlib
import io
import json
import zipfile
import pandas as pd
import pytest
from phishshield.data.prepare import archive_index
from phishshield.data.splits import assign
from phishshield.data.tuning_workspace import tuning_workspace
from phishshield.utils.storage import (
    publish,
    sha256,
    validate_drive_access,
    verify_saved_artifact,
)


def test_tuning_recovers_only_the_locked_cohort_in_runtime(tmp_path):
    root, runtime = tmp_path / "drive", tmp_path / "runtime"
    runtime.mkdir()
    directories = ("data/splits", "data/features", "data/raw/compphish", "configs", "manifests")
    for rel in directories:
        (root / rel).mkdir(parents=True)
    raw = root / "data/raw/compphish"
    mapping = pd.DataFrame(
        [(2, "https://example.org", 0), (1, "https://example.net", 1)],
        columns=["serial_number", "url", "label"],
    )
    mapping.to_excel(raw / "Mapping_File.xlsx", index=False)
    with zipfile.ZipFile(raw / "All_HTML.zip", "w") as z:
        z.writestr("All_HTML/2.txt", b"sample")
    catalog = [{"name": f.name, "sha256": sha256(f)} for f in raw.iterdir()]
    (root / "configs/compphish_v4.json").write_text(json.dumps(catalog))
    (root / "configs/dataset.yaml").write_text(
        "max_archive_bytes: 99\nmax_member_bytes: 99"
    )
    split = root / "data/splits/assignments.csv"
    split.write_text("serial_number,split\n2,train\n")
    snapshot_hash = hashlib.sha256(b"sample").hexdigest()
    cohort = (
        "serial_number,url,label,domain,html_sha256,html_bytes\n"
        f"2,https://example.org,0,example.org,{snapshot_hash},6\n"
    ).encode()
    expected = hashlib.sha256(cohort).hexdigest()
    index = "data/processed/cohort.csv"
    lock = {"cohort_sha256": expected, "sha256": sha256(split)}
    (root / "data/splits/lock.json").write_text(json.dumps(lock))
    (root / "manifests/features.json").write_text(
        json.dumps({"artifacts": {index: expected}})
    )

    with tuning_workspace(root, runtime) as view:
        assert (view / index).read_bytes() == cohort
        assert (view / "results").samefile(root / "results")
    assert not (root / index).exists()
    (raw / "All_HTML.zip").unlink()
    with tuning_workspace(root, runtime) as view:
        assert (view / index).read_bytes() == cohort

    (root / index).parent.mkdir()
    (root / index).write_bytes(b"unexpected cohort")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        with tuning_workspace(root, runtime):
            pytest.fail("Used a corrupt cohort")


@pytest.mark.parametrize(
    "name,limit", [("../4.txt", 99), ("/4.txt", 99), ("All_HTML/1.txt", 1)]
)
def test_archive_rejected(name, limit):
    with zipfile.ZipFile(io.BytesIO(), "w") as z:
        z.writestr(name, b"123")
        with pytest.raises(ValueError):
            archive_index(z, {"max_member_bytes": limit, "max_archive_bytes": 999})


def test_linked_groups():
    n = 120
    frame = pd.DataFrame(
        dict(
            serial_number=range(n),
            domain=[f"d{i}" for i in range(n)],
            html_sha256=[str(i) for i in range(n)],
            url=[f"u{i}" for i in range(n)],
            label=[i % 2 for i in range(n)],
        )
    )
    frame.loc[1, "domain"] = "d0"
    frame.loc[2, "html_sha256"] = "1"
    s = assign(frame)
    assert s.split.nunique() == 3 and s.split[:3].nunique() == 1
    pd.testing.assert_frame_equal(s, assign(frame))


def test_atomic_copy(tmp_path):
    validate_drive_access(tmp_path)
    assert list(tmp_path.iterdir()) == []
    src, dst = tmp_path / "a", tmp_path / "dir/b"
    src.write_bytes(b"complete")
    digest = publish(src, dst)
    assert sha256(src) == digest == sha256(dst)
    assert publish(src, dst) == digest
    dst.write_bytes(b"broken")
    with pytest.raises(OSError):
        verify_saved_artifact(dst, digest)
