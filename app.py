"""반다비 AI — HTML prototype shell for Streamlit deploy + future backend API."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="반다비 AI",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _backend_api_url() -> str:
    try:
        value = st.secrets.get("BACKEND_API_URL", None)
        if value not in (None, ""):
            return str(value).rstrip("/")
    except Exception:
        pass
    env_value = os.environ.get("BACKEND_API_URL", "").strip()
    if env_value:
        return env_value.rstrip("/")
    return "http://localhost:8000"


BACKEND_API_URL = _backend_api_url()
HTML_PATH = Path(__file__).resolve().parent / "bandabi_purple.html"

st.markdown(
    """
    <style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { visibility: hidden; height: 0 !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    .stDeployButton { display: none !important; }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        width: 100%;
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if HTML_PATH.exists():
    html = HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("__BACKEND_API_URL__", BACKEND_API_URL)
    components.html(html, height=2400, scrolling=True)
else:
    st.error(
        "HTML 파일을 찾을 수 없습니다. `bandabi_purple.html` 파일을 app.py와 같은 폴더에 넣어주세요."
    )
    st.caption(f"Expected path: {HTML_PATH}")
