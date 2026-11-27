# Ranh giới an toàn

Quick Scan và Snapshot Analysis dùng parser tĩnh và PSL đóng gói. API chỉ bind loopback trên host, giới hạn body 8 MiB + 64 KiB và thời gian nhận 15 giây. API kiểm SHA trên chính bytes của checkpoint trước khi deserialize. Người vận hành cần bảo vệ quyền ghi thư mục cài đặt và cấu hình Docker.

Full Scan chuyển việc tải tài liệu sang một container Linux riêng. Trước khi mở dịch vụ, worker cài chính sách nftables trong namespace mạng, bỏ toàn bộ capability, hạ UID xuống 65534 rồi xác minh kết nối tới một socket thử nghiệm trên loopback đã bị chặn. Worker dùng filesystem chỉ đọc và không mount checkpoint. Cấu hình native chỉ xuất cổng điều khiển trên loopback. Cấu hình Docker dùng mạng điều khiển nội bộ.

Chính sách kết nối mới chỉ cho DNS qua resolver của Docker và HTTP(S) đến IPv4 công khai trên cổng chuẩn. Worker kiểm mọi địa chỉ DNS trả về và kiểm lại từng đích chuyển hướng, kết nối trực tiếp tới địa chỉ đã duyệt và xác minh hostname khi dùng TLS. Firewall chặn mạng riêng, link-local, loopback và các subnet gắn trực tiếp. Mỗi lượt có tối đa ba chuyển hướng, 12 giây và 2 MiB HTML tĩnh. Worker chỉ nhận encoding identity, không chạy JavaScript, tải tài nguyên con hay gửi cookie. Tối đa hai lượt tải đồng thời.

Website đích nhận kết nối từ địa chỉ ra Internet của máy triển khai. Giao diện hiển thị kết quả phân tích và lý do chuyển nhánh. Trang phụ thuộc JavaScript có thể chỉ cung cấp HTML khung. Dịch vụ được kiểm trong triển khai local. [Nghiệm thu Full Scan](../../reports/product/FULL_SCAN_ACCEPTANCE.md).
