# Phương pháp tuning

Đơn vị chọn cấu hình là một cặp thuật toán/modality. Ngân sách của mỗi cặp gồm đúng 24 cấu hình, mỗi cấu hình tạo một dự đoán OOF cho từng mẫu Train. Ba fold được dùng chung cho cả sáu cặp. Pooled F2 là tiêu chí chọn trong tìm kiếm. Điểm Validation chính thức được tính sau khi fit lại trên Train và chọn lại threshold.

| Outer fold | Legitimate | Phishing | Tổng |
|---|---:|---:|---:|
| 0 | 1892 | 1142 | 3034 |
| 1 | 1863 | 1971 | 3834 |
| 2 | 1948 | 1913 | 3861 |

Nhóm domain/hash có kích thước khác nhau. StratifiedGroupKFold giữ nguyên nhóm nên tỷ lệ phishing của fold 0 thấp hơn hai fold kia. Mỗi quan sát có cùng trọng số trong phép gộp OOF. MLP chia nhóm lần thứ hai bên trong phần fit, chọn best epoch theo inner loss và dùng checkpoint đó trên outer fold. Số lần refit bổ sung bằng 0.

CV SHA-256 `fd766213fca49c34bc2c3f6dd8b4edb69d3d28f378cac0f01633ae4fa8ec94cd`. Search seed 2026, CV seed 2026, training seed 42. Trial ID cố định trước khi chạy. Bảng sweep sử dụng riêng những trial chỉ đổi số cây/width. Các điểm random search khác có thể thay nhiều chiều đồng thời. Chi phí theo từng fold có trong fold_metrics.json. Kết quả thực nghiệm chính thức: PENDING.

[Quy tắc chọn, ngân sách và tiêu chí đo](../../docs/EXPERIMENT_PROTOCOL.md) · [Bảng tham số và bằng chứng từng cặp](hyperparameter_comparison.md)
