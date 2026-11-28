# Thành phần

| Thành phần | Hành vi và tiêu chí |
|---|---|
| Điều hướng | Dùng liên kết có nhãn. Bốn mục cùng một hàng trên desktop và hai hàng trên màn hình hẹp. Dùng bộ biểu tượng Material của Streamlit kèm chữ. Wordmark có dấu hiệu hình khiên riêng. |
| Form URL | Có nhãn hiển thị và một nút gửi. Enter gửi URL. Một nhóm radio chọn chế độ. Snapshot mở trường dán hoặc tải tệp UTF-8. |
| Trạng thái | Đọc capabilities từ API. Nếu API mất kết nối, hiện hướng xử lý và khóa gửi. Nếu worker tắt, giữ Quick và Snapshot. Spinner bao phủ đúng thời gian chờ HTTP. |
| Kết luận | In nhãn từ prediction. Hiện điểm và ngưỡng thực. Fallback có lý do từ API. Ghi lại mode người dùng chọn và số đặc trưng đã dùng. |
| Dấu hiệu | Dùng tên tiếng Việt, giá trị quan sát, thanh hai hướng và số có dấu. Không suy diễn quan hệ nhân quả từ đóng góp. |
| Hiệu năng | Hai bảng cho metric và ma trận nhầm lẫn, tiêu đề hàng/cột rõ, số lượng mẫu tính từ ma trận. Metadata và metric lấy từ API. |

Focus phải nhìn được khi di chuyển bằng Tab. Nội dung quan trọng đọc được bằng chữ dù bỏ màu. Không đưa HTML người dùng vào HTML trình bày.
