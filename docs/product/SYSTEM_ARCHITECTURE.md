# Kiến trúc và phạm vi Gate 7

1. Streamlit nhận đầu vào và POST JSON tới FastAPI.
2. Middleware chặn body quá giới hạn hoặc quá hạn. Backend xác định modality và kiểm tra chữ ký nhận dạng model bằng SHA-256 đã khóa trong mã.
   Với `mode=full`, API gửi URL tới worker qua HTTP nội bộ. Worker xác minh địa chỉ ở mỗi lần chuyển hướng rồi trả HTML và URL cuối. API đưa cả hai vào cùng đường suy luận của Snapshot Analysis.
3. Cùng bộ trích của nghiên cứu tính 17 hoặc 34 biến, đúng thứ tự của bundle. RF và vector trung vị Train nằm trong joblib đã xác minh.
4. Service so lớp phishing với ngưỡng, tính đóng góp tuần tự và trả JSON. UI hiển thị score, thông tin checkpoint, thời gian và lý do fallback.
5. /performance đọc số liệu primary được phân phối trong bundle. /ready thử nạp cả hai vai trò.

Drive là kho nghiên cứu có quyền truy cập riêng. GitHub lưu mã và tài liệu công khai. Bản cài chỉ đọc checkpoint và manifest dưới thư mục local hoặc các mount read-only trong container. V1/V2 và selection đã khóa giữ nguyên ở kho nghiên cứu; Gate 7 bổ sung packaging, runtime và thẩm định triển khai. [Giao thức](../EXPERIMENT_PROTOCOL.md) · [Registry bản phát hành](../../MODEL_MANIFEST.json).
