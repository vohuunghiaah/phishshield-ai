# Gate 7 · Nghiệm thu sản phẩm PhishShield AI

Cập nhật 28/11/2026. Trạng thái bên dưới ghi nhận lần nghiệm thu Gate 7 ban đầu. [Kết quả nghiệm thu Full Scan sau khi bổ sung worker cô lập](FULL_SCAN_ACCEPTANCE.md).

**READY FOR LOCAL DEMO. Full Scan thu thập HTML từ Internet: BLOCKED.** Trưởng nhóm Võ Hữu Nghĩa. Ngày 28/11/2026.

## A. Tóm tắt điều hành

Quick Scan và Snapshot Analysis đã chạy trên Windows native, Docker và bản clone sạch dùng hai checkpoint nghiên cứu chính thức. Bản phân phối mã nguồn ở GitHub main. Bộ model được trưởng nhóm cung cấp riêng. [Mã nguồn](https://github.com/vohuunghiaah/phishshield-ai) · [Kịch bản demo](../../docs/product/DEMO_GUIDE.md).

## B. Bảo toàn nghiên cứu

Gate 7 chỉ đọc Drive. Kiểm lại 1.314 SHA-256 theo danh mục đã khóa, số digest sai là 0. Giữ 18 baseline, 144 candidate, 432 trial-fold, sáu tuning lock, 18 tuned run, selection, phê duyệt, Test và SHAP. [Đối soát sau khi đóng gói](research_preservation.json).

## C. Chuyển sang local

Product workspace: C:\dev\phishshield-ai. Đã sao mã nguồn, configs, 13 notebook chính từ 00–12, ba notebook tuning, script phân tích thay cho notebook 13, tests, pyproject/uv.lock, quy trình V1/V2, tài liệu khoa học, bảng và hình. Chỉ sao hai checkpoint phục vụ demo. Notebook công khai đã bỏ outputs/metadata phiên, ID Drive được chuyển thành cấu hình môi trường. T24 public có bốn dòng tổng hợp; T07 bỏ đường dẫn interpreter; T28 tổng hợp theo mục đích/phiên bản. Bản nghiên cứu đầy đủ tiếp tục ở Drive. Tài liệu public Word/PDF đã render 33 trang.

## D. Tính toàn vẹn của model

MODEL_MANIFEST.json ghi role, feature order, cấu hình, ngưỡng và checksum từng payload. SHA256SUMS.txt và MODEL_CARD.md nằm trong ZIP nội bộ, dung lượng 7.477.704 byte. Primary C019 seed 43, fallback C022 seed 44, đều 300 cây. SHA-256 primary 0a78a47a3a46579cabed3da4d68ed926573fd87df3df45afc9d59e24468ef948; fallback 0ce231574e7d61d7fdedb65b85f00c7cc1ecdd5e02859cb48bb4ea955f9a2897. [Hồ sơ integrity](MODEL_INTEGRITY_REPORT.md).

## E. Tính năng sản phẩm

Scanner URL-only trả 17 biến và ngưỡng 0,15. Snapshot Analysis trả 34 biến và ngưỡng 0,20. UI hiển thị xác suất mô hình chưa calibration, thời gian xử lý, phiên bản và đóng góp. Các ví dụ demo chỉ dùng example.org cùng HTML tĩnh tổng hợp.

## F. Safe HTML Fetcher

Đã kiểm implementation hiện hữu và tách khỏi đường gọi của API. Chưa có worker với chính sách egress đã thẩm định. Khi người dùng chọn Full Scan, UI và JSON ghi lý do rồi trả kết quả URL-only. Lỗi checkpoint/schema được trả 503. [An toàn](SECURITY_TEST_REPORT.md).

## G. Khả năng giải thích

Trên mỗi modality, thử TreeExplainer với 32 mẫu Train làm nền, 8 mẫu Validation, đúng 2 class, đúng thứ tự đặc trưng và additivity trên xác suất. Residual tối đa 2,75×10⁻⁸. Demo giữ phương pháp thay biến tuần tự từ median Train, không mang thư viện SHAP/background vào runtime. Dự đoán RF và ngưỡng giữ đúng fixture khóa. [Biên bản](tree_shap.json).

## H. FastAPI và Streamlit

Đã hoàn thiện src/phishshield/api/app.py, inference/service.py và ui/app.py. /health, /ready, /model/info, /performance, /predict, /predict-from-html, /explain và /docs hoạt động. Streamlit gọi REST thật. Có bằng chứng Chromium cho hai nhánh, Full Scan fallback, lỗi input, Swagger, màn hình desktop và mobile. [Ảnh](screenshots/) · [HTTP](http_evidence.json) · [Swagger](browser_modes.json).

## I. Chạy trên Windows

Máy bàn giao đã cài và xác minh model. Mở PowerShell:

```powershell
cd C:\dev\phishshield-ai
.\start.ps1
```

Nếu dịch vụ đã chạy, mở **http://127.0.0.1:8501**. Swagger ở http://127.0.0.1:8000/docs. Máy mới có thể cài trước bằng `.\setup.ps1 -ModelSource 'C:\path\to\phishshield-models-v1.0.0.zip'`. Dừng bằng `.\stop.ps1`. [Minh chứng](LOCAL_DEPLOYMENT_EVIDENCE.md).

## J. Docker

PASS. Đã build và khởi động api/web bằng Compose, kiểm healthy, hai kết quả HTTP đúng modality, gọi UI health, xem logs và down. Hai cổng nghiệm thu 18000/18501. Cả hai dịch vụ bind loopback của host. Docker được vận hành riêng với bản native.

## K. Kiểm thử

Windows CPU: **72 passed, 5 skipped, 0 failed**. Năm mục có điều kiện liên quan dependency/thiết bị nghiên cứu. CI Linux dùng fixture. Local đối chiếu hai checkpoint thực và hai fixture prediction đã lưu. Kiểm thêm lỗi model/schema, threshold equality, HTTP 408/413/422, API unavailable, HTML tĩnh và URL hết hợp lệ. [JUnit](pytest.xml) · [Ma trận an toàn](SECURITY_TEST_REPORT.md).

## L. Hiệu năng

25 lần đo mỗi phép thử sau ba warm-up. HTTP primary P50/P95 184,61/212,78 ms; fallback 143,77/221,06 ms. Ba lần khởi động từ clean clone có UI ready trong 8,65–17,93 giây. Đây là benchmark tuần tự một client. [Bảng và phương pháp](PERFORMANCE_BENCHMARK.md).

## M. GitHub

Initial commit trên main do remote trống. GitHub xác nhận SHA 6853f39b95df9558be4277f23e188091a587335e. CI thành công. Hồ sơ nghiệm thu được thêm bằng commit tiếp theo. [Bàn giao và CI](GITHUB_DELIVERY_REPORT.md).

## N. Clean clone

Clone trực tiếp từ GitHub vào C:\dev\phishshield-ai-verify, cài bằng lockfile và ZIP độc lập. Cả ba lần restart phục vụ hai model khi chặn tiến trình Python đọc Drive, cây phát triển và kết nối đi ngoài loopback. [Bằng chứng](CLEAN_CLONE_VERIFICATION.md).

## O. Tài liệu và demo

README chứa cách cài và chạy thành viên mới. docs/product chứa mười hướng dẫn theo yêu cầu. reports/product có JUnit, JSON, benchmark và năm ảnh. Bản public giữ 28 bảng và 30 hình trong reports/final, cùng hai bộ DOCX/PDF. [Checklist](DEMO_CHECKLIST.md) · [Hướng dẫn cài model](../../docs/product/MODEL_INSTALLATION_GUIDE.md).

## P. Phần còn mở

Full Scan Internet cần thiết kế/kiểm chứng egress riêng trước khi kích hoạt. Quyền public model bundle và license mã nguồn chờ trưởng nhóm xét. Chưa đánh giá scale production, drift hoặc hiệu năng Test độc lập của fallback.

## Q. Nghiệm thu

| Hạng mục | Trạng thái |
|---|---|
| Workspace local, preservation, hai checkpoint và checksum | PASS |
| Quick Scan, Snapshot, runtime CPU, 17/34 features, ngưỡng | PASS |
| Truy xuất website bất kỳ qua Full Scan | BLOCKED |
| Explainability, REST, Streamlit, Windows và Docker | PASS |
| Regression, HTTP, browser, restart và offline | PASS |
| GitHub main, CI và clone sạch | PASS |
| Bộ tài liệu và kịch bản bảo vệ | READY FOR LOCAL DEMO |
