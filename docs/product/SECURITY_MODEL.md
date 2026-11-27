# Ranh giới an toàn

Cổng trên host chỉ bind loopback. Quick và Snapshot phân tích tĩnh, PSL đóng gói chạy offline, không render HTML người dùng, không chạy JavaScript hay tải tài nguyên con. Thân POST giới hạn 8 MiB + 64 KiB, thời gian nhận 15 giây. Kiểm SHA trên chính bytes sẽ được deserialize. Người vận hành phải tin nguồn mã ứng dụng và bảo vệ quyền ghi workspace. Request body và URL đích không được ghi vào access log mặc định.

Fetcher nghiên cứu có kiểm scheme, port, toàn bộ DNS answers, địa chỉ đặc biệt và redirect; connect vào địa chỉ đã kiểm, giới hạn thời gian, số hop, kích thước, chỉ nhận encoding identity. Gate 7 ngắt đường gọi fetcher khỏi API. Hai biến cờ hoặc một Docker bridge không chứng minh cô lập mạng. Full Scan hiện trả lý do rồi dùng URL-only. Chưa nghiệm thu worker/egress độc lập, audit mạng biên hay khả năng quét website tùy ý. Checkpoint hỏng luôn dẫn tới lỗi hệ thống. [Kiểm thử](../../reports/product/SECURITY_TEST_REPORT.md).
