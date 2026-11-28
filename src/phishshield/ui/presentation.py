"""Shared presentation for the analyst workspace."""
from base64 import b64encode
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent


@st.cache_data(show_spinner=False)
def font_faces():
    fonts = []
    for weight, name in [(400, "Regular"), (600, "SemiBold")]:
        data = b64encode((ROOT / "assets" / f"BeVietnamPro-{name}.ttf").read_bytes()).decode()
        fonts.append(f"@font-face{{font-family:Be Vietnam Pro;src:url(data:font/ttf;base64,{data});font-weight:{weight};font-display:swap}}")
    return "".join(fonts)


def stylesheet():
    return "<style>" + font_faces() + (ROOT / "styles/tokens.css").read_text("utf8") + (ROOT / "styles/app.css").read_text("utf8") + "</style>"


def number(value, places=3):
    return f"{value:.{places}f}".replace(".", ",")


def heading(title, description):
    st.title(title)
    st.write(description)


def brand():
    image = b64encode((ROOT / "assets/mark.svg").read_bytes()).decode()
    st.html(f'<div class="brand"><img src="data:image/svg+xml;base64,{image}" width="30" height="34" alt=""><span>PhishShield AI</span></div>')


def status(live):
    label = {True: "Thu thập HTML sẵn sàng", False: "Thu thập HTML chưa sẵn sàng", None: "API chưa kết nối"}[live]
    state = "online" if live else "unavailable"
    st.html(f'<div class="availability {state}"><i aria-hidden="true"></i>{label}</div>')
