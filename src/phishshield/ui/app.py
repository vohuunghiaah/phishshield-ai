import os

import httpx
import pandas as pd
import streamlit as st

API = os.environ.get("PHISHSHIELD_API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="PhishShield AI", page_icon="🛡️", layout="centered")
st.sidebar.title("🛡️ PhishShield AI")
screen = st.sidebar.radio("Điều hướng", ["Trang chủ","Website Scanner","Phân tích nâng cao","Kết quả","Giải thích","Hiệu năng","Giới thiệu"],index=1,key="screen")
st.sidebar.caption("Phát hiện phishing từ URL và HTML tĩnh")


def call(method, path, payload=None):
    try:
        response = httpx.request(method,API+path,json=payload,timeout=25)
        if response.is_success:
            return response.json()
        st.error(response.json().get("detail","API chưa thể xử lý yêu cầu."))
    except (httpx.HTTPError, ValueError):
        st.error("Không kết nối được API. Kiểm tra tiến trình FastAPI trên máy chủ.")
    return None


def result(r):
    positive = bool(r["prediction"])
    st.subheader("Có dấu hiệu phishing" if positive else "Dưới ngưỡng cảnh báo")
    if positive:
        st.warning("Website có dấu hiệu phishing theo mô hình. Hãy thận trọng và tránh cung cấp thông tin nhạy cảm.")
    else:
        st.info("Mô hình chưa phát hiện dấu hiệu phishing vượt ngưỡng đã cấu hình. Kết quả không bảo đảm website hoàn toàn an toàn.")
    first,second = st.columns(2)
    first.metric("Điểm phishing",f"{r['phishing_probability']:.3f}")
    second.metric("Ngưỡng Validation",f"{r['threshold']:.2f}")
    role="Primary" if r["feature_modality"]=="url_html" else "Fallback"
    if r.get("fallback_reason"):
        st.info(r["fallback_reason"])
    st.caption(f"{role} · {r['model_name']} · {r['feature_modality']} · {r['feature_count']} đặc trưng · {r['model_phase']}")
    st.caption(f"Phiên bản {r['model_version']} · HTML: {r['html_extraction_status']} · Xử lý {r['processing_ms']:.1f} ms")


def explanation(r):
    st.subheader("Các yếu tố đóng góp")
    st.write(r["explanation"]["method"]+". Giá trị dương làm tăng điểm theo thứ tự thay thế đã định.")
    rows=r["explanation"]["contributions"]
    if rows:
        frame=pd.DataFrame(rows).rename(columns={"feature":"Đặc trưng","value":"Giá trị","contribution":"Đóng góp"})
        st.bar_chart(frame.set_index("Đặc trưng")["Đóng góp"],horizontal=True,color="#16756c")
        st.dataframe(frame,hide_index=True,use_container_width=True)
        top=rows[0]
        action="tăng" if top["contribution"]>0 else "giảm"
        st.write(f"Với giá trị {top['value']:.3g}, {top['feature']} làm {action} điểm {abs(top['contribution']):.3f} trong phép thay biến này.")
    else:
        st.caption("Không có thay đổi điểm ở các bước thay thế.")
    st.caption("Đóng góp cục bộ phụ thuộc thứ tự. SHAP là phân tích riêng trên tập Validation.")


if screen == "Trang chủ":
    st.title("🛡️ PhishShield AI")
    st.button("Bắt đầu phân tích",on_click=lambda: st.session_state.update(screen="Website Scanner"))
    st.write("Kiểm tra một địa chỉ bằng mô hình đã huấn luyện trên CompPhish v4. Chọn Website Scanner cho URL, hoặc Phân tích nâng cao nếu đã có snapshot HTML.")
elif screen in ("Website Scanner","Phân tích nâng cao"):
    st.title(screen)
    advanced=screen=="Phân tích nâng cao"
    st.write("Phân tích snapshot HTML cùng URL gốc." if advanced else "Phân tích đặc trưng URL bằng mô hình URL-only. Chế độ mặc định xử lý ngoại tuyến.")
    mode="snapshot" if advanced else st.radio("Chế độ",["Quick Scan","Full Scan"],horizontal=True)
    if mode=="Full Scan":
        st.info("Thu thập HTML trực tuyến chưa được bật. Khi phân tích, ứng dụng chuyển sang Quick Scan và ghi rõ lý do.")
    url=st.text_input("URL cần kiểm tra",placeholder="https://example.org/")
    html=None
    if advanced:
        source=st.radio("Nguồn HTML",["Dán HTML","Tải tệp UTF-8"],horizontal=True)
        if source=="Dán HTML":
            html=st.text_area("HTML snapshot",height=150)
        else:
            upload=st.file_uploader("Snapshot HTML tối đa 8 MiB",type=["html","htm","txt"])
            if upload:
                if upload.size>8388608:
                    st.error("Snapshot quá lớn.")
                else:
                    try:
                        html=upload.getvalue().decode("utf-8-sig")
                    except UnicodeError:
                        st.error("Tệp cần dùng UTF-8.")
    if st.button("Phân tích website",type="primary"):
        st.session_state.pop("prediction",None)
        if not url.strip() or (advanced and not (html or "").strip()):
            st.error("Nhập URL và cung cấp snapshot khi dùng phân tích nâng cao.")
        else:
            with st.spinner("Đang phân tích…"):
                r=call("POST","/predict",{"url":url,"mode":"snapshot" if advanced else ("full" if mode=="Full Scan" else "quick"),**({"html":html} if advanced else {})})
            if r:
                st.session_state.prediction=r
                result(r)
                explanation(r)
elif screen in ("Kết quả","Giải thích"):
    st.title(screen)
    if "prediction" not in st.session_state:
        st.info("Chạy Website Scanner hoặc Phân tích nâng cao để xem kết quả.")
    elif screen=="Kết quả":
        result(st.session_state.prediction)
    else:
        explanation(st.session_state.prediction)
elif screen=="Hiệu năng":
    st.title("Hiệu năng trên tập Test")
    record=call("GET","/performance")
    if record:
        m=record["metrics"]
        st.write("Random Forest URL+HTML · checkpoint chính đã khóa")
        for group in [("f2","recall","fpr"),("accuracy","precision","roc_auc")]:
            for c,k in zip(st.columns(3),group):
                c.metric(k.upper(),f"{m[k]:.3%}")
        st.caption("CompPhish v4 · 2.299 mẫu Test. Hiệu năng trên website mới phụ thuộc phân bố đầu vào.")
        st.dataframe(pd.DataFrame(m["confusion_matrix"],index=["Thật · Legitimate","Thật · Phishing"],columns=["Dự đoán legitimate","Dự đoán phishing"]),use_container_width=True)
        st.caption("Fallback URL-only chưa có đánh giá Test riêng.")
else:
    st.title("Giới thiệu")
    st.write("Đồ án Machine Learning so sánh Random Forest, XGBoost và MLP trên URL và HTML tĩnh của CompPhish v4. Các tập dữ liệu được tách theo domain và nội dung HTML trùng khớp.")
    st.write("Điểm mô hình phụ thuộc dữ liệu huấn luyện. Trang thay đổi theo thời gian, chiến dịch mới và nội dung tạo bởi JavaScript có thể gây sai số.")


    st.write("V2 chọn mô hình theo F2 Validation trung bình rồi chọn checkpoint trong nhóm thắng.")
    st.write("Gịp Xương Thanh Quyền · Random Forest. Vũ Thị Tuyết Trang · XGBoost. Võ Hữu Nghĩa · MLP và trưởng nhóm.")
    st.link_button("GitHub · mã nguồn", "https://github.com/vohuunghiaah/phishshield-ai")
