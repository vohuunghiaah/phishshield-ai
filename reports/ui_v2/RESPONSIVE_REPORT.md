# Kiểm thử bố cục

| Viewport | Trước | Sau | Quan sát bản cuối |
|---|---|---|---|
| 1440 × 900 | [Ảnh](screenshots/before/scanner-1440x900.png) | [Ảnh](screenshots/after/scanner-1440x900.png) | Bốn liên kết cùng hàng, thông tin phạm vi bên phải. |
| 1280 × 800 | [Ảnh](screenshots/before/scanner-1280x800.png) | [Ảnh](screenshots/after/scanner-1280x800.png) | URL và nút gửi nằm trong viewport đầu. |
| 768 × 1024 | [Ảnh](screenshots/before/scanner-768x1024.png) | [Ảnh](screenshots/after/scanner-768x1024.png) | Điều hướng chia hai hàng, không che ô nhập. |
| 390 × 844 | [Ảnh](screenshots/before/scanner-390x844.png) | [Ảnh](screenshots/after/scanner-390x844.png) | Một cột, masthead giữ trạng thái, bảng metric và biểu đồ vẫn đọc được. |

Playwright đo chiều rộng tài liệu và vùng chính, khung liên kết, khung từng đoạn chữ hiển thị và kích thước nút. Ở bốn kích thước, chữ trên các trang được đo nằm trong viewport, các liên kết Scanner nằm trọn bên trong màn hình. Các số đo áp dụng cho Chromium, zoom 100% và nội dung đã thử. Chưa kiểm trên thiết bị iOS thật.

[Hình học Scanner](evidence/layout-final.json) · [Trang khác](evidence/views-final.json) · [Ma trận nhầm lẫn trên điện thoại](screenshots/mobile/performance.png).
