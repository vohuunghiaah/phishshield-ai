# Khởi động native trên Windows

Trong PowerShell tại thư mục clone, chạy:

```powershell
.\setup.ps1 -ModelSource 'C:\path\to\phishshield-models-v1.0.0.zip'
.\start.ps1 -FullScan
```

Cần uv và Python 3.11.15 (uv có thể chuẩn bị interpreter). Môi trường .venv nằm trong clone. Setup cài extra demo và kiểm checksum, schema, effective parameters và prediction parity. Khi đã cài model chỉ cần start. Launcher kiểm bundle, chờ /ready rồi mở Streamlit; terminal in địa chỉ. Mở http://127.0.0.1:8501. Dừng bằng Ctrl+C hoặc .\stop.ps1. Để đổi cổng, truyền cùng -ApiPort và -UiPort cho cả start và stop.

Full Scan cần Docker Desktop ở chế độ Linux containers. `-FullScan` khởi động worker và chờ worker xác nhận cô lập. Kiểm bằng `Invoke-RestMethod http://127.0.0.1:8000/capabilities`. Launcher không có tham số sẽ dùng worker đang sẵn sàng. `-Offline` cho phép chạy Quick Scan và Snapshot Analysis khi không có Docker hoặc mạng. Sau `./stop.ps1`, dùng `docker compose -f compose.fetcher.yaml down` để dừng cả worker.

Để chạy thủ công trên Linux với Python và uv, dùng `uv sync --frozen --python 3.11.15 --extra demo`, `uv run --no-sync python scripts/install_models.py /path/to/bundle.zip`, rồi `uv run --no-sync python scripts/run_local.py`. Phương án Linux được kiểm ở container. Phần nghiên cứu có các extra riêng cho tuning, trees, mlp, explain và dữ liệu Drive nội bộ.
