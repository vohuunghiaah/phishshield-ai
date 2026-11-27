# Nghiệm thu Full Scan trên máy local

Ngày 28/11/2026. Full Scan đã được bật cho bản chạy Windows sau khi kiểm thử trên một worker và cặp API/UI riêng. Phiên thử nghiệm dùng cổng 18732/18141/18541. Phiên sử dụng mặc định dùng cổng 18731/8000/8501. Cả hai dùng checkpoint Random Forest của bundle v1.0.0.

| Phép kiểm | Kết quả quan sát |
|---|---|
| Nhập `https://example.org/` trên Website Scanner | Giao diện chọn sẵn Full Scan. Một lần nhấn **Phân tích website** tải HTML tĩnh rồi hiển thị Primary, `url_html`, 34 đặc trưng. |
| Đối chiếu với Snapshot Analysis | Tài liệu thử nghiệm dài 577 byte. Cùng URL và nội dung cho cùng nhãn, checkpoint `0a78a47a3a46`, ngưỡng 0,20 và điểm khoảng 0,111695. Sai lệch điểm nhỏ hơn 10⁻¹². |
| Đích bị chặn và website không khả dụng | Loopback trả HTTP 422. Tên miền thử nghiệm `.invalid` trả `fetch_failed`, lý do và kết quả 17 đặc trưng. Quick Scan dùng ngưỡng 0,15. |
| Worker | UID 65534, CapEff và CapBnd bằng 0, NoNewPrivs bằng 1, filesystem chỉ đọc và không có volume mount. Kiểm tra khởi động xác nhận kết nối tới socket đang lắng nghe trên loopback bị chặn. Yêu cầu thiếu header giao thức trả 415. |
| Docker Compose đầy đủ | API, web và worker cùng chạy. API báo `full_scan=true`, Full Scan trả `fetched` và 34 đặc trưng, Streamlit health trả `ok`. |

[Phản hồi API đã ghi](fullscan_http.json) · [Kết quả trình duyệt](browser_modes.json) · [Ảnh giao diện](screenshots/06_full_scan.png)

## Chạy lại

Sau khi cài bundle và khởi động Docker Desktop, mở PowerShell trong thư mục sản phẩm và chạy `.\start.ps1 -FullScan`. Mở PowerShell thứ hai và chạy `.\.venv\Scripts\python.exe scripts/verify_fullscan.py` để kiểm lại qua API bằng tên miền ví dụ. Tài liệu trên website có thể thay đổi theo thời điểm. Script đối chiếu nội dung lấy ở cùng lần kiểm.

Full Scan xử lý HTML tĩnh trên HTTP(S) công khai qua IPv4. Worker giới hạn ba chuyển hướng, 2 MiB và 12 giây cho mỗi lượt. Website cần trình duyệt chạy JavaScript có thể trả HTML khung. Các số liệu thử nghiệm trên đây xác nhận luồng triển khai và suy luận. Hiệu năng phát hiện phishing trên cohort được báo cáo riêng trong [model card](../../MODEL_CARD.md).
