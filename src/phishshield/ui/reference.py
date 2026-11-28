import streamlit as st

from phishshield.ui.api_client import ApiError, request
from phishshield.ui.presentation import heading, number


def performance():
    heading("Hiệu năng mô hình", "Kết quả trên tập Test đã khóa của CompPhish v4, dành cho mô hình chính dùng URL và HTML.")
    try:
        m = request("/performance")["metrics"]
        info = request("/model/info")["primary"]
    except ApiError as exc:
        st.error(str(exc))
        return
    matrix = m["confusion_matrix"]
    tn, fp = matrix[0]
    fn, tp = matrix[1]
    st.header("Kết quả trên tập Test")
    cols = st.columns([1.2, 1], gap="large")
    metrics = [("F2", "f2"), ("Recall", "recall"), ("Precision", "precision"), ("Tỷ lệ cảnh báo nhầm (FPR)", "fpr"), ("Accuracy", "accuracy"), ("ROC-AUC", "roc_auc")]
    with cols[0]:
        rows = "".join(f'<tr><th scope="row">{label}</th><td>{number(100*m[field], 3)}%</td></tr>' for label, field in metrics)
        st.html(f'<table class="report-table" aria-label="Chỉ số Test"><thead><tr><th>Chỉ số</th><th>Giá trị</th></tr></thead><tbody>{rows}</tbody></table>')
    with cols[1]:
        st.html(f'<table class="report-table" aria-label="Ma trận nhầm lẫn"><thead><tr><th>Nhãn thật</th><th>Dự đoán hợp lệ</th><th>Dự đoán phishing</th></tr></thead><tbody><tr><th scope="row">Hợp lệ</th><td>{tn}</td><td>{fp}</td></tr><tr><th scope="row">Phishing</th><td>{fn}</td><td>{tp}</td></tr></tbody></table>')
        st.write(f"Trong {tn + fp + fn + tp:,} mẫu Test, mô hình bỏ sót {fn} mẫu phishing và cảnh báo nhầm {fp} mẫu hợp lệ.".replace(",", ".", 1))
    st.header("Phạm vi áp dụng")
    st.write(f'Random Forest · {info["feature_count"]} đặc trưng · seed {info["seed"]} · ngưỡng {number(info["threshold"], 2)}.')
    st.caption("Mô hình chỉ dùng URL chưa được đánh giá riêng trên tập Test. Hiệu năng thực tế phụ thuộc vào loại website và thời điểm thu thập.")


def guide():
    heading("Giới thiệu và hướng dẫn", "PhishShield AI phân tích địa chỉ website và nội dung HTML tĩnh bằng Random Forest.")
    st.header("Chọn phương pháp phân tích")
    st.html('<dl class="reading"><div><dt>Full Scan</dt><dd>Nhập URL để worker cô lập tải HTML tĩnh. Khi nhận được HTML, mô hình dùng 34 đặc trưng.</dd></div><div><dt>Quick Scan</dt><dd>Phân tích 17 đặc trưng của URL ngay cả khi không thể kết nối đến website.</dd></div><div><dt>Snapshot Analysis</dt><dd>Chọn tùy chọn nâng cao để phân tích URL cùng HTML đã lưu bằng mô hình 34 đặc trưng.</dd></div></dl>')
    st.header("Giới hạn")
    st.write("Điểm mô hình chưa được hiệu chỉnh thành xác suất. Trang phụ thuộc JavaScript có thể chỉ trả về HTML khung. Khi website không cung cấp HTML phù hợp, báo cáo Full Scan ghi lý do chuyển sang phân tích URL.")
    with st.expander("Nghiên cứu và nhóm thực hiện"):
        st.write("Nghiên cứu so sánh Random Forest, XGBoost và MLP trên CompPhish v4. Nhóm tách các tập theo domain và snapshot trùng, sau đó chọn mô hình theo F2 trên tập Validation.")
        st.write("Gịp Xương Thanh Quyền phụ trách Random Forest. Vũ Thị Tuyết Trang phụ trách XGBoost. Võ Hữu Nghĩa phụ trách MLP và là trưởng nhóm.")
        st.link_button("Mã nguồn trên GitHub", "https://github.com/vohuunghiaah/phishshield-ai")
