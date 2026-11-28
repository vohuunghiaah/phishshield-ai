"""Streamlit entry point for the local analysis workspace."""
import streamlit as st

from phishshield.ui.api_client import BASE, capabilities
from phishshield.ui.presentation import ROOT, brand, heading, status, stylesheet
from phishshield.ui.reference import guide, performance
from phishshield.ui.report import render
from phishshield.ui.scanner import scanner

st.set_page_config(page_title="PhishShield AI", page_icon=ROOT / "assets/mark.svg", layout="wide")
st.html(stylesheet())
live = capabilities(BASE)


def scan_page():
    scanner(live)


def report_page():
    if "report" in st.session_state:
        st.title("Báo cáo phân tích")
        render(st.session_state.report)
    else:
        heading("Báo cáo phân tích", "Chưa có kết quả trong phiên này. Phân tích một địa chỉ để xem điểm, ngưỡng và các dấu hiệu ảnh hưởng.")
        st.page_link(scan, label="Mở công cụ phân tích", icon=":material/arrow_forward:")


scan = st.Page(scan_page, title="Phân tích website", default=True)
navigation = [
    (scan, "Phân tích website", "search"),
    (st.Page(report_page, title="Báo cáo phân tích", url_path="bao-cao"), "Báo cáo phân tích", "description"),
    (st.Page(performance, title="Hiệu năng mô hình", url_path="hieu-nang"), "Hiệu năng mô hình", "table_chart"),
    (st.Page(guide, title="Giới thiệu và hướng dẫn", url_path="huong-dan"), "Hướng dẫn", "menu_book"),
]
page = st.navigation([entry[0] for entry in navigation], position="hidden")
with st.container(key="masthead"):
    left, right = st.columns([1.4, 1])
    with left:
        brand()
    with right:
        status(live)
with st.container(key="navigation"):
    for destination, label, icon in navigation:
        st.page_link(destination, label=label, icon=f":material/{icon}:")
page.run()
