# Docker Compose

Chuẩn bị bộ model dưới thư mục clone bằng setup.ps1. Khởi động Docker Desktop ở chế độ Linux containers, rồi:

```powershell
docker compose -f compose.yaml -f compose.fullscan.yaml up --build -d --wait
docker compose -f compose.yaml -f compose.fullscan.yaml ps
curl.exe http://127.0.0.1:8000/capabilities
curl.exe http://127.0.0.1:8000/ready
docker compose -f compose.yaml -f compose.fullscan.yaml down
```

Mở UI tại 127.0.0.1:8501. Nếu native đang chiếm cổng, đặt $env:PHISH_API_PORT='18000' và $env:PHISH_UI_PORT='18501' trước khi up. Container web gọi api:8000 nội bộ. Hai dịch vụ không chạy với quyền root. Chỉ api nhận mount checkpoint và metrics read-only. Ảnh chỉ chứa mã và các gói demo. Kiểm tra HTTP thật trong hồ sơ nghiệm thu. Worker nằm trên bridge dành riêng cho truy cập ra ngoài và mạng điều khiển nội bộ với API. Worker không publish cổng ra host trong cấu hình này. Dùng riêng `compose.yaml` khi cần chạy ngoại tuyến. [Chính sách mạng](SECURITY_MODEL.md).
