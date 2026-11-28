# Hai vòng đánh giá trên Chromium

| Vòng | Quan sát khi thao tác | Thay đổi và bằng chứng |
|---|---|---|
| 1 · Scanner | Thanh bên màu mực làm chữ của liên kết Streamlit khó đọc. Ở 768 px, ngăn kéo rộng 336 px che đầu biểu mẫu. Trên điện thoại wordmark biến mất. | Thay thanh bên bằng masthead và bốn liên kết trong luồng trang. [Desktop trước](screenshots/before/scanner-1440x900.png) · [Tablet sau](screenshots/after/scanner-768x1024.png). |
| 1 · Chọn chế độ | Bật Snapshot nâng cao vẫn để Full hoặc Quick hiển thị đang chọn. Ô URL đứng sau các tùy chọn. | Đưa URL và hành động chính lên đầu. Chỉ có một nhóm radio. Khi chọn Snapshot, xuất hiện trường HTML. [Snapshot](screenshots/desktop/snapshot.png). |
| 2 · Điện thoại | Tên mục hướng dẫn dài tràn khỏi nền điều hướng. Trạng thái dịch vụ chỉ 11,52 px. Ở tablet, phần dữ liệu HTML bị chia thành nhiều dòng ngắn. | Rút gọn nhãn Hướng dẫn, tăng chữ trạng thái lên 14 px, xếp tên nguồn và mô tả theo hàng. [Điện thoại sau](screenshots/after/scanner-390x844.png). |
| 2 · Khả năng đọc | Màu CSS của chữ phụ đủ đậm nhưng opacity của phần tử cha làm giảm tương phản thực. | Đặt độ mờ của cả vùng chú thích và chữ về 1. Đo lại trên trang thật bằng axe và Impeccable. [Phép đo](ACCESSIBILITY_REPORT.md). |
| 2 · Báo cáo | Cần đọc được chiều đóng góp khi không phân biệt hai màu. | Hiện dấu, giá trị thực và thanh hai phía mốc 0. [Minh họa từ mô hình](screenshots/mobile/contributions.png). |

Ảnh gốc là viewport thật ở zoom 100%. Hai vòng có đối chiếu với phản hồi API; đánh giá thiết kế là đánh giá chuyên gia. Chưa đo thời gian hoàn thành tác vụ với người dùng đại diện.
