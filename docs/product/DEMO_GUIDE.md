# Kịch bản demo 6 phút

| Thời gian | Người trình bày thực hiện |
|---|---|
| 0:00–0:45 | Nêu bài toán phishing và lý do phải xử lý trường hợp chỉ có URL. Giới thiệu ba thành viên và ba mô hình. |
| 0:45–1:30 | Trình bày 144 trial × 3 fold. XGBoost baseline có F2 Validation cao nhất khi xét cả hai pha; quy tắc V2 chọn RF URL+HTML. |
| 1:30–2:20 | Mở terminal đã cài model, chạy .\\start.ps1. Mở UI, nhập example.org trong Quick Scan; chỉ ra 17 cột, ngưỡng 0,15. |
| 2:20–3:20 | Dùng cùng URL, dán snapshot tổng hợp ở User Guide. Nhấn phân tích; kiểm primary 34 cột, ngưỡng 0,20. |
| 3:20–4:15 | Mở Giải thích, chọn một dòng và diễn giải giá trị cùng dấu đóng góp; phân biệt số đó với bằng chứng nhân quả và SHAP nghiên cứu. |
| 4:15–5:10 | Mở Hiệu năng, đọc 17 FN và 147 FP. Chọn Full Scan để minh họa lý do chuyển nhánh khi thu thập chưa được phép. |
| 5:10–6:00 | Mở Swagger /docs, gọi /ready và /model/info. Kết luận phạm vi kiểm thử local, một corpus, điểm chưa calibration và fallback chưa có Test riêng. |

Chuẩn bị dependency và bundle trước buổi bảo vệ. Khi mất Internet dùng Quick/Snapshot; Swagger tương tác mặc định có thể cần tải tài nguyên UI lần đầu, khi ngoại tuyến dùng curl.exe /ready và POST từ Python. Không cần Colab hoặc Drive.
