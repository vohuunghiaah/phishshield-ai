# Chẩn đoán

| Dấu hiệu | Cách xử lý |
|---|---|
| setup không tìm thấy model | Dùng -ModelSource với ZIP nội bộ hoặc thư mục đã cấp quyền. |
| Hash hoặc parity sai | Kiểm digest ZIP, khôi phục bundle từ trưởng nhóm, giữ Python/sklearn theo lock. |
| /health 200 nhưng /ready 503 | Kiểm cả hai selection.json, file joblib và registry, chạy verify_models.py. |
| UI không kết nối API | Kiểm cổng launcher, trạng thái terminal và URL nội bộ của web trong Compose. |
| 422 khi gửi snapshot | Kiểm UTF-8, URL, HTML rỗng, mode và tên trường. |
| Full Scan chuyển về URL-only | Phiên bản này chưa có egress đã thẩm định. Dùng snapshot tĩnh khi đã có HTML. |
| Cổng đã dùng | Dùng -ApiPort 8001 -UiPort 8502 hoặc biến PHISH_API_PORT/PHISH_UI_PORT cho Compose. |
| Execution policy chặn launcher | Có thể dùng các lệnh uv và Python trực tiếp từ thư mục dự án, như hướng dẫn Windows. |
| Docker daemon chưa chạy | Khởi động Docker Desktop, đợi Engine ready, chạy docker compose up hoặc dùng bản native. |
