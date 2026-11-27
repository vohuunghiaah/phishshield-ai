# Làm việc nhóm trên Drive và Colab

1. Mỗi thành viên mở folder chung bằng tài khoản riêng được cấp Editor. Kiểm tra ID PHISHSHIELD_DRIVE_FOLDER_ID trong URL. Nếu cần, dùng Organize → Add shortcut trong My Drive.
2. Mở notebooks/00_setup_environment.ipynb → Open with Google Colaboratory → Run all. Cho phép mount. Đường dẫn mặc định là `/content/drive/MyDrive/phishshield-ai`. Nếu shortcut của thành viên nằm ở vị trí khác, sửa ô `candidate` theo đường dẫn trong Files. Khi cần, chấp thuận Drive API để xác minh folder bằng tệp thử. Mount path có thể khác giữa các tài khoản.
3. Thiết lập Gate 1 bằng 00 trên CPU. Đối với cohort hiện tại đã qua audit, đi thẳng tới Gate 2.2. Các notebook 01–06 dùng khi dựng workspace dữ liệu ban đầu.
4. Thành viên 1 chạy 07a → 07 trên CPU. Thành viên 2 chạy 08a → 08 trên CPU. Thành viên 3 mở runtime GPU rồi chạy 09a → 09. Từng người kiểm tra Hardware Check và bật cờ thực thi riêng ở ô cuối. Hướng dẫn có liên kết trực tiếp đến từng notebook.
5. Sau mỗi modality, kiểm tra tuning_lock.json. 07–09 tự nạp cấu hình đã khóa và chạy ba seed. Baseline V1 được lưu theo registry. Kết quả mới nằm ở results/tuning_v2, results/tuned_v2 và checkpoints/tuned_v2.
6. Khi Colab ngắt, kiểm tra manifest và chủ phiên trước khi khôi phục writer. Mỗi model/modality tuning hoặc mỗi seed training chỉ có một phiên ghi. [Quy trình khôi phục, kiểm tra hash và nghiệm thu](HYPERPARAMETER_TUNING_GUIDE.md)
7. Điều phối viên chạy notebook 10 ở chế độ report mặc định. Khi đủ 18 run V2 mới bật chọn mô hình. Việc chấm Test có cờ và phê duyệt riêng. Tiếp tục 11 → 12 sau khi khóa mô hình.
8. Git hiện ở local. Xem trước danh sách với python scripts/sync_github.py. Khi chủ động lưu phiên bản local, chạy python scripts/sync_github.py --commit "Initial PhishShield workspace". Có thể chỉ định --repo /content/<checkout> để sao chép danh sách cho phép vào checkout tạm đã dùng git init -b main. Dùng gh auth login từ terminal cá nhân khi sau này cần remote private và xác nhận tài khoản đích. Không dán token vào notebook hoặc Drive. Không push khi train.

## Môi trường CUDA

Trong 09a và 09, chọn GPU ở Runtime → Change runtime type. Mặc định DEVICE="cuda". Chạy bootstrap sau khi xác minh Drive. Ô này tạo hoặc cập nhật /content/phishshield-ai-run/.venv-cuda-mlp, đồng bộ project bằng Python 3.11, rồi cài torch 2.8.0+cu128. Khi đổi VM cần chạy lại bootstrap và Hardware Check. RF và XGBoost Gate V2 dùng CPU. Kiểm tra trường actual_device trong manifest.

[Hướng dẫn chạy từng thành viên và điều kiện nghiệm thu](HYPERPARAMETER_TUNING_GUIDE.md)
