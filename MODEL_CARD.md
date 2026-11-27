# PhishShield AI · Random Forest 1.0.0

Hai RandomForestClassifier của scikit-learn 1.6.1 thuộc TUNED_V2. Điểm đầu ra là predict_proba của lớp 1 (phishing), chưa hiệu chỉnh xác suất. Ngưỡng thuộc từng run đã chọn trên Validation.

| Vai trò | Cột | Trial / seed | Ngưỡng | F2 Validation | Recall Validation | FPR Validation |
|---|---:|---|---:|---:|---:|---:|
| Primary URL+HTML | 34 | C019 / 43 | 0,20 | 95,972% | 97,772% | 10,229% |
| Fallback URL | 17 | C022 / 44 | 0,15 | 89,778% | 93,129% | 22,504% |

Cả hai dùng 300 cây, max_features=log2, bootstrap=True, min_samples_split=5, class_weight=None, n_jobs=-1. Primary không giới hạn độ sâu, min_samples_leaf=2. Fallback giới hạn độ sâu 10, min_samples_leaf=4. Thứ tự cột, mã băm và tham số ghi trong [manifest](MODEL_MANIFEST.json). Bundle lưu cả vector trung vị Train để giải thích tuần tự.

CompPhish v4 của Richa Goenka, CC BY 4.0, cung cấp URL và snapshot để trích biến. Cohort có 15.327 mẫu chia nhóm theo domain và HTML trùng. Primary trên Test đạt F2 96,102%, Recall 98,422%, Precision 87,821%, FPR 12,029%. Có 17 FN và 147 FP. Fallback chưa có Test riêng. Một corpus, ba seed và một phân bố nguồn giới hạn khả năng suy rộng. Điểm và giải thích phục vụ sàng lọc và giảng dạy. Dùng kết quả để tự động chặn hoặc xác nhận một website an toàn nằm ngoài phạm vi thẩm định. [Dataset và giấy phép](https://data.mendeley.com/datasets/fmbs4kp9wz/4).

Bundle được phân phối nội bộ riêng với mã nguồn. Quyền công bố checkpoint và giấy phép mã nguồn đang chờ trưởng nhóm quyết định.
