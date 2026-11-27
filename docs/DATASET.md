# CompPhish v4

Richa Goenka, CompPhish, Mendeley Data, phiên bản 4, DOI 10.17632/fmbs4kp9wz.4, giấy phép CC BY 4.0. Nhóm PhishShield AI tạo thêm bảng đặc trưng và split từ tài liệu nguồn cho mục đích môn học. [Bản phát hành chính thức](https://data.mendeley.com/datasets/fmbs4kp9wz/4) · [Giấy phép](https://creativecommons.org/licenses/by/4.0/)

data/raw/compphish/ chứa nguyên 8 tệp. Mapping_File.xlsx liên kết serial_number với URL và label. All_HTML.zip chứa All_HTML/<serial_number>.txt. Bảng All_Features_threshold90.xlsx và Data_Dictionary.xlsx dùng để đối chiếu. Hai ZIP mã của tác giả, Readme.docx và requirements.txt được bảo quản nguyên bản.

Notebook 01 lấy danh mục chính thức và đối chiếu danh mục v4 đã ghim. Bản tải dở giữ hậu tố .part, HTTP Range chỉ nối khi máy chủ xác nhận đúng offset. Sau tải kiểm tra kích thước, SHA-256 trước khi công bố tệp hoàn chỉnh. Nếu mạng chặn, tải từng tệp từ bản phát hành trên và đặt đúng tên vào data/raw/compphish/ rồi chạy lại 01. Tệp hoàn chỉnh có hash sai cần được người phụ trách kiểm tra và chuyển riêng trước khi tải lại.

Notebook 02 kiểm tra ZIP theo danh sách đường dẫn, loại symlink, giới hạn kích thước mỗi member và tổng kích thước. Đọc từng snapshot trong runtime, không giải nén hàng nghìn tệp lên Drive. So khớp hai bảng theo ID/URL/label, đếm trùng URL và hash HTML, loại URL mâu thuẫn, URL không hợp lệ và snapshot thiếu/rỗng/không phân tích được. Đối chiếu hàng cụ thể ở data/interim/exclusions.csv. Báo cáo đo thực tế trong reports/dataset/dataset_audit.md và manifests/dataset_manifest.json.
