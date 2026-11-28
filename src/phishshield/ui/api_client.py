"""Read-only service metadata and prediction requests from the local UI."""
import os

import httpx
import streamlit as st

BASE = os.environ.get("PHISHSHIELD_API_URL", "http://127.0.0.1:8000").rstrip("/")


class ApiError(Exception):
    """A message suitable for display in the workspace."""


def request(path, payload=None, *, timeout=25):
    try:
        with httpx.Client(base_url=BASE, timeout=timeout, trust_env=False) as client:
            response = client.get(path) if payload is None else client.post(path, json=payload)
            value = response.json()
            if response.is_success:
                return value
            raise ApiError(value.get("detail") or "API chưa thể xử lý yêu cầu.")
    except (httpx.HTTPError, ValueError) as exc:
        raise ApiError("Không kết nối được API. Kiểm tra FastAPI rồi thử lại.") from exc


@st.cache_data(ttl=3, show_spinner=False)
def capabilities(base):
    # Include the configured endpoint in the cache key.
    try:
        return request("/capabilities", timeout=3)["full_scan"]
    except (ApiError, KeyError):
        return None
