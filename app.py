"""Kimpo Bandabi AI — native Streamlit UI (HTML purple design reference)."""

from __future__ import annotations

import streamlit as st

from components.app_shell import render_header, render_tab_content, render_tab_nav, render_toast
from components.session_state import init_session_state
from components.theme import inject_purple_theme
from modules.safety import SERVICE_DISCLAIMER, sanitize_public_claims
from modules.ui_components import inject_global_styles, render_disclaimer_box
from views.auth_flow import ensure_authenticated


st.set_page_config(
    page_title="반다비 AI",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


init_session_state()
inject_global_styles()
inject_purple_theme(high_contrast=bool(st.session_state.get("high_contrast")))

if not ensure_authenticated():
    st.stop()

render_header()
render_disclaimer_box(s(SERVICE_DISCLAIMER))
render_toast()
render_tab_nav()
render_tab_content()
