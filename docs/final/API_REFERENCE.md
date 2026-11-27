# API PhishShield AI

Gốc mặc định [http://127.0.0.1:8000](http://127.0.0.1:8000/docs). Nội dung yêu cầu POST là application/json. HTTP 200 trả JSON, ngoại trừ Swagger UI trả HTML.

| Phương thức | Đường dẫn | Đầu vào và ý nghĩa |
|---|---|---|
| GET | /health | Trạng thái tiến trình |
| GET | /ready | Kiểm tra có thể nạp cả hai bundle |
| GET | /model/info, /model-info | Hai vai trò cùng model, phase, ngưỡng, seed, schema, số biến và SHA-256 |
| GET | /performance | Metric primary trên Locked Test và định danh mô hình tương ứng |
| POST | /predict | URL HTTP(S) và HTML tùy chọn. Trả dự đoán kèm giải thích |
| POST | /predict-from-html | Bắt buộc có cả URL và HTML |
| POST | /explain | Cùng đầu vào và cách tính với /predict, bao gồm explanation |
| GET | /docs | Giao diện Swagger cho OpenAPI |

## Gửi yêu cầu

```python
import requests

api = "http://127.0.0.1:8000"
payload = {"url": "https://example.org/", "html": "<html><title>Demo</title></html>"}
response = requests.post(api + "/predict", json=payload, timeout=25)
response.raise_for_status()
result = response.json()
print(result["feature_modality"], result["threshold"], result["prediction"])
```

Với cấu hình demo, bỏ trường html hoặc dùng null chọn url_only (17 cột). Snapshot khác rỗng chọn url_html (34 cột). Nội dung HTML tĩnh được phân tích như dữ liệu. URL tối đa 8.192 ký tự. Giới hạn HTML 8 MiB theo UTF-8, giới hạn JSON trước khi parse là 8 MiB + 64 KiB. Thời gian chờ đọc thân POST là 15 giây.

## Đọc phản hồi

| Trường | Quy ước |
|---|---|
| prediction, risk_level | 1 và “cao” khi điểm ≥ threshold, 0 và “thấp” khi dưới ngưỡng |
| phishing_probability | Điểm lớp dương do RF xuất ra, chưa hiệu chỉnh trên tập calibration độc lập |
| model_name, model_version, model_phase | random_forest, 12 ký tự đầu SHA-256 và TUNED_V2 |
| feature_modality, feature_count | url_html/34 hoặc url_only/17 |
| threshold, html_extraction_status | 0,20 cho primary, 0,15 cho fallback. Trạng thái demo là snapshot hoặc disabled |
| explanation | text, method và contributions, mỗi phần tử có feature, value và contribution có dấu |
| warnings | Lưu ý về diễn giải kết quả |

Trong bản ghi HTTP thật cho URL example.org, fallback trả điểm 0,05207749, ngưỡng 0,15, nhãn 0 và model_version 0ce231574e7d. Giá trị đóng góp là hiệu giữa hai lần tính điểm khi thay tuần tự các biến từ trung vị Train theo thứ tự schema. Danh sách hiển thị tối đa năm biến theo trị tuyệt đối. Tổng của riêng năm biến này thường không tái tạo toàn bộ điểm. Hồ sơ SHAP khoa học có phương pháp và tập tham chiếu riêng. Ví dụ đầy đủ có status, request và response (kho nghiên cứu nội bộ).

## Mã lỗi

| Mã | Ý nghĩa và thao tác |
|---:|---|
| 408 | Quá thời hạn nhận body. Gửi lại từ máy local với payload đã chuẩn bị. |
| 413 | Dữ liệu vượt hạn mức. Giảm kích thước snapshot hoặc JSON. |
| 422 | Thiếu trường bắt buộc, URL sai, JSON sai dạng hoặc snapshot rỗng. Kiểm lại dữ liệu gửi. |
| 503 | Thiếu cấu hình workspace, checkpoint hoặc schema sai, hay kết quả Test chưa hợp lệ. Kiểm /ready và manifest. |

Việc thiếu metadata của một vai trò có thể trả null ở /model/info. Dùng /ready để kiểm khả năng phục vụ đầy đủ. [Thông số model đã chọn](../../reports/final/tables/T20_selection.csv).
