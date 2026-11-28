# Đánh giá giao diện trước Gate 8

Đánh giá A độc lập của Impeccable, commit `7978d036f999bdb4a86dd19e88f4a552c459c3a2`. Đánh giá theo nhiệm vụ nhập URL, kiểm tra kết luận và giải thích kết quả. Duyệt bằng Chromium thật, với bản sao nguyên trạng của mã giao diện và cấu hình theme ở commit gốc. Dùng API local và model thật. Các ảnh là viewport ở mức thu phóng 100%. Đây là đánh giá chuyên gia, chưa có người dùng tham gia.

## Điều cần sửa

| Mức | Vị trí và bằng chứng | Vấn đề quan sát được | Tác động và thay đổi đề xuất |
|---|---|---|---|
| P1 | Scanner ở [768 × 1024](../../reports/ui_v2/screenshots/before/scanner-768x1024.png) | Sidebar rộng khoảng 336 px mở đè lên đầu tiêu đề, ô URL và nút phân tích ngay lần vào đầu tiên. | Người dùng phải đóng vùng điều hướng trước khi thực hiện tác vụ chính. Dành chiều ngang cho nội dung và kiểm tra điểm chuyển bố cục ở đúng 768 px. |
| P1 | [Worker không sẵn sàng](../../reports/ui_v2/screenshots/before/worker-unavailable.png) và [API mất kết nối](../../reports/ui_v2/screenshots/before/api-unavailable.png) | Full Scan vẫn chọn được khi worker tắt. Nếu API tắt, giao diện cũng báo worker chưa sẵn sàng trước khi trả lỗi API khi gửi. | Người dùng khó biết việc tải trang có thực hiện hay không. Phân biệt mất API với mất worker, khóa lựa chọn không khả dụng, hiển thị phương pháp thực sự đã chạy. |
| P1 | [Kết quả Quick Scan](../../reports/ui_v2/screenshots/before/report.png), [màn Giải thích](../../reports/ui_v2/screenshots/before/explanation.png) | Bản báo cáo riêng không kèm URL, không hiện tên chế độ người dùng đã chọn. Người đọc phải chuyển trang để xem đóng góp. | Dễ ghép nhầm kết quả với lần quét trước. Giữ URL dạng văn bản, phương pháp, ngưỡng và bằng chứng trong cùng báo cáo. |
| P2 | [Trang chủ](../../reports/ui_v2/screenshots/before/home.png), [Scanner trên desktop](../../reports/ui_v2/screenshots/before/scanner-1440x900.png) | Bảy mục ngang cấp đặt trang khởi đầu, lựa chọn nhập liệu và từng phần của báo cáo cùng một nhóm. Snapshot nằm ở “Phân tích nâng cao”. | Người mới phải đoán nơi nhập HTML. Hợp nhất ba cách nhập trên Scanner và rút điều hướng còn nhóm tác vụ. |
| P2 | [Biểu đồ giải thích](../../reports/ui_v2/screenshots/before/explanation.png) | Hai hướng đóng góp dùng chung màu; nhãn như `subdomain_count` xuất hiện cả trên trục, trong bảng và câu diễn giải. | Người đọc phải dịch tên và lần theo trục để hiểu chiều ảnh hưởng. Dùng tên Việt, dấu +/−, từ chỉ chiều và hai màu, chuyển tên gốc vào chi tiết kỹ thuật. |
| P2 | [Chưa có báo cáo](../../reports/ui_v2/screenshots/before/empty-result.png) và [gửi URL rỗng](../../reports/ui_v2/screenshots/before/empty-submit.png) | Màn báo cáo hướng dẫn bằng chữ nhưng không có hành động; gửi trống trong Scanner thường nhận thông báo đề cập snapshot. | Người dùng phải tự tìm đường quay lại và xác định trường cần sửa. Đặt hành động quay về Scanner, trả lỗi sát trường tương ứng. |
| P2 | [Hiệu năng](../../reports/ui_v2/screenshots/before/metrics.png) | Sáu KPI đều lớn như nhau; nhãn như FPR và F2 đứng riêng trên số liệu. | Người thuyết trình phải giải thích mỗi ký hiệu và tự suy ra báo động nhầm từ ma trận. Ưu tiên F2/recall theo giao thức, bổ sung mẫu số và cách đọc từng sai số. |
| P2 | [Desktop](../../reports/ui_v2/screenshots/before/scanner-1280x800.png) và [390 × 844](../../reports/ui_v2/screenshots/before/scanner-390x844.png) | Heading tiếng Anh xuất hiện trước nội dung tiếng Việt. Trên điện thoại, tên sản phẩm nằm sau sidebar còn nút Deploy của framework luôn thấy. | Khó nhận diện ứng dụng khi trình chiếu từ màn hình hẹp. Giữ wordmark nhỏ, dùng tiêu đề tác vụ bằng tiếng Việt và ưu tiên thao tác quét. |

## Những hành vi nên giữ

Scanner mở mặc định và tự chọn Full Scan theo worker thực. Khi tải được HTML, kết quả trả mô hình 34 đặc trưng. Trang không lấy được HTML chuyển sang 17 đặc trưng và hiển thị lý do. Quick Scan có thể chạy ngoại tuyến. Spinner theo thời gian chờ yêu cầu; nhãn cảnh báo luôn đi cùng màu. [Full Scan](../../reports/ui_v2/screenshots/before/full.png) · [Đang chạy](../../reports/ui_v2/screenshots/before/loading.png) · [Truy xuất thất bại](../../reports/ui_v2/screenshots/before/fetch-failed.png) · [Quick Scan](../../reports/ui_v2/screenshots/before/quick.png).

## Thang điểm nhận định

Thang 0–4 của Impeccable. Điểm nhằm xác định hạng mục cần sửa, chưa phải số đo usability hay chứng nhận accessibility.

| Heuristic | Điểm | Căn cứ |
|---|---:|---|
| Trạng thái hệ thống | 2 | Có spinner, phản hồi lỗi API và worker chưa được tách rõ. |
| Ngôn ngữ thực tế | 2 | Kết luận tiếng Việt, nhưng mục điều hướng lẫn tiếng Anh và tên biến thô. |
| Kiểm soát người dùng | 2 | Chuyển chế độ được, nhưng Full Scan còn chọn được khi worker tắt. |
| Nhất quán | 2 | Dùng cùng widget, nhưng tên phương pháp ở điều hướng và kết quả khác nhau. |
| Ngăn lỗi | 2 | API từ chối URL sai, thông báo nhập rỗng nhắc cả snapshot. |
| Nhận biết thay vì ghi nhớ | 1 | Báo cáo riêng thiếu URL đã gửi. |
| Hiệu quả thao tác | 2 | Quét URL một nút; đường nhập snapshot và xem chi tiết bị chia màn. |
| Tối giản và phân cấp | 2 | Không có số liệu trang trí, sáu KPI đồng cấp và hai màn báo cáo chồng chức năng. |
| Phục hồi sau lỗi | 2 | Nêu lỗi, nhưng thiếu hành động quay lại ở màn báo cáo trống. |
| Trợ giúp | 2 | Có [giới thiệu](../../reports/ui_v2/screenshots/before/about.png), thiếu ngữ cảnh thuật ngữ ngay nơi đọc kết quả. |

Tổng 19/40. Với sinh viên lần đầu thử URL, trở ngại đầu tiên là lựa chọn chế độ và điều hướng. Với giảng viên cần đối chiếu dữ liệu, trở ngại chính là thiếu liên kết giữa URL, phương pháp và đóng góp. Với người dùng tablet, lớp điều hướng có thể che tác vụ chính.

## Phạm vi tái hiện

Bốn ảnh Scanner giữ nguyên viewport. Các ảnh trạng thái còn lại dùng 1440 × 900. Kiểm tra Full Scan trên `example.org`, lỗi truy xuất trên tên miền thử nghiệm `.invalid`, Snapshot trên HTML tự tạo minh bạch và lỗi URL trên đầu vào thiếu scheme. API mất kết nối dùng một giao diện trỏ tới cổng local không có backend; tình huống worker tắt dùng một backend local riêng có `full_scan=false`. [Ảnh Snapshot](../../reports/ui_v2/screenshots/before/snapshot.png) · [URL không hợp lệ](../../reports/ui_v2/screenshots/before/invalid.png).

Nguồn phương pháp. [Impeccable, rubric tại phiên bản được dùng](https://github.com/pbakaus/impeccable/blob/2fc5e1459efbbf06d92c7306517c286bf12490cf/.agents/skills/impeccable/reference/critique-rubric.md).
