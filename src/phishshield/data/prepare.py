"""Audit the author mapping and stream bounded snapshot members without unpacking to disk."""

from collections import Counter
import hashlib
import json
from pathlib import PurePosixPath
import re
from stat import S_ISLNK
import zipfile
import pandas as pd
import yaml

from phishshield.features.pipeline import VERSION, extract_features, schema
from phishshield.features.url_features import host_info, parse_url
from phishshield.utils.storage import (
    publish,
    save_json,
    stage_dataset_to_runtime,
    verify_saved_artifact,
)

INDEX = "data/processed/cohort.csv"
FEATURES = {m: f"data/features/{m}/features.csv" for m in ("url_only", "url_html")}
CACHE = "manifests/features.json"
AUDIT = "reports/dataset/dataset_audit.md"


def read_json(path):
    return json.loads(path.read_text("utf8"))


def archive_index(z, cfg):
    members = {}
    total = 0
    for info in z.infolist():
        name = PurePosixPath(info.filename)
        if (
            name.is_absolute()
            or ".." in name.parts
            or "\\" in info.filename
            or ":" in info.filename
            or S_ISLNK(info.external_attr >> 16)
            or info.flag_bits & 1
        ):
            raise ValueError("Unsafe archive entry")
        total += info.file_size
        if total > cfg["max_archive_bytes"] or info.file_size > cfg["max_member_bytes"]:
            raise ValueError("Archive exceeds configured bounds")
        if info.is_dir():
            continue
        match = re.fullmatch(r"All_HTML/(\d+)\.txt", info.filename)
        if not match or int(match[1]) in members:
            raise ValueError(f"Unexpected or ambiguous member: {info.filename!r}")
        members[int(match[1])] = info
    return members


def save_frame(frame, rel, root, runtime):
    path = runtime / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    return publish(path, root / rel)


def prepare(root, runtime):
    manifest = read_json(root / "manifests/dataset_manifest.json")
    cfg = yaml.safe_load((root / "configs/dataset.yaml").read_text("utf8"))
    identity = {
        "version": VERSION,
        "input": {f["name"]: f["sha256"] for f in manifest["files"]},
        "policy": "paired-cohort-v1",
    }
    if (root / CACHE).exists():
        cache = read_json(root / CACHE)
        if cache["identity"] == identity:
            if cache["audit"]["mapping_differences"]:
                raise ValueError("Mapping mismatch; inspect dataset_audit.md")
            for rel, digest in cache["artifacts"].items():
                verify_saved_artifact(root / rel, digest)
            return cache
    raw = stage_dataset_to_runtime(root, runtime)
    mapping = pd.read_excel(raw / "Mapping_File.xlsx")
    supplied = pd.read_excel(raw / "All_Features_threshold90.xlsx")
    keys = ["serial_number", "url", "label"]
    if (
        list(mapping) != keys
        or mapping.serial_number.isna().any()
        or mapping.serial_number.duplicated().any()
    ):
        raise ValueError("Schema hoặc serial_number trong bảng ánh xạ không hợp lệ")
    if not mapping.label.isin([0, 1]).all():
        raise ValueError("Nhãn ngoài {0,1}")
    mismatch = len(
        mapping.merge(supplied[keys], on=keys, how="outer", indicator=True).query(
            "_merge != 'both'"
        )
    )
    normalized = mapping.url.fillna("").str.strip()
    conflicts = set(
        normalized[mapping.label.groupby(normalized).transform("nunique") > 1]
    )
    all_hashes = Counter()
    counts = Counter()
    issues, records, values = [], [], []
    with zipfile.ZipFile(raw / "All_HTML.zip") as z:
        members = archive_index(z, cfg)
        orphans = len(set(members) - set(mapping.serial_number))
        for row in mapping.itertuples(index=False):
            sid, url, label = row
            problems = []
            domain = None
            try:
                domain = host_info(parse_url(url).hostname)[0]
            except (ValueError, UnicodeError):
                problems.append("invalid_url")
            if isinstance(url, str) and url.strip() in conflicts:
                problems.append("conflicting_url")
            info = members.get(sid)
            html = None
            if info is None:
                problems.append("missing_html")
            else:
                payload = z.read(info)
                digest = hashlib.sha256(payload).hexdigest()
                all_hashes[digest] += 1
                try:
                    html = payload.decode("utf-8-sig")
                except UnicodeDecodeError:
                    html = payload.decode("cp1252", errors="replace")
                    counts["legacy_decoding"] += 1
                if not html.strip():
                    problems.append("empty_html")
            if not problems:
                try:
                    features = extract_features(url, html)
                except (ValueError, UnicodeError, OverflowError):
                    problems.append("parse_error")
                else:
                    values.append({"serial_number": sid, **features})
                    records.append(
                        dict(
                            serial_number=sid,
                            url=url,
                            label=label,
                            domain=domain,
                            html_sha256=digest,
                            html_bytes=info.file_size,
                        )
                    )
            if problems:
                counts.update(problems)
                issues.append({"serial_number": sid, "reasons": ",".join(problems)})
    if not records:
        raise ValueError("Không có cohort hợp lệ")
    frame = pd.DataFrame(values)
    artifacts = {}
    for modality, rel in FEATURES.items():
        artifacts[rel] = save_frame(
            frame[["serial_number", *schema(modality)]], rel, root, runtime
        )
    artifacts[INDEX] = save_frame(pd.DataFrame(records), INDEX, root, runtime)
    issues_rel = "data/interim/exclusions.csv"
    artifacts[issues_rel] = save_frame(
        pd.DataFrame(issues, columns=["serial_number", "reasons"]),
        issues_rel,
        root,
        runtime,
    )
    n_features = len(supplied.columns.difference(keys))
    summary = dict(
        samples=len(mapping),
        legitimate=int((mapping.label == 0).sum()),
        phishing=int(mapping.label.sum()),
        snapshots=len(members),
        precomputed_features=n_features,
        mapping_differences=mismatch,
        duplicate_url_rows=int(normalized.duplicated().sum()),
        conflicting_url_keys=len(conflicts),
        duplicate_html_rows=sum(c - 1 for c in all_hashes.values()),
        orphan_html=orphans,
        missing_html=counts["missing_html"],
        empty_html=counts["empty_html"],
        invalid_url=counts["invalid_url"],
        parse_error=counts["parse_error"],
        legacy_decoding=counts["legacy_decoding"],
        precomputed_missing=int(supplied.isna().sum().sum()),
        cohort=len(records),
        excluded=len(issues),
    )
    text = [
        "# Kiểm định CompPhish v4",
        "",
        "Đếm trực tiếp từ hai bảng XLSX và ZIP snapshot đã xác minh SHA-256.",
        "",
        "| Chỉ tiêu | Giá trị |",
        "|---|---:|",
        *[f"| {k} | {v} |" for k, v in summary.items()],
        "",
        f"Schema ánh xạ: {', '.join(keys)}. Nhãn 0 = legitimate, 1 = phishing.",
        "Đối chiếu số công bố: "
        + str({k: summary[k] == v for k, v in cfg["expected"].items()}),
        "Các ID loại và lý do nằm trong data/interim/exclusions.csv.",
        "Loại ID, nhãn, tên tệp, hash và 70 cột tính sẵn khỏi đầu vào mô hình. Hai modality dùng cùng cohort.",
        "Giữ các bản trùng còn hợp lệ trong cùng nhóm khi chia. HTML lỗi cú pháp có thể được lxml phục hồi.",
    ]
    report = runtime / AUDIT
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(text) + "\n", "utf8")
    artifacts[AUDIT] = publish(report, root / AUDIT)
    manifest["audit"] = summary
    save_json(root / "manifests/dataset_manifest.json", manifest)
    cache = dict(
        identity=identity,
        artifacts=artifacts,
        schemas={m: schema(m) for m in FEATURES},
        audit=summary,
    )
    save_json(root / CACHE, cache)
    if mismatch:
        raise ValueError("Hai bảng nguồn không khớp. Kiểm tra dataset_audit.md")
    return cache
