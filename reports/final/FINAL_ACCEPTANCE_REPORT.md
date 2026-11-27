*Bản công khai tóm lược bằng chứng Gate 6. Các log, danh mục theo mẫu và tệp gốc do trưởng nhóm lưu nội bộ.*

# Biên bản nghiệm thu PhishShield AI

**FINAL PASS — phạm vi hồ sơ nghiên cứu đã khóa và ứng dụng demo local.**  
Ngày 28/11/2026 · Trưởng nhóm Võ Hữu Nghĩa (Vohuunghia) · Random Forest: Gịp Xương Thanh Quyền · XGBoost: Vũ Thị Tuyết Trang · MLP: Võ Hữu Nghĩa.

## A. Tóm tắt điều hành

Nhóm bàn giao giao thức 35 chương, báo cáo đồ án 17 mục, 28 bảng, 30 hình, bộ 82 câu phản biện và bản demo dùng hai checkpoint chính thức. Trên 2.299 mẫu Test, mô hình chính phát hiện đúng 1.060 mẫu phishing, bỏ sót 17 mẫu và cảnh báo nhầm 147 mẫu hợp lệ. Bằng chứng thực nghiệm và bằng chứng vận hành nằm trong hai hồ sơ riêng để người đọc kiểm tra độc lập. [Kiểm toán](FINAL_EXPERIMENT_AUDIT.md) · [Bằng chứng HTTP](http_evidence.json).

## B. Toàn vẹn thực nghiệm

Đã đối chiếu tám tệp nguồn, feature/split/CV lock, 18 run V1, 144 trial, 432 trial-fold evaluations và 18 run V2. 36 checkpoint chính thức tái tạo metric Validation. 144 OOF đúng membership, ba fold mỗi trial khớp metric. Với MLP, mean, variance và số dòng scaler khớp đúng phần dữ liệu được phép học ở final fit và inner-fit. SHA của danh mục 1.314 digest bằng nhau trước và sau khi chạy lại phân tích. Tệp gốc được sử dụng theo chế độ đọc. Inventory (kho nghiên cứu nội bộ) · Danh mục SHA (kho nghiên cứu nội bộ) · [QC01–QC26](tables/T27_qc.csv).

## C. Giao thức và phương pháp

CompPhish v4 có cohort 15.327 mẫu. Split theo connected component của registrable domain và HTML SHA-256. Train, Validation, Test lần lượt có 10.729, 2.299 và 2.299 mẫu. Tuning chỉ sử dụng Train. Mô hình/seed và điểm vận hành chọn bằng Validation. Approval đã lưu tên Vohuunghia và đúng SHA selection. Giao thức Final tổng hợp hậu nghiệm. Đối chiếu tham khảo ProtoEnergy-IDS ở mức cấu trúc tài liệu, dùng bản DOCX V01 và văn bản V02_EXT có trong workspace. [Master Protocol](../../docs/final/PHISHSHIELD_AI_EXPERIMENT_PROTOCOL_AND_ANALYSIS.md).

## D. Phân tích thống kê

Ghép từng run V1/V2 theo model, modality và seed. Bảng cung cấp mean, SD mẫu, min, max và thay đổi tuyệt đối/tương đối. Ba seed cùng split giới hạn kết luận về tổng quát hóa. Baseline ablation thêm HTML tăng F2 trung bình 6,005–6,599 điểm phần trăm trên Validation. Ở pha V2, việc chọn cấu hình khác nhau theo modality cũng góp vào hiệu đo được. [Ablation](tables/T18_ablation.csv) · [Thống kê ghép cặp](tables/T19_paired_statistics.csv).

## E. Kết quả baseline và tuned

Hai trong sáu cặp tăng F2 trên Validation, gồm RF URL+HTML (+0,110 điểm phần trăm) và MLP URL+HTML (+0,476). XGBoost URL-only có chênh lệch âm lớn nhất (−1,023 điểm), cùng FPR tăng 10,229 điểm. XGBoost baseline URL+HTML có F2 trung bình cao nhất khi nhìn cả hai pha. Trong phạm vi lựa chọn TUNED_V2, RF URL+HTML đứng đầu theo quy tắc đã khóa. [Kết quả baseline](tables/T12_baseline_summary.csv) · [Kết quả tuned](tables/T16_tuned_summary.csv).

## F. Siêu tham số

Hai nhánh RF chọn 300 cây. XGBoost chọn 100 vòng cho URL và 300 vòng cho URL+HTML. MLP chọn lớp ẩn 256 cho cả hai. F11–F13 so các sweep có kiểm soát về số cây, số vòng và chiều rộng. Thay đổi đồng thời nhiều tham số trong một candidate chỉ hỗ trợ kết luận về cả cấu hình. [Bảng 144 trial](tables/T13_trials.csv) · [Thay đổi tham số theo từng cặp](tables/T14_parameters.csv).

## G. Mô hình và Locked Test

| Vai trò | Checkpoint được nạp | Trial / seed | Schema | Ngưỡng |
|---|---|---|---|---:|
| Primary | checkpoints/selected_model/primary/model.joblib | RF C019 / 43 | URL+HTML, 34 cột | 0,20 |
| Fallback | checkpoints/selected_model/url_fallback/model.joblib | RF C022 / 44 | URL, 17 cột | 0,15 |

Hai SHA bắt đầu bằng 0a78a47a3a46 và 0ce231574e7d. Bản selection kèm checksum đầy đủ, checkpoint nguồn và phiên bản. Primary đạt Accuracy 92,866%, Precision 87,821%, Recall 98,422%, F2 96,102%, FPR 12,029%. Confusion matrix theo thứ tự nhãn [0,1] là [[1075,147],[17,1060]]. Chưa có đánh giá Test riêng cho fallback/XGBoost theo thiết kế khóa. [Hai bundle](tables/T20_selection.csv) · [Metric Test](tables/T21_test_metrics.csv).

## H. Khả năng giải thích

32 mẫu Train làm nền và 24 mẫu Validation làm tập giải thích. Kiểm tra ID, feature order, điểm nền, điểm checkpoint, tính cộng và global mean absolute SHAP. Sai lệch cộng tối đa 1,78 × 10⁻¹⁵. API trả attribution tuần tự từ vector trung vị Train theo thứ tự cột; phản hồi ghi rõ tên phương pháp. [Global importance](tables/T23_shap.csv) · [SHAP local](figures/F26_shap_local.png).

## I. FastAPI

Uvicorn thực sự phục vụ trên 127.0.0.1:8765 trong phiên nghiệm thu. Đã gọi /health bằng curl; requests đã thực hiện 14 yêu cầu gồm readiness, metadata, cả hai nhánh predict, explain, input lỗi, Swagger và performance. Trình duyệt còn dùng nút Execute trong Swagger để gửi GET /health và nhận 200. Đối chiếu điểm và đóng góp REST với offline ở sai số tuyệt đối tối đa 10⁻¹². Cả hai nhánh kiểm SHA trước khi deserialize và kiểm schema trước khi suy luận. [HTTP](http_evidence.json) · curl (kho nghiên cứu nội bộ) · Swagger (kho nghiên cứu nội bộ) · [API reference](../../docs/final/API_REFERENCE.md).

## J. Streamlit

Ứng dụng thực sự chạy ở 127.0.0.1:8766 và gọi REST qua HTTP. Playwright nhập URL, gửi snapshot tĩnh, kiểm đúng nhánh, mở trang giải thích và hiệu năng, rồi kiểm viewport 390 × 844. Access log Uvicorn có hai POST tương ứng và GET /performance. Ảnh được chụp sau khi Streamlit hoàn tất lượt render. [URL-only](screenshots/01_url_fallback.png) · [URL+HTML](screenshots/02_html_primary.png) · [Giải thích](screenshots/03_explanation.png) · [Hiệu năng](screenshots/04_locked_test.png) · [Màn hình hẹp](screenshots/05_mobile.png) · Access log (kho nghiên cứu nội bộ).

## K. Bằng chứng kiểm thử

Pytest ghi **66 passed, 1 skipped, 0 failed, 0 errors**. Mục bỏ qua là kiểm thử MLP CUDA thật có điều kiện opt-in. Suite có fixture tổng hợp cho các đường lỗi, tách biệt checkpoint nghiên cứu. E2E UI và REST chạy ngoài TestClient. JUnit XML (kho nghiên cứu nội bộ) · [Test service/UI](../../tests/test_final_delivery.py) · [Script HTTP](../../scripts/verify_local.py) · [Script trình duyệt](../../scripts/check_ui.cjs).

| # | Tình huống và quan sát | Bằng chứng | Trạng thái |
|---:|---|---|---|
| 1 | URL hợp lệ, không HTML → 200, url_only | HTTP, ảnh 01 | PASS |
| 2 | URL và snapshot → 200, url_html | HTTP, ảnh 02 | PASS |
| 3 | URL sai cú pháp → 422 | HTTP | PASS |
| 4 | URL rỗng → 422 | HTTP | PASS |
| 5 | HTML trắng → 422 | HTTP | PASS |
| 6 | HTML > 8 MiB hoặc body chunked quá mức → 413 | HTTP, pytest | PASS |
| 7 | Thiếu checkpoint → 503 | pytest, fixture missing | PASS |
| 8 | Sai SHA → 503, không chuyển nhánh | pytest, fixture checksum | PASS |
| 9 | Sai feature schema/version → 503 | pytest, fixture schema | PASS |
| 10 | API không khả dụng → UI hiện thông báo | Streamlit AppTest | PASS |
| 11 | JSON lỗi → 422 | HTTP | PASS |
| 12 | Primary dùng 34 biến, threshold 0,20 | HTTP, metadata | PASS |
| 13 | Fallback dùng 17 biến, threshold 0,15 | HTTP, metadata | PASS |
| 14 | Điểm bằng ngưỡng → prediction=1 | pytest, ConstantScore | PASS |
| 15 | /explain trả method và contributions | HTTP | PASS |
| 16 | Snapshot chứa script được xử lý tĩnh | pytest, input HTML có script | PASS |
| 17 | Chế độ demo tắt live fetch, status disabled | HTTP /predict, config và launcher | PASS |
| 18 | Trình duyệt submit qua Streamlit, API nhận POST | Playwright, access log | PASS |
| 19 | Nhãn, điểm, ngưỡng và attribution phù hợp giữa offline/API | verify_local.py, HTTP | PASS |
| 20 | Model/version/threshold khớp registry; registry sai trả lỗi | HTTP, T20 và fixture registry | PASS |

## L. Hạn chế nghiên cứu

Dữ liệu chỉ từ một nguồn, chưa có temporal/external holdout hay đánh giá drift. Việc cô lập nhóm không loại hết near-duplicate hoặc campaign chung. Ba seed và 24 trial/cặp giới hạn khả năng suy rộng. Có 147 cảnh báo nhầm trên Test. Điểm chưa calibration và SHAP phụ thuộc nền. Máy local chứng minh liên kết UI/API và checkpoint. Tải đồng thời, mức độ sẵn sàng của Drive ở nơi khác và triển khai public chưa được nghiệm thu.

## M. Danh mục bàn giao

| Nhóm | Tệp mới hoặc thay đổi trong đợt Final |
|---|---|
| Tài liệu khoa học | [Master MD](../../docs/final/PHISHSHIELD_AI_EXPERIMENT_PROTOCOL_AND_ANALYSIS.md), [Master DOCX](PhishShield-AI-Experiment-Protocol-and-Analysis.docx), [Master PDF](PhishShield-AI-Experiment-Protocol-and-Analysis.pdf), [Report MD](PhishShield-AI-Final-Report.md), [Report DOCX](PhishShield-AI-Final-Report.docx), [Report PDF](PhishShield-AI-Final-Report.pdf) |
| Bảo vệ và hướng dẫn | [82 câu hỏi](../../docs/final/DEFENSE_QA.md), [triển khai](../../docs/final/DEPLOYMENT_GUIDE.md), [API](../../docs/final/API_REFERENCE.md), [người dùng](../../docs/final/USER_GUIDE.md), cập nhật [README](../../README.md) |
| Phân tích và kiểm toán | Tạo scripts/final_audit.py, final_features.py, final_figures.py, final_qc.py và [generate_final_analysis.py](../../scripts/generate_final_analysis.py); sinh [28 bảng](tables/index.csv), [30 hình](figures/index.csv), audit_summary.json, experiment_integrity.csv, artifact_checksums.json và hardware_software.json |
| Ứng dụng | Sửa [FastAPI](../../src/phishshield/api/app.py), [model loader](../../src/phishshield/inference/service.py), [Streamlit](../../src/phishshield/ui/app.py); tạo [launcher](../../scripts/run_local.py) |
| Kiểm thử | Tạo verify_local.py, check_ui.cjs, tests/test_final_delivery.py; lưu HTTP, curl, Swagger, log, JUnit và năm ảnh tại reports/final |
| Hồ sơ nghiệm thu | [Kiểm toán thực nghiệm](FINAL_EXPERIMENT_AUDIT.md) và biên bản này |

Đã xuất PDF A4 từ chính hai tệp Word. Master có 27 trang với 30 hình, 28 bảng trình bày và 19 đối tượng công thức Word. Báo cáo đồ án có sáu trang với bốn hình, ba bảng và tám đối tượng công thức. Đã render từng trang, đối chiếu bảng/hình, kiểm các đích liên kết tệp nội bộ của DOCX. Thư mục CSV giữ số đầy đủ để tránh mất chính xác khi làm tròn trong bản nộp.

## N. Hạng mục còn mở

Không còn blocker cho phạm vi nghiên cứu đã khóa và bản demo local. Chưa kiểm chứng thực nghiệm ngoài corpus, khả năng chịu tải, chạy CUDA trong lần pytest bàn giao, hay tính sẵn có lâu dài của workspace Drive. Những tệp cây tạm từng fold và chứng thực timestamp độc lập không có trong bộ artifact ban đầu. ProtoEnergy-IDS được dùng làm tài liệu tham khảo đọc. Bàn giao ở workspace cục bộ.

## O. Ma trận nghiệm thu cuối

| Điều kiện | Bằng chứng có thể kiểm lại | Trạng thái |
|---|---|---|
| Dataset, feature, split và CV | QC01–QC07, T01–T07 | PASS |
| V1, tuning, 432 fold và V2 | QC08–QC15, 180 dòng inventory | PASS |
| Candidate, selection, phê duyệt, Test | QC16–QC19, T20–T22 | PASS |
| SHAP global/local | QC20, T23, F25–F26 | PASS |
| Giao thức, ablation, thống kê, độ nhạy, phân tích lỗi | Chương 15–26, T13–T25, F11–F28 | PASS |
| Phân tích tái lập và bất biến | Hai lần đối chiếu 1.314 digest, script phân tích hoàn thành | PASS |
| API và inference parity | QC21–QC23, requests, curl, Swagger | PASS |
| Streamlit và E2E | QC24–QC25, năm ảnh và log local | PASS |
| Hướng dẫn tái lập, báo cáo nộp và bộ phản biện | QC26, hai bộ DOCX/PDF, 82 đáp án | PASS |

Phạm vi ký duyệt Test thuộc manifest đã khóa của Project Leader. Biên bản Final này ghi nhận kết quả kiểm tra kỹ thuật để trưởng nhóm sử dụng khi bàn giao.
