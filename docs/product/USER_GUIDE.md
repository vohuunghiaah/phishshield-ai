# Sử dụng Website Scanner

Mở Website Scanner. Khi worker sẵn sàng, giao diện chọn sẵn **Full Scan**. Nhập `https://example.org/` rồi nhấn **Phân tích website**. Khi tải được HTML, kết quả hiển thị Primary, 34 đặc trưng và ngưỡng 0,20. Nếu website không trả HTML phù hợp, kết quả ghi lý do chuyển sang 17 đặc trưng. Để phân tích ngoại tuyến, chọn **Quick Scan**.

Ở **Phân tích nâng cao**, cung cấp cùng URL và dán snapshot tĩnh, hoặc upload tệp HTML UTF-8. Ví dụ tổng hợp: `<html><title>Demo</title><form><input type="password"></form></html>`. Đây là dữ liệu minh họa; biểu mẫu đăng nhập cũng có thể hợp lệ. Kết quả dùng Primary, 34 cột và ngưỡng 0,20.

Ở **Giải thích**, đọc giá trị cột và hướng đóng góp. Ở **Hiệu năng**, đọc ma trận với hàng là nhãn thật và cột là nhãn dự đoán. “Dưới ngưỡng” vẫn có trường hợp bỏ sót. Điểm RF chưa calibration. [Kịch bản trình diễn](DEMO_GUIDE.md).
