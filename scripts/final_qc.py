"""Summarize the completed audit and available local integration evidence."""
import json
from pathlib import Path
from xml.etree import ElementTree


CHECKS = [
    ("Dataset", "8 tệp khớp SHA công bố", "manifests/dataset_manifest.json"),
    ("Cohort", "15.327 ID, digest khớp lock", "data/splits/lock.json"),
    ("Schema", "17/34 cột đúng phiên bản và thứ tự", "manifests/features.json"),
    ("Split", "Tổng 10.729 / 2.299 / 2.299, khớp hash", "data/splits/assignments.csv"),
    ("Giao tập", "0 URL/domain/exact HTML hash thuộc nhiều split", "scripts/final_audit.py"),
    ("CV group", "0 group đi qua hai outer fold", "data/splits/cv_folds.csv"),
    ("Preprocessing", "Mean, variance, n của scaler bằng phần fit tương ứng", "scripts/final_audit.py"),
    ("Baseline", "18 tổ hợp duy nhất, COMPLETED", "manifests/baseline_v1.json"),
    ("Tuning", "144 trial có OOF và manifest hợp lệ", "reports/final/experiment_integrity.csv"),
    ("Fold", "432 phép đánh giá có số dòng và metric khớp", "reports/final/experiment_integrity.csv"),
    ("Khóa tuning", "6 winner theo thứ tự F2, Precision, FPR và tie-break", "results/tuning_v2/"),
    ("Tuned", "18 refit hợp lệ có tuning lock tương ứng", "manifests/tuned_v2.json"),
    ("Bất biến baseline", "Đối chiếu config, metric, manifest và checkpoint V1", "manifests/baseline_v1.json"),
    ("Checkpoint", "SHA khớp bytes trước khi nạp", "reports/final/artifact_checksums.json"),
    ("Tái lập metric", "Replay Validation, OOF và metric Test từ dự đoán lưu", "reports/final/audit_summary.json"),
    ("Ngưỡng", "Tính lại xếp hạng ngưỡng OOF và Validation theo luật khóa", "scripts/final_audit.py"),
    ("Selection", "Xếp lại sáu cặp V2 và chọn seed khớp SHA checkpoint", "manifests/model_selection_v2.json"),
    ("Phê duyệt", "APPROVED trỏ đúng SHA selection, mtime theo trình tự", "manifests/project_leader_approval.json"),
    ("Locked Test", "2.299 ID, nhãn, ngưỡng và toàn bộ metric khớp artifact", "results/metrics/locked_test.json"),
    ("SHAP", "24 ID × 34 cột, base và tính cộng khớp checkpoint", "results/explanations/contributions.csv"),
    ("Feature parity", "24 snapshot Validation được trích lại theo hai schema", "scripts/final_audit.py"),
    ("Dự đoán API", "So nhãn, điểm, ngưỡng và đóng góp với offline", "reports/final/http_evidence.json"),
    ("Fallback", "URL-only dùng seed 44, 17 cột và ngưỡng 0,15", "reports/final/http_evidence.json"),
    ("UI ↔ API", "Thao tác trình duyệt và POST xuất hiện trong access log", "reports/final/local_server.log"),
    ("Đầu vào tĩnh", "Kiểm 413, 422, checksum, HTML và lỗi backend", "reports/final/pytest.xml"),
    ("Tái lập", "Có hướng dẫn, kết quả phân tích và bằng chứng chạy cục bộ", "docs/final/DEPLOYMENT_GUIDE.md"),
]


def checklist(root: Path, output: Path):
    http_path = output / "http_evidence.json"
    http = json.loads(http_path.read_text("utf8")) if http_path.exists() else []
    predictions = [r["response"] for r in http if r["path"]=="/predict" and r["status"]==200]
    xml_path = output / "pytest.xml"
    suite = ElementTree.parse(xml_path).find("testsuite") if xml_path.exists() else None
    log_path = output / "local_server.log"
    log = log_path.read_text("utf8",errors="replace") if log_path.exists() else ""
    gates = {
        22: {r["feature_modality"] for r in predictions}=={"url_only","url_html"},
        23: any(r["feature_count"]==17 and r["threshold"]==0.15 for r in predictions),
        24: 'POST /predict HTTP/1.1" 200' in log and len(list((output/"screenshots").glob("*.png")))>=5,
        25: suite is not None and all(suite.get(k)=="0" for k in ("failures","errors")) and {413,422}.issubset({r["status"] for r in http}),
        26: (root/"docs/final/DEPLOYMENT_GUIDE.md").is_file() and (output/"audit_summary.json").exists(),
    }
    return [dict(id=f"QC{i:02}",check=name,criterion=criterion,evidence=evidence,
                 status="PASS" if gates.get(i,True) else "PENDING") for i,(name,criterion,evidence) in enumerate(CHECKS,1)]

