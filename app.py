from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="반다비 AI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp {
        margin: 0;
        padding: 0;
        background: #e8e2f4;
    }

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    iframe {
        display: block;
        width: 100% !important;
        border: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path(__file__).parent / "bandabi_purple.html"

if not html_path.exists():
    st.error("bandabi_purple.html 파일을 찾을 수 없습니다.")
else:
    html = html_path.read_text(encoding="utf-8")
    components.html(
        html,
        height=3000,
        scrolling=True,
    )
