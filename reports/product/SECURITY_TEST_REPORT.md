# Kết quả kiểm tra an toàn

Cập nhật 28/11/2026. Trạng thái bên dưới ghi nhận lần nghiệm thu Gate 7 ban đầu. [Kết quả nghiệm thu Full Scan sau khi bổ sung worker cô lập](FULL_SCAN_ACCEPTANCE.md).

**Quick/Snapshot PASS. Thu thập HTML trực tuyến BLOCKED.** Product API không nhập hoặc gọi fetcher mạng. Thiết lập cờ egress cũ không bật được fetch. Full Scan trả thông báo và actual modality URL-only. Unit test kiểm các chế độ không phân giải DNS, các địa chỉ đặc biệt bị từ chối, timeout 408, JSON sai, kích thước vượt giới hạn và schema/checksum lỗi. Test dùng fixture tổng hợp hoặc địa chỉ loopback của ứng dụng.

Parser tĩnh nhận script như dữ liệu. Trình duyệt chỉ nhận kết quả model. Thử thay bytes đã pin trong fixture installer bị từ chối trước khi publish. Access log chỉ ghi endpoint. Compose sử dụng non-root, drop capabilities, bind loopback và mount model read-only. Chưa chứng minh cô lập worker, DNS hoặc tuyến egress triển khai thực tế; kiểm thử chức năng trên localhost không xác minh các điều kiện đó.

Trước công bố, kiểm staged blobs, từ khóa credential, tệp lớn, notebook outputs, host của URL literal trong mã/tài liệu và danh sách file nhạy cảm. Loại ID Drive nội bộ, prediction theo mẫu, checkpoint và log gốc khỏi bản Git. Bản public của T24 chứa bốn số tổng hợp. [Pytest](pytest.xml) · [Hợp đồng an toàn](../../docs/product/SECURITY_MODEL.md).
