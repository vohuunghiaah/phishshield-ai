# Hướng dẫn sử dụng PhishShield AI

Mở địa chỉ Streamlit của phiên local. Trong cấu hình mặc định đó là [127.0.0.1:8501](http://127.0.0.1:8501). Thanh bên cung cấp bảy màn hình. “Trang chủ” giới thiệu bài toán. “Giới thiệu” mô tả nguồn dữ liệu và giới hạn.

1. Mở **Website Scanner**, nhập URL với http:// hoặc https:// và chọn **Phân tích**. Dùng https://example.org/ cho bài demo. Chế độ này chạy RF URL-only với 17 biến, ngưỡng 0,15. Bạn có thể kiểm tra chuỗi URL mà không mở website.
2. Khi đã có snapshot, mở **Phân tích nâng cao**. Nhập URL nguồn và dán HTML hoặc tải tệp HTML tĩnh. Ví dụ dùng `<html><title>Demo</title><p>Trang mẫu</p></html>`. Chọn **Phân tích** để chạy RF URL+HTML với 34 biến, ngưỡng 0,20. Giới hạn snapshot là 8 MiB.
3. Mở **Kết quả** để xem lại lần phân tích trong phiên. So sánh điểm với ngưỡng hiển thị và đối chiếu nhãn primary/fallback. Cảnh báo dương có nghĩa mô hình phát hiện dấu hiệu phishing. Kết quả dưới ngưỡng vẫn có thể bỏ sót.
4. Mở **Giải thích** để đọc tên đặc trưng, giá trị và đóng góp có dấu. Giá trị dương kéo điểm lên trong phép thay biến của ứng dụng. Giá trị âm kéo xuống. Danh sách chọn tối đa năm đóng góp lớn nhất theo trị tuyệt đối.
5. Mở **Hiệu năng** để xem số liệu của primary trên 2.299 mẫu Test. Phần này mô tả thí nghiệm đã khóa, độc lập với lần quét vừa nhập.

Nếu giao diện báo không kết nối, mở /health và /ready trên cổng API của phiên local. Nếu đầu vào bị từ chối, kiểm tra scheme của URL, khoảng trắng trong HTML và kích thước tệp. Chỉ gửi snapshot bạn có quyền sử dụng. [Hướng dẫn chạy](DEPLOYMENT_GUIDE.md) · [Ảnh kết quả URL](../../reports/final/screenshots/01_url_fallback.png) · [Ảnh kết quả có HTML](../../reports/final/screenshots/02_html_primary.png) · [Màn hình giải thích](../../reports/final/screenshots/03_explanation.png).
