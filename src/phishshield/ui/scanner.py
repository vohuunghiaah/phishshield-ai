import streamlit as st

from phishshield.ui.api_client import ApiError, request
from phishshield.ui.presentation import heading
from phishshield.ui.report import render


def snapshot_input():
    source = st.radio("Nguồn HTML", ["Dán HTML", "Tải tệp UTF-8"], horizontal=True)
    if source == "Dán HTML":
        return st.text_area("Nội dung HTML", height=125)
    upload = st.file_uploader("Tệp HTML UTF-8 (tối đa 8 MiB)", type=["html", "htm", "txt"])
    if upload is None:
        return ""
    if upload.size > 8 * 1024 * 1024:
        raise ValueError("Tệp HTML vượt quá 8 MiB.")
    try:
        return upload.getvalue().decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Tệp HTML cần được lưu bằng UTF-8.") from exc


def scope(mode):
    detail = {"full": "Worker cô lập sẽ tải tài liệu từ website.", "quick": "Chỉ xử lý địa chỉ bạn nhập.", "snapshot": "Dùng bản HTML do bạn cung cấp."}[mode]
    html = {"full": "Tự thu thập", "quick": "Không sử dụng", "snapshot": "Dán hoặc tải tệp"}[mode]
    with st.container(key="scope"):
        st.header("Dữ liệu sử dụng")
        st.html(f'<dl class="scope-list"><div><dt>URL</dt><dd>Địa chỉ HTTP hoặc HTTPS</dd></div><div><dt>HTML tĩnh</dt><dd>{html}</dd></div></dl>')
        st.caption(detail)


def scanner(live):
    heading("Phân tích website", "Kiểm tra một địa chỉ nghi ngờ và xem những dấu hiệu ảnh hưởng đến kết luận.")
    with st.container(key="workbench"):
        entry, side = st.columns([2.1, 1], gap="large")
        with entry:
            if live is None:
                st.error("API chưa kết nối. Kiểm tra FastAPI rồi tải lại trang.")
            elif not live:
                st.info("Full Scan chưa khả dụng. Bạn có thể dùng Quick Scan hoặc cung cấp HTML.")
            with st.form("submit_url", border=False):
                url = st.text_input("Địa chỉ website", placeholder="https://example.org/")
                submitted = st.form_submit_button("Phân tích", type="primary", disabled=live is None)
            modes = {"Quick Scan": "quick", "Snapshot Analysis (nâng cao)": "snapshot"}
            if live:
                modes = {"Full Scan": "full", **modes}
            mode = modes[st.radio("Chế độ phân tích", list(modes), horizontal=True, key="scan_mode")]
            html, error = None, None
            if mode == "snapshot":
                try:
                    html = snapshot_input()
                except ValueError as exc:
                    error = str(exc)
        with side:
            scope(mode)
    if submitted:
        st.session_state.pop("report", None)
        url = url.strip()
        if not url:
            error = "Nhập địa chỉ website để bắt đầu."
        elif mode == "snapshot" and not error and not (html or "").strip():
            error = "Cung cấp HTML cho Snapshot Analysis."
        if error:
            st.error(error)
        else:
            pending = {"full": "Đang chờ thu thập HTML và suy luận…", "quick": "Đang chờ phân tích đặc trưng URL và suy luận…", "snapshot": "Đang chờ phân tích URL, HTML và suy luận…"}[mode]
            try:
                with st.spinner(pending):
                    payload = {"url": url, "mode": mode}
                    if mode == "snapshot":
                        payload["html"] = html
                    result = request("/predict", payload)
                st.session_state.report = {"result": result, "url": url, "mode": mode}
            except ApiError as exc:
                st.error(str(exc))
    if "report" in st.session_state:
        render(st.session_state.report)
    elif not submitted:
        st.header("Cách đọc kết quả")
        st.html('<dl class="reading"><div><dt>Điểm phishing</dt><dd>Mức nghi ngờ mô hình ghi nhận trên thang 0–1.</dd></div><div><dt>Ngưỡng cảnh báo</dt><dd>Khi điểm bằng hoặc vượt ngưỡng, kết luận có dấu hiệu phishing.</dd></div><div><dt>Dấu hiệu ảnh hưởng</dt><dd>Các đặc trưng làm tăng hoặc giảm điểm trong lần phân tích.</dd></div></dl>')
