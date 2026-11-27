"""Vietnamese field definitions for schema 1.0.0, in inference order."""
FEATURES = """
url_length|int|len(url), ký tự|Độ dài địa chỉ nhập|Không đo số byte
hostname_length|int|len(hostname)|Độ dài phần tên máy|Không phản ánh chủ sở hữu
path_length|int|len(path)|Độ dài đường dẫn gốc|Chưa giải mã phần trăm
subdomain_count|int|Số nhãn dưới registrable domain theo PSL|Mức phân cấp tên miền|IP nhận 0, phụ thuộc PSL đóng gói
dot_count|int|Đếm dấu chấm trên cả URL|Mật độ dấu phân cách|Tính cả path và query
hyphen_count|int|Đếm gạch nối trên cả URL|Cấu trúc tên và đường dẫn|Tên hợp lệ cũng dùng gạch nối
digit_count|int|Tổng ký tự thỏa isdigit|Số ký tự số|Gồm chữ số Unicode
digit_ratio|float|digit_count / url_length|Tỷ trọng chữ số|URL rỗng bị loại trước phép chia
special_count|int|Đếm ký tự không thỏa isalnum|Dấu câu và phân cách|Tính cả ký tự của scheme
query_count|int|Số cặp parse_qsl, giữ giá trị rỗng|Số tham số truy vấn|Khóa lặp được đếm nhiều lần
https|binary|scheme bằng https|Giao thức được khai báo|Không kiểm tra chứng thư
ip_host|binary|ipaddress nhận diện hostname|Địa chỉ IP trực tiếp|IP hợp lệ cũng phục vụ trang nội bộ
keyword_count|int|Tổng count của login, verify, secure, account, password, update, bank, signin trên URL chữ thường|Dấu hiệu từ vựng|Đếm chuỗi con, phụ thuộc ngôn ngữ
entropy|float|−Σ p(c) log₂ p(c), bit/ký tự|Đa dạng phân bố ký tự|Không xét thứ tự
encoded_count|int|Số chuỗi % kèm hai chữ số hex|Mức mã hóa URL|Mã hóa là hợp lệ
punycode|binary|Có nhãn hostname bắt đầu xn--|Dấu hiệu IDN dạng ASCII|Không phát hiện mọi tên gần giống
explicit_port|binary|urlsplit.port có giá trị|Cổng khai báo tường minh|Vẫn đếm khi là cổng mặc định
html_length|int|len(html) sau giải mã|Quy mô snapshot|Không bằng kích thước ZIP
tag_count|int|Số node có tag kiểu str trong cây lxml|Độ phức tạp cây|Gồm node parser tự bổ sung
form_count|int|Số phần tử form|Sự hiện diện biểu mẫu|Không nói rõ mục đích
password_count|int|Số input có type password sau strip/lower|Điểm nhập mật khẩu|Đăng nhập hợp lệ cũng có
hidden_count|int|Số input có type hidden sau strip/lower|Trường ẩn trong biểu mẫu|Không kiểm tra CSS
external_link_ratio|float|Số đích anchor ngoài domain / max(1,số đích HTTP(S) hợp lệ)|Tỷ lệ liên kết ra ngoài|Không có link hợp lệ nhận 0
external_action_count|int|Số form có action HTTP(S) sang domain khác|Điểm gửi biểu mẫu|SSO hợp lệ có thể dùng domain khác
iframe_count|int|Số phần tử iframe|Nội dung nhúng|Không tải frame
script_count|int|Số phần tử script|Mức dùng mã script|Không thực thi mã
external_script_count|int|Số script src HTTP(S) ngoài registrable domain|Phụ thuộc ngoài trang|CDN cũng được đếm
image_count|int|Số phần tử img|Mật độ ảnh|Không tải ảnh
anchor_count|int|Số phần tử a|Mật độ điều hướng|Kể cả anchor thiếu href
empty_action_count|int|Số form thiếu action hoặc trống sau strip|Gửi về cùng tài liệu|Hợp lệ theo HTML
has_title|binary|Có title có văn bản sau strip|Metadata của trang|Không đánh giá nội dung
has_favicon|binary|Có link với token icon trong rel chữ thường|Khai báo biểu tượng|Không kiểm tra tài nguyên tồn tại
suspicious_form_count|int|Số form action khác domain hoặc có password và method GET, mặc định GET|Mẫu gửi dữ liệu đáng xem xét|Hai điều kiện trên một form chỉ đếm một lần
sensitive_input|binary|Có password, passwd, otp, cc-number, creditcard, ssn trong type/name/id/autocomplete|Dấu hiệu nhập dữ liệu nhạy cảm|Heuristic theo chuỗi con
""".strip()

