# Chạy và kiểm tra PhishShield AI trên máy cục bộ

Hai dịch vụ dùng chung môi trường Python 3.11.15 đã khóa bằng uv.lock. FastAPI đọc hai checkpoint từ workspace. Streamlit gọi FastAPI qua HTTP. Có thể chạy demo CPU mà không cài PyTorch. Cần sẵn các tệp Google Drive trên đĩa (hoặc workspace đã mount), quyền đọc checkpoint, manifest và kết quả Test. Cài dependency lần đầu cần kết nối tới nguồn gói.

## Windows PowerShell

```powershell
Set-Location -LiteralPath 'C:\dev\phishshield-ai'
uv sync --frozen --python 3.11.15 --extra demo
uv run --frozen --extra demo python scripts/run_local.py
```

## Linux

```bash
cd '/path/to/phishshield-ai'
uv sync --frozen --python 3.11.15 --extra demo
uv run --frozen --extra demo python scripts/run_local.py
```

Thay đường dẫn bằng thư mục chứa pyproject.toml và checkpoints. Trên Colab, ổ được mount phải chứa chính workspace gồm các artifact, còn 127.0.0.1 thuộc máy ảo Colab. Bản bàn giao đã kiểm thử qua trình duyệt trên Windows cục bộ. Để tái hiện bản demo tại máy người xem, dùng địa chỉ trên máy đang chạy trình khởi động.

Mở [Streamlit](http://127.0.0.1:8501) và [Swagger](http://127.0.0.1:8000/docs). Script thiết lập PHISHSHIELD_DRIVE_ROOT, PYTHONPATH, PHISHSHIELD_API_URL và tắt egress cho cả hai tiến trình con. Dừng bằng Ctrl+C. Ví dụ dùng cổng khác như phiên nghiệm thu:

```bash
uv run --frozen --extra demo python scripts/run_local.py --api-port 8765 --ui-port 8766
```

## Kiểm tra sau khởi động

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
uv run --frozen --extra demo python scripts/verify_local.py --base http://127.0.0.1:8000
```

Trên Windows có thể gọi curl.exe. Kịch bản kiểm 14 yêu cầu và ghi kết quả vào reports/final/http_evidence.json. Dùng cổng API thực tế nếu đã đổi cổng. Để tái lập kiểm thử trình duyệt, cần Node.js, Playwright và Chromium tương thích. Chạy lệnh dưới trong môi trường Node đã có Playwright. Nếu dùng Chrome đã cài, đặt PHISHSHIELD_CHROME bằng đường dẫn executable. Năm ảnh được ghi vào reports/final/screenshots/.

```bash
node scripts/check_ui.cjs http://127.0.0.1:8501
```

## Tái lập bảng và hình

```bash
uv run --frozen --python 3.11.15 --extra tuning --extra trees --extra mlp --extra explain python scripts/generate_final_analysis.py
uv run --frozen --python 3.11.15 --extra test --extra demo --extra tuning --extra trees --extra mlp --extra explain python -m pytest -q
```

Lệnh đầu kiểm hash, tải checkpoint tin cậy, phát lại Validation và đọc các dự đoán OOF/Test đã lưu. Nó ghi bảng, hình và biên bản tại reports/final. Không chạy lại các notebook training để tạo báo cáo. Test CUDA thực là một phép kiểm opt-in, cần thiết bị và bản PyTorch phù hợp. Thời gian đọc dữ liệu phụ thuộc trạng thái đồng bộ Drive.

## Chẩn đoán

| Hiện tượng | Kiểm tra |
|---|---|
| Không kết nối được UI/API | Kiểm địa chỉ và cổng trên terminal, thử /health. Hai dịch vụ phải cùng còn chạy. |
| /ready trả 503 | Kiểm hai thư mục checkpoints/selected_model/{primary,url_fallback}, selection.json và manifests/model_selection_v2.json. Khôi phục đúng bytes từ nguồn tin cậy, đối chiếu T20. |
| Báo thiếu cohort.csv trong notebook hoặc audit | Xác nhận root trỏ vào workspace có data/processed/cohort.csv và data/splits/lock.json. Đối chiếu SHA của cohort đã khóa trước khi chạy lại bước đọc dữ liệu. |
| Lỗi backend matplotlib khi chạy thủ công từ kernel | Cho subprocess dùng môi trường có MPLBACKEND=Agg. Lỗi kế thừa backend inline có thể xảy ra ngay khi import matplotlib. |
| /predict trả 422 hoặc 413 | Kiểm URL HTTP(S), HTML rỗng, kích thước UTF-8 và cấu trúc JSON. |
| Máy báo cổng đã được sử dụng | Khởi chạy với --api-port và --ui-port là hai cổng trống. |

Ứng dụng mặc định chỉ bind loopback. Hồ sơ bàn giao đo chức năng ở local. Kiểm thử tải đồng thời, xác thực người dùng, TLS triển khai và vận hành bên ngoài cần môi trường nghiệm thu riêng. [Registry lựa chọn](../../reports/final/tables/T20_selection.csv) · [Hợp đồng API](API_REFERENCE.md).
