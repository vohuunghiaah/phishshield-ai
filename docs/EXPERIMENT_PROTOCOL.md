# Giao thức thực nghiệm PhishShield AI

| Phiên bản | Thời điểm quyết định | Phạm vi |
|---|---|---|
| Protocol V1 — Fixed Hyperparameter Baseline | Trước 18 run baseline | Cấu hình cố định, hai modality, ba seed. [Bản gốc](EXPERIMENT_PROTOCOL_V1.md) |
| Protocol V2 — Hyperparameter Tuning and Tuned Evaluation | Sau khi nhóm xem Baseline Validation, trước đánh giá Test | Khóa thiết kế tìm kiếm, đánh giá OOF trong Train, huấn luyện lại và so sánh Validation theo seed |

## Dữ liệu và đối chứng

CompPhish v4 (CC BY 4.0), 15.358 mẫu gốc, cohort 15.327. Split seed 2026, Train/Validation/Test lần lượt 10.729/2.299/2.299. SHA-256 membership `d3ecbd33e6597b3c75f036c8c58a86f84addf4790743b467666d83d903cdd3e5`. Schema 1.0.0, 17 hoặc 34 cột theo manifest. Giữ nguyên extraction, nhãn, cohort và thứ tự cột. Nhóm là thành phần liên thông của registrable domain và SHA-256 HTML. PID, URL, domain, group và hash chỉ dùng quản lý mẫu.

BASELINE_V1 gồm đủ 18 run có sẵn. Manifest, checkpoint, config và metrics giữ tại đường dẫn lịch sử. Thông số do mã khai báo, mặc định estimator, booster thực tế, seed, thiết bị và threshold được ghi riêng. Các con số ban đầu là cấu hình cố định của V1. [Đặc tả và bằng chứng baseline](BASELINE_HYPERPARAMETERS.md)

## Gate 2.2 · TUNING_V2

Dùng StratifiedGroupKFold 3 fold trên Train sắp theo serial_number, shuffle với CV seed 2026. Cả sáu cặp dùng cùng membership. Khóa SHA-256 trong manifests/cv_lock.json. Kiểm tra hai lớp trong mỗi tập, coverage và tính nguyên vẹn của group, URL, domain, HTML hash. Nếu không đạt thì dừng. Ghi phân bố lớp thực tế của từng fold. Pooled OOF tính mỗi mẫu một lần, phù hợp khi kích thước fold khác nhau.

Mỗi thuật toán có 24 candidate dùng chung cho hai modality. Mở đầu bằng sweep một chiều của số cây hoặc hidden width và chứa đúng một baseline. Phần còn lại lấy ngẫu nhiên đồng đều từng chiều với search seed 2026, bỏ tổ hợp trùng. Mỗi fit dùng training seed 42. Không gian hữu hạn, thứ tự candidate, ngân sách và tiêu chí hòa được khóa trước lần chạy đầu. [Không gian RF](../configs/tuning/random_forest.yaml) · [XGBoost](../configs/tuning/xgboost.yaml) · [MLP](../configs/tuning/mlp.yaml) · [Ngân sách và seeds](../configs/tuning/experiment.yaml)

| Thuật toán | Thiết bị | Sweep cố định các chiều khác ở baseline | Trials × modality × folds |
|---|---|---|---|
| Random Forest | CPU | 50, 100, 200, 300, 500 cây | 24 × 2 × 3 |
| XGBoost | CPU hist | 100, 200, 250, 300, 500 vòng | 24 × 2 × 3 |
| MLP | CUDA, ưu tiên T4 | 32, 64, 128, 256 nơ-ron trong một hidden layer | 24 × 2 × 3 |

Tổng 144 trial, 432 lần đánh giá outer fold. RF/XGBoost fit trực tiếp toàn bộ CV-Train. XGBoost dùng số vòng đã định. MLP chia CV-Train bằng 3-fold StratifiedGroupKFold với seed 2026, dùng inner fold 0 để dừng và hai fold còn lại để fit scaler và cập nhật trọng số. BCE loss trên inner fold chọn checkpoint, patience 8. Checkpoint đó dự đoán outer fold đúng một lần. Thiết kế dùng một fit mỗi outer fold, 0 refit. Báo cáo loss hai tập, best epoch, số epoch thực chạy và kích thước tập nội bộ. Loss train tiếp tục giảm trong khi inner loss tăng sau best epoch là dấu hiệu overfitting. Hai đường loss còn cao và ít cải thiện là dấu hiệu cần đối chiếu thêm với OOF, chưa đủ để kết luận underfitting. Inference dùng scaler và trọng số đóng băng.

Tìm threshold trên toàn bộ xác suất OOF bằng grid 0,05–0,95 bước 0,05. Cùng một quy tắc chọn ngưỡng cho OOF và Validation: F2 phishing cao hơn, precision cao hơn, FPR thấp hơn, threshold cao hơn. F2 = 5 × precision × recall / (4 × precision + recall). False negative bỏ lọt website phishing, do đó ưu tiên recall và báo cáo cả FPR. Metric trên OOF là tiêu chí tìm kiếm trong Train.

Xếp candidate bằng giá trị đầy đủ theo F2 giảm dần, precision giảm dần, FPR tăng dần, ưu tiên baseline, cuối cùng candidate ID nhỏ hơn. Chỉ kết luận “Best configuration found within the predefined search space and search budget.” Ghi cả accuracy, F1, macro-F1, recall, ROC-AUC, PR-AUC hình thang, average precision và confusion matrix thứ tự [0,1]. Chi phí thực tính riêng theo model, thiết bị và phiên. Phân tích sensitivity một chiều dùng các trial sweep đã định trước. Scatter từ random search đa chiều chỉ mô tả liên hệ.

## Gate 2.3 · TUNED_V2

Mỗi cặp model/modality lấy cấu hình duy nhất từ tuning_lock đã xác minh toàn bộ trial và checksum. Ba seed 42/43/44 dùng cùng cấu hình. Fit trên Train chính thức. RF/XGBoost dùng CPU. MLP dùng CUDA, scaler fit trên Train, checkpoint có loss Validation thấp nhất. Validation chính thức vừa dùng dừng MLP, vừa chọn threshold và so sánh mô hình. Cả ba mô hình đều chọn lại threshold trên Validation. OOF threshold chỉ có giá trị trong tìm kiếm.

Báo cáo riêng sáu bảng Baseline/Selected, kể cả tham số giữ nguyên. Mỗi bảng chỉ rõ candidate, CV hash, trial và chênh lệch OOF. Sau huấn luyện ghép đúng model, modality và seed để tính mean, sample SD (ddof=1), min, max, delta từng seed, mean paired delta và điểm phần trăm. Chênh lệch tương đối chia cho giá trị baseline khi khác 0. Baseline ablation giữ nguyên hyperparameters khi thêm HTML. Hai tuned modality có thể chọn cấu hình khác nhau. Không suy ra ý nghĩa thống kê từ ba seed. [Sáu bảng tham số](../reports/experiments/hyperparameter_comparison.md) · [So sánh Validation](../reports/experiments/baseline_vs_tuned_report.md)

## Chọn mô hình, duyệt và đánh giá Test

Notebook 10 mặc định chỉ tạo báo cáo. Cờ chọn mô hình yêu cầu 18 run TUNED_V2 đã xác minh và sáu tuning lock. Xếp sáu cặp bằng mean F2, mean precision, lower mean FPR, tên thuật toán rồi modality. Trong cặp thắng, chọn seed theo F2, precision, lower FPR rồi seed nhỏ hơn. Cùng quy tắc cho URL-only fallback. Khóa checkpoint, threshold, schema, split và đường dẫn/hash từng nguồn trong model_selection_v2.json. Protocol dùng Tuned V2 kể cả khi baseline tốt hơn. Project Leader xem mọi cặp suy giảm trước khi ký duyệt.

Test chỉ chấm primary đã khóa sau khi bật cờ độc lập và có phê duyệt của Project Leader ràng buộc với SHA-256 của selection. SHAP bước 11 dùng tối đa 32 mẫu Train làm nền và 24 Validation làm ví dụ. Bước 12 kiểm tra API và UI. [Thao tác và điều kiện nghiệm thu](HYPERPARAMETER_TUNING_GUIDE.md)

<!-- selected-hyperparameters-v2 -->
## Cấu hình đã khóa theo kết quả OOF

| Model | Modality | Selected trial | Selected hyperparameters |
|---|---|---|---|
| random_forest | url_only | C022 | {'n_estimators': 300, 'min_samples_leaf': 4, 'n_jobs': -1, 'class_weight': None, 'max_depth': 10, 'max_features': 'log2', 'min_samples_split': 5} |
| random_forest | url_html | C019 | {'n_estimators': 300, 'min_samples_leaf': 2, 'n_jobs': -1, 'class_weight': None, 'max_depth': None, 'max_features': 'log2', 'min_samples_split': 5} |
| xgboost | url_only | C006 | {'n_estimators': 100, 'learning_rate': 0.06, 'max_depth': 3, 'tree_method': 'hist', 'eval_metric': 'logloss', 'n_jobs': 2, 'min_child_weight': 1, 'subsample': 1.0, 'colsample_bytree': 1.0, 'gamma': 0.5, 'reg_alpha': 0.1, 'reg_lambda': 10} |
| xgboost | url_html | C004 | {'n_estimators': 300, 'learning_rate': 0.06, 'max_depth': 5, 'tree_method': 'hist', 'eval_metric': 'logloss', 'n_jobs': 2, 'min_child_weight': 1, 'subsample': 1.0, 'colsample_bytree': 1.0, 'gamma': 0, 'reg_alpha': 0, 'reg_lambda': 1} |
| mlp | url_only | C021 | {'hidden': 256, 'batch_size': 64, 'epochs': 150, 'patience': 8, 'learning_rate': 0.0005, 'weight_decay': 0.001, 'dropout': 0.1} |
| mlp | url_html | C021 | {'hidden': 256, 'batch_size': 64, 'epochs': 150, 'patience': 8, 'learning_rate': 0.0005, 'weight_decay': 0.001, 'dropout': 0.1} |
