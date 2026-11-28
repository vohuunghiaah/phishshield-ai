# REST API sản phẩm

Base mặc định là http://127.0.0.1:8000. GET /health kiểm tiến trình, /ready tải hai bundle, /model/info và /model-info trả thông tin hai role, /performance trả metric Test của primary, /docs mở Swagger. POST /predict và /explain nhận JSON. POST /predict-from-html yêu cầu URL và HTML.

| Payload | Kết quả |
|---|---|
| {"url":"https://example.org/","mode":"quick"} | url_only, 17 cột, ngưỡng 0,15 |
| {"url":"https://example.org/","mode":"snapshot","html":"<p>Demo</p>"} | url_html, 34 cột, ngưỡng 0,20 |
| {"url":"https://example.org/","mode":"full"} | `fetched` → `url_html`, 34 đặc trưng, ngưỡng 0,20. `fetch_failed` → `url_only`, 17 đặc trưng và lý do |

`GET /capabilities` trả `full_scan` theo trạng thái worker. `fetch_ms` đo thời gian gọi worker, kể cả khi website không trả được HTML. Khi chạy ngoại tuyến, yêu cầu Full Scan trả trạng thái `disabled` và lý do chuyển nhánh. Đích bị chính sách mạng chặn trả HTTP 422. Worker đã cấu hình nhưng mất kết nối hoặc quá tải trả HTTP 503.

Khi bỏ mode, có HTML thì dùng primary, chỉ có URL dùng fallback. Nhãn 1 khi score ≥ ngưỡng. Các trường gồm prediction, phishing_probability, threshold, risk_level, model_name, model_version (prefix SHA), model_phase, feature_modality, feature_count, html_extraction_status, fallback_reason, processing_ms, explanation và warnings. Trong explanation, giá trị thực và contribution có dấu cho tối đa năm biến. processing_ms đo nạp model và suy luận tại backend, không gồm thời gian truyền body.

422 cho JSON/URL/mode/snapshot sai; 408 cho timeout nhận body; 413 cho kích thước vượt ngưỡng; 503 khi model/schema/metadata không phục vụ được. [Phản hồi thật](../../reports/product/http_evidence.json).
