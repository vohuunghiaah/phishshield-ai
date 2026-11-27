*Bản công khai tóm lược bằng chứng Gate 6. Các log, danh mục theo mẫu và tệp gốc do trưởng nhóm lưu nội bộ.*

# Kiểm toán thực nghiệm PhishShield AI

**Ngày lập 28/11/2026 · CompPhish v4 · schema 1.0.0 · Project Leader Võ Hữu Nghĩa (Vohuunghia).**

## Kết quả đối soát

Có đủ 18 run BASELINE_V1, 144 trial TUNING_V2 qua 432 lượt đánh giá fold và 18 run TUNED_V2. Inventory có 180 dòng cho 36 run và 144 trial. Sáu tuning lock có đủ 24 candidate mỗi cặp. Dự đoán ngoài fold của mỗi candidate phủ đúng 10.729 ID thuộc Train. 432 lượt fit ngoài và 36 final fit tạo 468 lần fit theo thiết kế, chưa tính lần thăm dò phần cứng hoặc retry trong lịch sử. Quá trình lập hồ sơ Final chỉ đọc, trích đặc trưng, suy luận và tính thống kê từ artifact. Biên bản máy đọc (kho nghiên cứu nội bộ) · Inventory theo run/trial (kho nghiên cứu nội bộ) · Danh mục 1.314 SHA-256 (kho nghiên cứu nội bộ).

| Đối tượng | Quy tắc kiểm tra | Kết quả |
|---|---|---|
| Tám tệp nguồn | Tính SHA và đối chiếu manifest dataset | Đủ tám tệp. 15.358 dòng ban đầu |
| Cohort | Hash, ID, metadata, feature manifest, quy tắc loại | 15.327 dòng. 23 URL lỗi và tám snapshot rỗng |
| Split | SHA chỉ mục, ID và lớp, connected components | Train 10.729, Validation 2.299, Test 2.299 |
| Giao tập | Cùng URL, registrable domain, SHA HTML hoặc group chỉ ở một split | Không thấy giao theo các khóa trên |
| Train-CV | Mỗi ID đúng một fold, group nguyên vẹn | 3.034, 3.834 và 3.861 dòng |
| V1/V2 chính thức | Registry, attempt, seed, config, metric, phần cứng, checkpoint | 36 checkpoint tải được, tái hiện Validation trong dung sai |
| Candidate | Identity, config, seed, CV hash, số fold, OOF và SHA các artifact lưu | Đủ 6 × 24, thuộc đúng khóa |
| Metric OOF và fold | Tính lại từ probability/label gốc, đúng ngưỡng gộp | 144 pooled, 432 fold; log loss pooled khớp |
| Preprocessing MLP | So n, mean và variance trong scaler với hàng fit được phép | Kiểm tra trên final checkpoint và các checkpoint inner-fit của CV |
| Chọn ngưỡng và model | So lại lưới ngưỡng từng run/trial, xếp lại candidate và cặp/seed | Trùng selection và threshold đã duyệt |
| Test | So ID, nhãn, giới hạn tập, prediction theo ngưỡng, toàn bộ metric | Đúng 2.299 hàng của primary |
| Giải thích | So nền Train, mẫu Validation, thứ tự 34 biến, score, thứ hạng | 24 mẫu cộng đúng trong sai số số học |

Đối với registry/hashes đã có digest tham chiếu, từng digest được đối chiếu chính xác. Những tệp cũ thiếu receipt riêng được ghi digest ở lần bàn giao, rồi đối soát với dữ liệu liên quan. Tệp tổng hợp artifact_checksums.json (kho nghiên cứu nội bộ) có SHA-256 **207a69447349d878ebefc9ce92df6516153c0b4fdf6efc316bdc89805aab0c3f** trong lần đối chiếu. Mốc này cho phép phát hiện thay đổi về sau.

## Chuỗi bằng chứng

| Thành phần | SHA-256 |
|---|---|
| Cohort | ef1e5b04d40da1dfe6e37d71481ad40810fa2753b3e9fd78688bf4b5d99a0deb |
| Chỉ mục Train/Validation/Test | d3ecbd33e6597b3c75f036c8c58a86f84addf4790743b467666d83d903cdd3e5 |
| Chỉ mục CV | fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd |
| Feature manifest | 95dc1cf7c5e636d8ac975a6b9d530b837e666bc7a73f1ce8d3df85e1c8d8c80a |
| Model selection | a0d5100ce5866e8281699795d27adf13caddb219b41aa94e65fb25eaa4bff606 |
| Phê duyệt leader | a3724cd78cc0e0b97dfa3843257f7dfb8e56aec0f0d2b4f5ffaec840f4cd6c97 |
| Checkpoint primary | 0a78a47a3a46579cabed3da4d68ed926573fd87df3df45afc9d59e24468ef948 |
| Checkpoint fallback | 0ce231574e7d61d7fdedb65b85f00c7cc1ecdd5e02859cb48bb4ea955f9a2897 |
| Locked Test metrics | 588c9452afa9e656d7e2d60a25c8e46c5efd043f419cd2e5ee935165c1a44cdd |
| Locked Test predictions | e116ba396594af5fc10804c76fed05c773a24a6b639ff0fc68f1f0160c105b0c |

Ngày 27/11/2026 UTC, mtime lần lượt là 17:11:26 cho selection, 17:27:48 cho approval và 17:32:43 cho Test. Approval ghi APPROVED, validation_comparison_reviewed=true và đúng digest selection. Mốc hệ thống tệp hỗ trợ xác minh thứ tự nội bộ. Chưa có chứng thực thời gian của một bên thứ ba.

## Checkpoint và phần cứng

RF primary là C019, seed 43, 34 biến, 300 cây và threshold 0,20. RF fallback là C022, seed 44, 17 biến, 300 cây và threshold 0,15. Hai artifact phục vụ giống bytes với nguồn checkpoint được chọn. Audit dùng bộ cột của từng bundle và replay Validation. Tolerance tuyệt đối tối đa là 10⁻⁵ cho metric replay đa nền tảng. Metric tính từ tệp prediction dùng tolerance 10⁻⁹, kiểm nhãn và SHA là so sánh chính xác. Với mỗi tổ hợp XGBoost pha/modality, ba seed có ba attempt riêng, một hash tree dump và một hash vector xác suất Validation. Nguồn cho phép kiểm cụ thể các cột trees_sha256 và val_probability_sha256. Inventory (kho nghiên cứu nội bộ) · [Hai đường dẫn checkpoint gốc và bản triển khai](tables/T20_selection.csv).

24 run cây chạy CPU, 12 run MLP dùng Tesla T4, PyTorch 2.8.0+cu128. T07 lưu record phần cứng và phiên bản phần mềm của từng run. Checkpoint fold RF/XGB là tệp tạm của pipeline CV. Khi không còn tệp cây theo fold, audit kiểm tra OOF, metric, config, identity và SHA tương ứng. Tất cả 144 checkpoint fold MLP được giữ cho 48 candidate MLP. [Cấu hình theo run](tables/T07_hardware.csv).

## Kết quả Test và SHAP

Từ 1.075 TN, 147 FP, 17 FN và 1.060 TP, F2 đạt 96,102%, Recall 98,422%, Precision 87,821% và FPR 12,029%. Trên 2.299 ID, toàn bộ nhãn dự đoán đúng theo phép so điểm với 0,20. Hồ sơ Test chỉ thuộc primary. [Tất cả chỉ số](tables/T21_test_metrics.csv) · [Các mẫu theo khoảng cách tới ngưỡng](tables/T24_error_cases.csv).

Với 32 mẫu nền Train và 24 mẫu giải thích Validation theo seed 42, điểm nền tái tạo từ checkpoint là 0,29055982. ID ẩn danh có điểm 0,85494940. Sai lệch cộng tính tối đa khoảng 1,78 × 10⁻¹⁵ trong lần đối chiếu đầu. Đối chiếu 34 mean absolute SHAP với contributions.csv tái lập bảng global. Phân tích này sử dụng các SHAP artifact sẵn có. Không có receipt riêng xác thực phiên bản môi trường SHAP của phiên chạy gốc. [Bảng thứ hạng](tables/T23_shap.csv).

## Phạm vi của kết luận

Các bằng chứng nhận diện đúng kết quả trên workspace đang truy cập. Không có kiểm chứng độc lập rằng mọi tài khoản Drive đều lấy được cohort trong tương lai. Phụ thuộc giữa các chiến dịch gần giống, phân bố theo thời gian, calibration và khả năng chuyển sang corpus khác chưa được đo. Phần kiểm toán và tái lập bảng/hình có entry point riêng. [Script phân tích](../../scripts/generate_final_analysis.py) · [Hướng dẫn tái lập](../../docs/final/DEPLOYMENT_GUIDE.md).
