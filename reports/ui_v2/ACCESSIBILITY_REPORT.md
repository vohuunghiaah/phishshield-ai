# Kiểm tra khả năng tiếp cận

Axe-core 4.10.3 chạy trên Chromium ở bốn viewport đối với Scanner, kết quả Quick Scan, Hiệu năng và Hướng dẫn. Bộ quy tắc gồm WCAG 2 A/AA, 2.1 A/AA và 2.2 AA. Phép kiểm bán tự động đã phát hiện lỗi tương phản, thuộc tính ARIA và nút thiếu tên ở bản cũ. Các lượt chạy cuối trên 16 tổ hợp trang/kích thước ghi nhận 0 vi phạm tự động.

- Tab đưa focus qua điều hướng, ô URL và nút gửi. URL có nhãn hiện trên màn hình, Enter gửi form. Nút chính cao 46 px; vùng nhãn radio cao 40 px. Kiểm tra bằng bàn phím đã chạy một lượt Quick Scan thực.
- Dấu cộng/trừ, kết luận bằng chữ và nhãn cột bổ sung thông tin cho các thanh màu. Dữ liệu số có thể đọc qua danh sách và phần chi tiết. Tệp font hỗ trợ tiếng Việt được serve local.
- Impeccable detect qua Chrome DevTools Protocol kiểm Scanner ở 1440 và 390 px, báo cáo và hiệu năng ở 1440 px. JSON rỗng tương ứng với lượt đó không có finding. Bản đầu có cảnh báo tương phản; kích thước chữ trên mobile đã được tăng sau khi detector đánh dấu.
- **Kiểm tra thủ công còn lại.** Axe đánh dấu một số trường hợp tương phản cần người đánh giá. Streamlit 1.45.1 xuất `html.lang=en` dù nội dung tiếng Việt. Chưa xác minh phát âm tiếng Việt với NVDA hoặc VoiceOver. Kết quả này không phải chứng nhận đáp ứng toàn bộ WCAG AA.

[Scanner và focus](evidence/layout-final.json) · [Kết quả, metric và hướng dẫn](evidence/views-final.json) · [Axe trước thiết kế](evidence/baseline-axe.json) · [Detector mobile](evidence/impeccable-final-scanner-390x844.json).
