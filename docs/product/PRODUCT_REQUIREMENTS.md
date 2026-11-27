# Yêu cầu sản phẩm 1.0.0

Đối tượng sử dụng là thành viên nhóm, giảng viên và người kiểm tra URL cục bộ. Từ một URL, người dùng nhận nhãn dựa trên ngưỡng, điểm và giải thích. Snapshot bổ sung 17 biến HTML. Tiêu chí nghiệm thu là cả hai tuyến chạy được khi Drive và Internet không khả dụng sau khi cài model, JSON khớp offline, lỗi bundle hiện rõ và trình duyệt hiển thị đúng phiên bản.

Giới hạn 8 MiB cho HTML, HTTP(S) cho URL và 15 giây để nhận body. Full Scan dùng worker Docker đã qua kiểm tra cô lập để tải tối đa 2 MiB HTML tĩnh trong 12 giây. HTML hợp lệ dùng model 34 biến. [Nghiệm thu Full Scan](../../reports/product/FULL_SCAN_ACCEPTANCE.md). Tỷ lệ lỗi của mô hình áp dụng cho corpus đã đánh giá. [Ma trận nghiệm thu](../../reports/product/GATE7_ACCEPTANCE_REPORT.md).
