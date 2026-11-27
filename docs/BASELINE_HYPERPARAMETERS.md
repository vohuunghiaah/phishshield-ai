# Baseline V1 · Đặc tả và nguồn bằng chứng

Cấu hình khởi đầu được cố định trước khi huấn luyện V1. Hồ sơ hiện có không ghi một search hoặc tài liệu nghiên cứu dùng để chọn riêng 200 cây, 250 vòng hay 64 hidden units. Các giá trị này là đối chứng. Mỗi slot có config, run manifest, checksum và checkpoint riêng.

## Random Forest · scikit-learn 1.6.1

| Tham số | Giá trị checkpoint | Nguồn / loại | Vai trò |
|---|---|---|---|
| bootstrap | True | Implicit / mặc định estimator | Lấy mẫu hoàn lại cho mỗi cây |
| ccp_alpha | 0.0 | Implicit / mặc định estimator | Mức phạt khi tỉa cây |
| class_weight | balanced | Explicit | Trọng số lớp theo tần suất |
| criterion | gini | Implicit / mặc định estimator | Hàm tính độ thuần để chọn split |
| max_depth | None | Implicit / mặc định estimator | Giới hạn độ sâu cây |
| max_features | sqrt | Implicit / mặc định estimator | Số feature thử tại mỗi split |
| max_leaf_nodes | None | Implicit / mặc định estimator | Số lá tối đa |
| max_samples | None | Implicit / mặc định estimator | Kích thước mẫu bootstrap |
| min_impurity_decrease | 0.0 | Implicit / mặc định estimator | Mức giảm impurity để chấp nhận split |
| min_samples_leaf | 2 | Explicit | Số hàng tối thiểu ở lá |
| min_samples_split | 2 | Implicit / mặc định estimator | Số hàng tối thiểu để chia nút |
| min_weight_fraction_leaf | 0.0 | Implicit / mặc định estimator | Tỷ lệ tổng trọng số tối thiểu ở lá |
| monotonic_cst | None | Implicit / mặc định estimator | Ràng buộc đơn điệu |
| n_estimators | 200 | Explicit | Số cây RF / số vòng boosting |
| n_jobs | -1 | Cấu hình thực thi trực tiếp | Số worker/luồng tính toán |
| oob_score | False | Implicit / mặc định estimator | Tính điểm out-of-bag |
| random_state | 42 / 43 / 44 | Training seed truyền trực tiếp | Seed của fit |
| verbose | 0 | Implicit / mặc định estimator | Mức ghi log |
| warm_start | False | Implicit / mặc định estimator | Tái sử dụng cây khi fit lần sau |

## XGBoost · 3.0.2

get_params(deep=True) ghi giá trị wrapper. Cột native lấy từ get_booster().save_config() của checkpoint đã load. Dấu — chỉ trường không có đối chiếu trực tiếp. Native config đầy đủ cho từng seed nằm trong JSON bằng chứng.

| Tham số | Wrapper | Native (seed 42, URL-only) | Nguồn / loại | Vai trò |
|---|---|---|---|---|
| objective | binary:logistic | binary:logistic | Implicit / mặc định estimator | Hàm mục tiêu và ánh xạ xác suất |
| base_score | None | 4.6845E-1 | Implicit / mặc định estimator | Điểm khởi tạo |
| booster | None | gbtree | Implicit / mặc định estimator | Họ mô hình boosting |
| callbacks | None | — | Implicit / mặc định estimator | Callback trong fit |
| colsample_bylevel | None | 1 | Implicit / mặc định estimator | Tỷ lệ cột mỗi tầng |
| colsample_bynode | None | 1 | Implicit / mặc định estimator | Tỷ lệ cột mỗi nút |
| colsample_bytree | None | 1 | Implicit / mặc định estimator | Tỷ lệ cột mỗi cây |
| device | cpu | cpu | Cấu hình thực thi trực tiếp | Thiết bị |
| early_stopping_rounds | None | — | Implicit / mặc định estimator | Số vòng chờ trước dừng sớm |
| enable_categorical | False | — | Implicit / mặc định estimator | Xử lý biến categorical |
| eval_metric | logloss | — | Explicit | Metric theo dõi |
| feature_types | None | — | Implicit / mặc định estimator | Kiểu cột |
| feature_weights | None | — | Implicit / mặc định estimator | Trọng số khi chọn cột |
| gamma | None | 0 | Implicit / mặc định estimator | Mức giảm loss tối thiểu để chia nút |
| grow_policy | None | depthwise | Implicit / mặc định estimator | Thứ tự mở rộng nút |
| importance_type | None | — | Implicit / mặc định estimator | Cách tổng hợp importance |
| interaction_constraints | None |  | Implicit / mặc định estimator | Giới hạn tương tác giữa cột |
| learning_rate | 0.06 | 0.0599999987 | Explicit | Hệ số co mỗi bước cập nhật |
| max_bin | None | 256 | Implicit / mặc định estimator | Số bin histogram |
| max_cat_threshold | None | 64 | Implicit / mặc định estimator | Giới hạn category khi xét split |
| max_cat_to_onehot | None | 4 | Implicit / mặc định estimator | Ngưỡng dùng split one-hot |
| max_delta_step | None | 0 | Implicit / mặc định estimator | Giới hạn bước cập nhật ở lá |
| max_depth | 5 | 5 | Explicit | Giới hạn độ sâu cây |
| max_leaves | None | 0 | Implicit / mặc định estimator | Số lá tối đa |
| min_child_weight | None | 1 | Implicit / mặc định estimator | Tổng Hessian tối thiểu ở nút con |
| missing | NaN | — | Implicit / mặc định estimator | Quy ước giá trị thiếu |
| monotone_constraints | None | () | Implicit / mặc định estimator | Ràng buộc đơn điệu |
| multi_strategy | None | one_output_per_tree | Implicit / mặc định estimator | Chiến lược nhiều đầu ra |
| n_estimators | 250 | — | Explicit | Số cây RF / số vòng boosting |
| n_jobs | 2 | 2 | Cấu hình thực thi trực tiếp | Số worker/luồng tính toán |
| num_parallel_tree | None | 1 | Implicit / mặc định estimator | Số cây song song mỗi vòng |
| random_state | 42 / 43 / 44 | 42 | Training seed truyền trực tiếp | Seed của fit |
| reg_alpha | None | 0 | Implicit / mặc định estimator | Hệ số L1 của trọng số lá |
| reg_lambda | None | 1 | Implicit / mặc định estimator | Hệ số L2 của trọng số lá |
| sampling_method | None | uniform | Implicit / mặc định estimator | Cách lấy mẫu hàng |
| scale_pos_weight | None | 1 | Implicit / mặc định estimator | Trọng số lớp dương |
| subsample | None | 1 | Implicit / mặc định estimator | Tỷ lệ hàng mỗi vòng |
| tree_method | hist | hist | Explicit | Phương pháp dựng cây |
| validate_parameters | None | 1 | Implicit / mặc định estimator | Kiểm tra cấu hình |
| verbosity | None | — | Implicit / mặc định estimator | Mức ghi log |

Mỗi booster có 250 cây. Full row/column sampling, histogram CPU và cơ chế chia cây cho kết quả trùng nhau theo seed trong từng modality. Audit so sánh cả estimator seed, đường dẫn, attempt, tree dump và xác suất. Early stopping rounds=None, fit không truyền eval_set.

## MLP · PyTorch 2.8.0+cu128

| Thành phần | Baseline V1 | Vai trò và nguồn |
|---|---|---|
| Input → hidden → output | 17 hoặc 34 → 64 → 1 | Hai Linear, đúng một hidden layer. Width điều khiển năng lực biểu diễn. Shape trong checkpoint |
| Activation / output | ReLU / một logit | BCEWithLogitsLoss khi fit. Sigmoid của logit khi inference |
| Optimizer / learning rate | Adam / 0.001 | Learning rate explicit, điều khiển độ lớn cập nhật |
| Mặc định Adam 2.8.0 | betas=(0.9,0.999), eps=1e-8, weight_decay=0, amsgrad=False | Moment bậc 1/2, ổn định mẫu số, regularization. maximize/capturable/differentiable/decoupled_weight_decay=False, foreach/fused=None |
| Dropout / scheduler | 0 / không dùng | V1 không có lớp dropout hoặc lịch đổi LR |
| Khởi tạo | Mặc định nn.Linear.reset_parameters | Kaiming uniform với a=√5 cho weight, bias uniform trong ±1/√fan_in |
| Batch / epochs / patience | 128 / 80 / 8 | Số hàng mỗi update, trần epoch, số epoch liên tiếp không giảm loss trước khi dừng |
| Best checkpoint | Lần giảm Validation BCE loss nghiêm ngặt | Lưu scaler và bốn tensor weight/bias. Loss bằng best không đặt lại bộ đếm |
| Scaler | StandardScaler, fit trên Train | Trung bình và scale từng cột trước khi vào mạng. Áp cùng scaler cho Validation |
| Seed | 42, 43, 44 | Python random, NumPy, CPU generator, all CUDA generators, DataLoader shuffle với generator có seed |
| Determinism | torch.use_deterministic_algorithms(True) | Mã đặt CUBLAS_WORKSPACE_CONFIG=:4096:8 nếu chưa có. Manifest lịch sử không ghi giá trị biến môi trường thực tế |
| Hardware | Tesla T4, torch CUDA 12.8 | Hardware check READY, tham số mạng cuda:0 ghi trong manifest. FrozenMLP dự đoán bằng NumPy và SciPy |

| Modality | Best epoch seed 42 / 43 / 44 | Epoch thực chạy |
|---|---|---|
| url_only | 30 / 20 / 42 | 38 / 28 / 50 |
| url_html | 30 / 21 / 34 | 38 / 29 / 42 |

## Threshold và thiết bị

Decision threshold được chọn sau fit từ 19 giá trị trên Validation. Seed, thiết bị và số luồng là cấu hình huấn luyện/thực thi. Ma trận, F2, threshold, best epoch, software và phần cứng có thể truy ngược từng run. RF và XGBoost dùng CPU. Giá trị native và cấu hình đầy đủ được lấy từ checkpoint của từng seed. [Audit 18 run](../reports/experiments/baseline_v1_audit.md) · Bằng chứng estimator, booster và MLP (kho nghiên cứu nội bộ)
