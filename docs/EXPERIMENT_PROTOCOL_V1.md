# Giao thức thí nghiệm

CompPhish v4 có hai nguồn đầu vào là URL và snapshot. Cả hai cấu hình lấy đúng các serial_number trong cohort đã kiểm định. Mô hình chỉ nhận các cột theo thứ tự từ feature schema phiên bản 1.0.0. Mọi bước phân tích liên quan lựa chọn đặc trưng sử dụng train. Dữ liệu thiếu URL hợp lệ hoặc snapshot hợp lệ được loại có ghi lý do. Các đặc trưng sinh ra đều xác định được trên cohort này.

Điều phối viên khóa split trước EDA. Mỗi thành phần liên thông của domain đăng ký và SHA-256 snapshot được gán nguyên vẹn vào một tập. Dùng Public Suffix List đóng gói có private suffixes. Seed 2026 trộn các nhóm đồng kích thước. Gán nhóm lớn trước để giảm sai số bình phương theo số mẫu từng lớp so với đích 70/15/15. PID, URL, domain, nhãn và hash chỉ phục vụ quản lý mẫu.

Ba thành viên dùng ba seed 42, 43, 44 cho mỗi modality. Tổng cộng 18 run. Random Forest và XGBoost học trực tiếp ma trận số. MLP chuẩn hóa bằng trung bình và độ lệch chuẩn của train, dùng ReLU, BCEWithLogitsLoss và Adam. Dừng sau 8 epoch không cải thiện validation loss. Lưu checkpoint lúc cải thiện, với scaler và trọng số đủ cho inference. Xem configs/models.yaml để lấy siêu tham số.

Chọn threshold trong 0,05 đến 0,95, bước 0,05 trên validation. Xếp theo F2 lớp phishing cao nhất, rồi precision cao hơn, FPR thấp hơn và cuối cùng threshold cao hơn. Báo cáo confusion matrix theo thứ tự lớp 0, 1. Cột pr_auc dùng tích phân hình thang trên đường precision–recall. Cột average_precision dùng tổng precision nhân với mức tăng recall ở từng bậc. Cả hai dùng xác suất trước khi áp ngưỡng.

Chọn cặp thuật toán/modality theo F2 trung bình ba seed, sau đó theo precision trung bình giảm dần, FPR trung bình tăng dần, rồi tên thuật toán và modality. Công bố mean, độ lệch chuẩn mẫu và từng seed. Trong nhóm thắng chọn seed theo F2, precision, FPR và cuối cùng seed nhỏ hơn. Khóa cùng lúc threshold, bộ tiền xử lý, schema, hash checkpoint và hash split trước khi chấm test. URL-only dự phòng cũng lấy từ nhóm URL-only đủ ba seed. Báo cáo test chỉ dành cho mô hình chính đã khóa.

SHAP sử dụng tối đa 32 mẫu train làm nền, 24 mẫu validation để minh họa và cùng hàm xác suất lớp phishing cho cả ba mô hình. Summary, waterfall, importance và bảng đóng góp được ghi trong results/explanations/. API dùng chênh lệch xác suất khi lần lượt thay từng đặc trưng từ trung vị train. Cách giải thích nhanh này phụ thuộc thứ tự cột, vì vậy response ghi rõ phương pháp.
