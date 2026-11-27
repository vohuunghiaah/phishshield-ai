# Bằng chứng chạy local

Windows native: setup.ps1 dựng .venv bằng uv.lock, cài từ ZIP, verify SHA và hai fixture thành công. start.ps1 kiểm model, phục vụ FastAPI 127.0.0.1:8000, rồi mở Streamlit 127.0.0.1:8501 sau /ready. curl.exe /health trả ok. Requests thực hiện 14 yêu cầu trên HTTP thật. Playwright chạy Quick, Snapshot, trang đóng góp, trang Test và viewport mobile. [HTTP](http_evidence.json) · [Ảnh](screenshots/) · [Swagger và Full Scan](browser_modes.json).

Docker Engine 29.9.2, Compose 5.6.1. Đã chạy docker compose up --build -d --wait với host ports 18000 và 18501, ps báo cả api/web healthy. GET /ready trả ready; Streamlit /_stcore/health trả ok; POST cho hai fixture lần lượt có 17 và 34 biến. Đã xem access log và down thành công. Native dùng các cổng mặc định riêng.
