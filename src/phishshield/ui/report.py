import streamlit as st

from phishshield.ui.presentation import number

LABELS = {
    "url_length": "Độ dài URL", "hostname_length": "Độ dài tên máy chủ", "path_length": "Độ dài đường dẫn",
    "subdomain_count": "Số tên miền phụ", "dot_count": "Số dấu chấm", "hyphen_count": "Số dấu gạch nối",
    "digit_count": "Số chữ số", "digit_ratio": "Tỷ lệ chữ số", "special_count": "Số ký tự đặc biệt",
    "query_count": "Số tham số truy vấn", "https": "Sử dụng HTTPS", "ip_host": "Địa chỉ IP làm tên máy chủ",
    "keyword_count": "Số từ khóa trong URL", "entropy": "Độ phân tán ký tự URL", "encoded_count": "Số ký tự mã hóa",
    "punycode": "Tên miền dùng Punycode", "explicit_port": "URL có ghi cổng",
    "html_length": "Độ dài HTML", "tag_count": "Số thẻ HTML", "form_count": "Số biểu mẫu",
    "password_count": "Số ô mật khẩu", "hidden_count": "Số trường ẩn", "external_link_ratio": "Tỷ lệ liên kết ra ngoài",
    "external_action_count": "Số biểu mẫu gửi ra ngoài", "iframe_count": "Số khung nhúng",
    "script_count": "Số thẻ script", "external_script_count": "Số script bên ngoài", "image_count": "Số hình ảnh",
    "anchor_count": "Số thẻ liên kết", "empty_action_count": "Số biểu mẫu thiếu đích gửi",
    "has_title": "Có tiêu đề trang", "has_favicon": "Có biểu tượng website", "suspicious_form_count": "Số biểu mẫu đáng chú ý",
    "sensitive_input": "Có trường nhập nhạy cảm",
}
METHOD = {"fetched": "URL và HTML tự thu thập", "snapshot": "URL và HTML cung cấp", "disabled": "Chỉ URL", "fetch_failed": "Chỉ URL"}
MODE = {"quick": "Quick Scan", "full": "Full Scan", "snapshot": "Snapshot Analysis"}


def signals(result):
    st.header("Dấu hiệu ảnh hưởng")
    st.caption("Đóng góp dương làm tăng điểm, đóng góp âm làm giảm điểm khi lần lượt thay giá trị trung vị của tập Train. Thứ tự thay thế ảnh hưởng đến kết quả.")
    rows = result["explanation"]["contributions"]
    if not rows:
        st.write("Các bước thay thế không làm thay đổi điểm.")
        return
    maximum = max(abs(r["contribution"]) for r in rows) or 1
    lines = []
    for row in rows:
        value, impact = row["value"], row["contribution"]
        direction = "up" if impact > 0 else "down"
        width = 50 * abs(impact) / maximum
        name = LABELS.get(row["feature"], "Đặc trưng khác")
        signed = ("+" if impact > 0 else "") + number(impact)
        lines.append(f'<div class="signal" role="listitem"><span>{name}<small>Giá trị {number(value).rstrip("0").rstrip(",")}</small></span><span class="axis" aria-hidden="true"><b class="{direction}" style="width:{width:.2f}%"></b></span><strong class="{direction}">{signed}</strong></div>')
    st.html('<div class="signals" role="list" aria-label="Đóng góp theo đặc trưng">' + "".join(lines) + "</div>")


def render(report):
    r = report["result"]
    positive = bool(r["prediction"])
    state = "positive" if positive else "negative"
    score, threshold = r["phishing_probability"], r["threshold"]
    with st.container(key="report"):
        st.caption("Kết quả phân tích · " + MODE[report["mode"]])
        verdict = "Có dấu hiệu phishing" if positive else "Chưa phát hiện dấu hiệu vượt ngưỡng"
        st.html(f'<h2 class="verdict {state}">{verdict}</h2>')
        st.text(report["url"])
        if r["fallback_reason"]:
            st.warning(r["fallback_reason"])
        st.html(f'<div class="score"><strong>{number(score)}</strong> điểm phishing &nbsp; / &nbsp; ngưỡng cảnh báo <b>{number(threshold, 2)}</b><div class="track {state}" aria-hidden="true"><b style="width:{100*score:.2f}%"></b><i style="left:{100*threshold:.2f}%"></i></div><div class="scale" aria-hidden="true"><span>0</span><span>1</span></div></div>')
        st.caption("Điểm thể hiện mức nghi ngờ của mô hình. Website dưới ngưỡng vẫn có thể là phishing.")
        method = METHOD[r["html_extraction_status"]]
        timing = " · Thu thập HTML " + number(r["fetch_ms"], 0) + " ms" if "fetch_ms" in r else ""
        st.write(f'{method} · {r["feature_count"]} đặc trưng · Suy luận {number(r["processing_ms"], 0)} ms{timing}')
        signals(r)
        with st.expander("Chi tiết kỹ thuật"):
            st.text(f'{r["model_name"]} · {r["model_phase"]} · {r["feature_modality"]}\nCheckpoint {r["model_version"]} · HTML {r["html_extraction_status"]}')
            st.write(r["explanation"]["method"])
            st.json(r["explanation"]["contributions"], expanded=True)
