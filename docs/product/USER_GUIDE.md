# Sử dụng Website Scanner

Mở Website Scanner, chọn Quick Scan, nhập https://example.org/ rồi nhấn **Phân tích website**. Kiểm nhãn Fallback, 17 đặc trưng và ngưỡng 0,15. Nếu chọn Full Scan, hệ thống nêu rõ lý do chuyển về phân tích URL. Trang đích không được mở.

Ở **Phân tích nâng cao**, cung cấp cùng URL và dán snapshot tĩnh, hoặc upload tệp HTML UTF-8. Ví dụ tổng hợp: `<html><title>Demo</title><form><input type="password"></form></html>`. Đây là dữ liệu minh họa; biểu mẫu đăng nhập cũng có thể hợp lệ. Kết quả dùng Primary, 34 cột và ngưỡng 0,20.

Ở **Giải thích**, đọc giá trị cột và hướng đóng góp. Ở **Hiệu năng**, đọc ma trận với hàng là nhãn thật và cột là nhãn dự đoán. “Dưới ngưỡng” vẫn có trường hợp bỏ sót. Điểm RF chưa calibration. [Kịch bản trình diễn](DEMO_GUIDE.md).
