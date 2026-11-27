# Nghiệm thu từ bản clone sạch

**PASS.** Tạo clone mới tại C:\dev\phishshield-ai-verify bằng GitHub HTTPS, nhánh main, commit sản phẩm 6853f39b95df9558be4277f23e188091a587335e. Cài dependency bằng setup.ps1 và uv.lock vào .venv mới. ZIP nội bộ được sao ra thư mục tạm độc lập trước khi cài. verify_models.py đọc hai checkpoint trong clone mới và tái lập hai fixture chính thức.

Trong lúc chạy, 12 tiến trình Python đã nạp audit hook thử nghiệm. Hook từ chối mở tệp trên G: và dưới cây phát triển C:\dev\phishshield-ai, đồng thời từ chối outbound socket/DNS ngoài loopback. Biến môi trường Drive cũ trỏ vào vị trí bị chặn. Đây là phép kiểm độc lập đường dẫn cho Python của ứng dụng ở local. Phép kiểm này không thẩm định egress cho live fetching.

| Lần khởi động | API ready (s) | UI ready (s) | Hai phản hồi thực |
|---:|---:|---:|---|
| 1 | 10,35 | 17,93 | 17 cột / 0,15 và 34 cột / 0,20 |
| 2 | 7,54 | 8,65 | 17 cột / 0,15 và 34 cột / 0,20 |
| 3 | 7,87 | 9,10 | 17 cột / 0,15 và 34 cột / 0,20 |

Dùng start.ps1, /ready, Streamlit health, hai lần POST và stop.ps1 mỗi chu kỳ. Lần đầu còn chạy Chromium trên UI để nhập liệu, xem giải thích, metric và bố cục hẹp. Cả ba launcher thoát thành công. [Biên bản máy đọc](clean_run.json).
