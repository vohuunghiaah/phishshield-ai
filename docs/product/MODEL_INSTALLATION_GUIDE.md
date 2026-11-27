# Cài model

Nhận phishshield-models-v1.0.0.zip qua kênh nội bộ của trưởng nhóm. Bundle 7.477.704 byte có SHA-256 **0f9251e315af95968b19aa4fb4144e373a15970ddefbcc2a1ba4a8b134daacfc**. Kiểm bằng `Get-FileHash -Algorithm SHA256 <file>`.

```powershell
.\setup.ps1 -ModelSource 'C:\path\to\phishshield-models-v1.0.0.zip'
.\.venv\Scripts\python.exe scripts/verify_models.py
```

Có thể dùng script install_models.ps1 với -Source trỏ tới ZIP hoặc thư mục nghiên cứu đã mount và có quyền. Script chỉ đọc sáu payload có tên, độ dài và digest được pin ở source. Toàn bộ được kiểm trước khi publish vào đúng cây thư mục. Metadata tham chiếu nằm trong MODEL_MANIFEST.json, SHA256SUMS.txt và MODEL_CARD.md. Model không được nhận qua API/UI. GitHub Release cho bundle cần xác nhận quyền phân phối riêng. [Model Card](../../MODEL_CARD.md).
