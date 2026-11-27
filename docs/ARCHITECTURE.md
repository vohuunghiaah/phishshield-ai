# Kiến trúc

| Vị trí | Sản phẩm và vòng đời |
|---|---|
| notebooks/ | 13 điểm vào Colab từ 00 đến 12. Mỗi notebook mount, xác minh và chuẩn bị runtime riêng. |
| src/phishshield/ | data kiểm định và chia mẫu, features trích xuất dùng chung, models và training huấn luyện, evaluation chọn model, explainability tính SHAP, inference nạp bundle, api và ui phục vụ demo, utils quản lý lưu trữ. |
| configs/ | Đường dẫn, danh mục nguồn v4, giới hạn dữ liệu, schema, seed, tham số mô hình và chính sách mạng. |
| data/raw/compphish/ | Tệp chính thức nguyên vẹn. |
| data/interim/, data/processed/ | Danh sách loại và cohort gắn ID, nhãn, domain, hash snapshot. |
| data/features/, data/splits/ | Hai bảng đặc trưng và khóa split. |
| experiments/ | Riêng từng thành viên, modality và seed. Gồm config, metrics, trạng thái cùng lịch sử MLP. |
| checkpoints/ | Bundle theo thuật toán, modality, seed và lần chạy. selected_model lưu selection và bundle triển khai. Chỉ nạp joblib được tạo bởi nhóm, trong folder tin cậy. |
| results/ | metrics cho holdout, predictions theo ID, comparisons theo seed/nhóm, explanations và figures. |
| reports/ | setup cho nghiệm thu, dataset cho audit, eda cho thống kê, experiments và final cho báo cáo môn học. |
| scripts/, tests/, docs/ | CLI, kiểm thử và hướng dẫn. |
| manifests/, logs/ | Danh mục kèm hash, schema và nơi lưu nhật ký vận hành. |
| /content/phishshield-ai-run | Bản sao mã nguồn, môi trường Python, ZIP staged và tệp tạm của phiên. Có thể mất khi ngắt kết nối. |

FastAPI và Streamlit chạy trong môi trường tin cậy với cùng quyền truy cập artifact. UI gọi backend qua HTTP. Demo dùng TestClient và AppTest, không cần mở cổng công khai. Để chạy độc lập, đặt PHISHSHIELD_DRIVE_ROOT tới workspace đã kiểm tra, chạy uvicorn phishshield.api.app:app --host 127.0.0.1, rồi streamlit run src/phishshield/ui/app.py --server.address 127.0.0.1. Backend mặc định của UI là http://127.0.0.1:8000.

Live fetch tắt trong cấu hình. Khi có hạ tầng egress cô lập chặn đường tới mạng riêng/metadata ở tầng mạng, quản trị viên có thể bật live_fetch và đặt PHISHSHIELD_ISOLATED_EGRESS=1. Bộ tải giới hạn HTTP(S) cổng chuẩn, kiểm tra toàn bộ câu trả lời DNS và từng redirect, nối thẳng IP đã duyệt, kiểm chứng TLS theo hostname, giới hạn timeout, MIME và số byte. Chỉ đọc một tài liệu tĩnh. Trong Colab giữ nguyên mặc định. URL ngoài dataset do người dùng nhập có thể được phân tích từ snapshot qua /predict-from-html trên loopback.
