# Hướng dẫn chạy Gate 2.2 và Gate 2.3

Mở notebook bằng tài khoản Editor của nhóm. Chạy 00 để xác minh Drive. Dữ liệu đã khóa và qua checksum cho phép đi thẳng tới notebook được giao. Nếu checksum sai, dừng và đối chiếu bản nguồn với điều phối viên.

| Thành viên | Bước thiết lập | Tuning | Training | Runtime |
|---|---|---|---|---|
| 1 | [00](https://colab.research.google.com/drive/1h0PGkqQVWF0w3UmLed8LUEqqeXMyS8OL) | [07a RF](https://colab.research.google.com/drive/1uIuMD2qkIbzveoTrlxrCs4aAlgNUXzOL) | [07 RF](https://colab.research.google.com/drive/1xKBEk-_et2GcvmvgFLYFrOy5CI8-P8Pj) | CPU |
| 2 | 00 | [08a XGBoost](https://colab.research.google.com/drive/1-V2CrEjtxJpN0dVv5TSfuRVUoaeTQNIP) | [08 XGBoost](https://colab.research.google.com/drive/14smkiShPFBA-Ly34zNN_PB63E0gBbNl2) | CPU |
| 3 | 00 | [09a MLP](https://colab.research.google.com/drive/1M2ML6XE18uBRyT_l7VWf_buZmBTCNPbx) | [09 MLP](https://colab.research.google.com/drive/1XkZ5xtpOwz0uK6TtHfDxrMc6uoF91cuA) | GPU T4 hoặc CUDA tương thích |

1. Ô mount cho phép sửa `candidate` nếu shortcut ở vị trí khác. Giữ model/phase/device tương ứng. `MODALITIES` mặc định chạy cả hai. Có thể giới hạn một modality để chia phiên. Mỗi cặp model/modality chỉ giao một người ghi tại một thời điểm.
2. Chạy các ô xác minh folder, bootstrap và Hardware Check. RF và XGBoost gọi CPU probe. MLP cần chọn GPU trong Runtime của Colab. Bootstrap đồng bộ source trước khi tạo `.venv-cuda-mlp` bằng Python 3.11 và cài torch 2.8.0+cu128. Hardware Check phải báo READY bằng đúng interpreter, GPU khả dụng và phép nhân tensor thành công.
3. Khi nhóm cho phép chạy chính thức, bật `START_TUNING=True` ở ô cuối của 07a/08a/09a. Trial COMPLETED chỉ dùng lại sau khi kiểm tra identity, software và checksum. Khi Colab mất kết nối, xác nhận VM cũ đã dừng. Trong đúng thư mục model/modality, đổi tên `.active` còn sót sang `.interrupted-<thời điểm>`, rồi mở lại cùng notebook. Trial dở chạy lại từ đầu. Backend giữ bản ghi attempt bị gián đoạn. Khi hash sai, đối chiếu bản lưu và báo điều phối viên.
4. Khi có tuning_lock cho từng modality, mở 07/08/09. Giữ `EXPERIMENT_PHASE="TUNED_V2"`, cấu hình `TRAIN_SEEDS=[42,43,44]`, bật `START_TRAINING=True` ở ô cuối. Backend tự đọc hyperparameters đã khóa. Nếu ngắt giữa seed, khôi phục .active trong đúng thư mục seed. Checkpoint từng attempt nằm riêng dưới checkpoints/tuned_v2.
5. Ngay khi đủ sáu tuning lock, chạy notebook 10 ở chế độ report để xuất sáu bảng Selected V2 và cập nhật phụ lục giao thức. Sau Gate 2.3, chạy lại [10](https://colab.research.google.com/drive/1Jmm8duvPzEwtiCrKfNjXfRzX0M-cGqMT) để làm mới registry và các bảng. Giữ hai cờ False khi lập báo cáo. Sau đủ 18 run, điều phối viên bật riêng START_MODEL_SELECTION để khóa primary và fallback. Rà soát cả các delta âm và các biểu đồ theo modality.
6. Chỉ sau nghiệm thu, Project Leader tự tạo `manifests/project_leader_approval.json` với các trường `decision="APPROVED"`, `reviewer` là họ tên, `validation_comparison_reviewed=true` và `selection_sha256` là SHA-256 thực tế của model_selection_v2.json. Thay đổi nguồn selection làm mất hiệu lực phê duyệt. Khi được phép mở Test, bật riêng START_TEST_EVALUATION. Sau đó chạy [11](https://colab.research.google.com/drive/1_ImLj-AGLP1n3AGK2esyq_GepX59FJlq) và [12](https://colab.research.google.com/drive/1FpB-nkXwyq7kIMI2iJXeMuZYMv7msriy).

## Registry và tiêu chí nghiệm thu

| Gate | Điều kiện | Bằng chứng |
|---|---|---|
| V1 | 18 danh tính duy nhất, hash hợp lệ, tái tạo Validation | manifests/baseline_v1.json, results/baseline_v1, baseline_v1_audit.md |
| Sẵn sàng tuning | Checksum dữ liệu, CV khóa, ngân sách chung đã khóa, test và smoke | manifests/cv_lock.json, manifests/tuning_design_v2.json, reports/setup/gate2_2_readiness_report.md |
| 2.2 | 24 trial hợp lệ mỗi cặp, 3 fold mỗi trial, đủ OOF và 6 lock | results/tuning_v2/<model>/<modality>, hyperparameter_comparison.md |
| 2.3 | 18 bản ghi có checkpoint, threshold Validation và provenance đúng | manifests/tuned_v2.json, results/tuned_v2, checkpoints/tuned_v2 |
| Cho phép chấm Test | Selection đã khóa, mọi checksum còn đúng, Project Leader đã duyệt đúng manifest | manifests/model_selection_v2.json và project_leader_approval.json |

Trạng thái trial lần lượt có thể là PENDING, RUNNING, COMPLETED, FAILED hoặc INTERRUPTED. Mỗi model/modality có tuning_summary.csv, tuning_summary.md, sensitivity.csv, biểu đồ, best_hyperparameters.json và tuning_lock.json sau khi hoàn tất. fold_metrics.json dùng threshold pooled, fold checkpoint MLP lưu cả scaler và kiến trúc. training_seconds ở CV gồm fit và ghi checkpoint trong runtime. model_bytes là trung bình ba checkpoint nén. Phương pháp dự đoán MLP đóng băng dùng NumPy trên CPU. Hardware ghi thiết bị huấn luyện riêng.

## Thuật ngữ

Model parameter là trọng số, bias hoặc split cây học từ dữ liệu. Hyperparameter là lựa chọn trước fit, ví dụ depth hay learning rate. Training seed điều khiển bộ sinh số ngẫu nhiên. Decision threshold chuyển xác suất thành nhãn. Early stopping chọn epoch theo loss trên tập dừng. Cross-validation luân phiên nhóm Train để sinh OOF. Baseline là đối chứng cố định V1. Tuned model dùng cấu hình thắng trong ngân sách định trước. Best configuration thuộc model/modality, còn best checkpoint là artifact của một lần fit/seed cụ thể.


## Kiểm tra lại bằng CLI

Trong môi trường dự án, điều phối viên có thể chạy `python scripts/gate2.py audit --root .` để kiểm checksum raw/cache và replay Validation, `python scripts/gate2.py prepare --root .` để xác minh CV và thiết kế đã khóa, hoặc `python scripts/gate2.py report --root .` để cập nhật bảng. Các lệnh này không huấn luyện chính thức. Baseline audit cần extra trees để load XGBoost. Bộ regression đầy đủ dùng extras test, trees, mlp, tuning, demo và explain trong môi trường riêng. Để kiểm thử GPU thật, cài bản torch CUDA tương thích và đặt PHISHSHIELD_GPU_SMOKE=1 trước khi chạy pytest. Thiết kế khóa cả mã ảnh hưởng đến candidate/fit/metric, do đó thay đổi sau khi mở Gate cần phiên bản giao thức mới.
