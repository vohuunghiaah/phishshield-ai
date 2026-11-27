# Benchmark cục bộ

Intel Core i5-12450HX, RAM hệ thống 12.578.578.432 byte, Windows build 26300, Python 3.11.15, scikit-learn 1.6.1. Mỗi phép đo 3 warm-up, 25 lần đo tuần tự, một client, fixture tổng hợp trên loopback. Bảng ghi P50/P95 bằng ms.

| Công đoạn | Primary | Fallback |
|---|---:|---:|
| Nạp và kiểm model | 135,24 / 166,77 | 81,81 / 98,52 |
| Trích feature | 0,134 / 0,226 | 0,0135 / 0,0147 |
| Một lần predict_proba | 37,59 / 41,32 | 37,69 / 53,16 |
| Giải thích tuần tự gồm scoring | 40,34 / 54,95 | 36,66 / 43,12 |
| HTTP từ client tới JSON | 184,61 / 212,78 | 143,77 / 221,06 |

Kích thước primary 4.787.201 byte, fallback 2.775.878 byte. Working set sau benchmark là 209.137.664 byte API và 151.445.504 byte UI. Đây là ảnh chụp bộ nhớ, không đo peak. Request mới kiểm/nạp checkpoint; phép đo API bao gồm I/O đó. Các công đoạn không cộng trực tiếp vì đánh giá theo batch khác nhau. Không có latency tải HTML từ Internet.

Đã thử SHAP TreeExplainer 0.47.2, interventional, output probability, 32 dòng Train làm nền và 8 dòng Validation mỗi modality. Class index phishing là 1, shape [1,34,2] hoặc [1,17,2]. Residual cộng tính tối đa 2,75×10⁻⁸. P50/P95 primary 42,96/75,24 ms, fallback 26,25/45,30 ms, chưa tính khởi tạo explainer. Demo giữ attribution tuần tự để hoạt động với dependency CPU tối thiểu, không cần phân phối background theo mẫu. [Timing](benchmark.json) · [Phần cứng](machine.json) · [Đối chiếu SHAP](tree_shap.json).


Ba lần khởi động độc lập qua start.ps1 trên clone sạch, không warm-up riêng. API ready P50/P95: 7.87/10.10 giây. Streamlit ready P50/P95: 9.10/17.05 giây. P95 ở n=3 là phân vị mô tả nội suy. [Số đo theo lần](clean_run.json).
