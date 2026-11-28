# Hồi quy chức năng và tính toàn vẹn mô hình

| Phép kiểm | Quan sát |
|---|---|
| API và khởi động lại | FastAPI trả health/ready. Sau khởi động lại native, capabilities báo Full Scan sẵn sàng; Swagger thực thi GET /health. |
| Quick Scan | Fixture phát hành cho điểm 0,05207749236559011, nhãn 0, 17 đặc trưng và ngưỡng 0,15. |
| Snapshot Analysis | Fixture phát hành cho điểm 0,15434539841045788, nhãn 0, 34 đặc trưng và ngưỡng 0,20. Đã kiểm cả dán HTML và upload tệp UTF-8. URL đã gõ vẫn giữ nguyên khi đổi chế độ và chọn tệp. |
| Full Scan | `example.org` trả cùng digest HTML với lần nghiệm thu Gate 7. Chênh lệch điểm ở mức sai số dấu phẩy động dưới 10⁻¹². Checkpoint, nhãn, ngưỡng và số đặc trưng khớp. |
| Lỗi và fallback | Miền .invalid chuyển sang 17 đặc trưng với lý do; đích loopback trả 422. API tắt khóa hành động. Worker tắt vẫn cho Quick/Snapshot. Với root thiếu checkpoint, API báo 503 và UI hiện thông báo. URL sai, HTML rỗng và tệp UTF-8 lỗi được kiểm qua trình duyệt. |
| Báo cáo và hiệu năng | Điều hướng trong phiên giữ kết quả, đóng góp, URL và phiên bản checkpoint. Bảng Test hiển thị F2 và ma trận nhầm lẫn lấy qua API. |
| Hai môi trường triển khai | Đã thao tác UI native Windows và UI trong Docker Compose có worker cô lập. Cả hai trả Full Scan 34 đặc trưng. |
| Phân phối | Wheel bao gồm CSS và font OFL. Trình duyệt chặn tài nguyên ngoài khi kiểm Quick Scan; các font cần dùng vẫn nạp được từ local. |

`scripts/verify_models.py` đối chiếu SHA-256, thứ tự schema, tham số, 300 cây và fixture cho mỗi model. Primary seed 43, fallback seed 44. Sai số cho phép khi đối chiếu điểm là 10⁻¹². SHA đầy đủ của cả hai checkpoint xuất hiện trong biên bản máy đọc được.

Bộ pytest trên Windows ghi nhận 84 đạt, 5 bỏ qua. Ruff không báo lỗi theo bộ quy tắc CI. Bài AppTest mất API kiểm thông báo ngay khi vào trang và nút gửi bị khóa.

Chạy lại `uv run --no-sync pytest -q`, `python scripts/verify_models.py`, `python scripts/verify_fullscan.py` và, với Playwright/Chromium đã cài, `node scripts/check_ui.cjs`, `node scripts/check_product_modes.cjs`. Hai lệnh trình duyệt dùng dịch vụ local đang chạy.

[Đối chiếu số thực và SHA](evidence/model-parity.json) · [Kiểm lỗi](evidence/fault-states.json) · [Tài nguyên trình duyệt](evidence/local-browser-resources.json).
