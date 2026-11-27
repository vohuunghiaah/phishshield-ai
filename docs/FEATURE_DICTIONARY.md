# Từ điển đặc trưng 1.0.0

Schema có thứ tự và hash của từng bảng nằm trong manifests/features.json. Các cột đếm là số nguyên. Các indicator nhận 0 hoặc 1. Mọi tỷ lệ dùng dạng thập phân.

| Cột URL | Công thức |
|---|---|
| url_length, hostname_length, path_length | Số ký tự Unicode của nguyên URL, hostname đã tách và path chưa giải mã. |
| subdomain_count | Số nhãn subdomain theo PSL đóng gói. Với IP bằng 0. Domain không có suffix đã biết dùng hostname đầy đủ làm khóa nhóm. |
| dot_count, hyphen_count, digit_count | Đếm dấu chấm, gạch nối, ký tự số trên nguyên URL. |
| digit_ratio, special_count | Số ký tự số chia độ dài URL, và số ký tự không phải chữ hoặc số. |
| query_count | Số cặp query, giữ khóa lặp và giá trị rỗng. |
| https, ip_host, explicit_port | Scheme là HTTPS, hostname là IPv4/IPv6, hoặc URL khai báo port tường minh. HTTPS riêng lẻ không chứng minh website an toàn. |
| keyword_count | Tổng số lần xuất hiện không phân biệt hoa thường của login, verify, secure, account, password, update, bank, signin. |
| entropy | Shannon entropy theo tần suất ký tự, log cơ số 2. |
| encoded_count, punycode | Số chuỗi phần trăm kèm hai chữ số hex, và có nhãn hostname bắt đầu bằng xn--. |

| Cột HTML | Công thức |
|---|---|
| html_length, tag_count | Số ký tự văn bản đã giải mã và số node phần tử trong cây HTML do lxml phục hồi, gồm cả node ngầm định. |
| form_count, iframe_count, script_count, image_count, anchor_count | Đếm phần tử form, iframe, script, img, a. |
| password_count, hidden_count | Số input có type tương ứng password hoặc hidden. |
| external_link_ratio | Số anchor trỏ HTTP(S) ra ngoài domain đăng ký trang chia số anchor có đích HTTP(S) hợp lệ. Bằng 0 khi mẫu số bằng 0. |
| external_action_count, external_script_count | Số form action hoặc script src có đích HTTP(S) ngoài domain trang. |
| empty_action_count | Số form thiếu action hoặc action rỗng sau khi bỏ khoảng trắng. |
| has_title, has_favicon | Có title có chữ, hoặc link có token icon trong thuộc tính rel. |
| suspicious_form_count | Đếm một lần mỗi form gửi ra domain khác hoặc có input mật khẩu và method GET, gồm GET mặc định. |
| sensitive_input | Có input chứa password, passwd, otp, cc-number, creditcard hoặc ssn trong type, name, id hoặc autocomplete. |

URL tương đối phân giải theo URL tài liệu và base href hợp lệ đầu tiên ở vị trí base được phân tích. So sánh domain sau chuẩn hóa IDNA và PSL cùng phiên bản với train. Không tải CSS, script, ảnh hay iframe. Parser có thể phục hồi HTML hỏng cú pháp. UTF-8 có BOM được hỗ trợ, fallback CP1252 có đếm trong audit. Các chỉ báo từ khóa là heuristic. Không có snapshot thì dùng checkpoint URL-only riêng.
