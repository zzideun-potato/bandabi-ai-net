"""Tab 4 placeholder — B2G only."""

from __future__ import annotations

import streamlit as st

from components.session_state import ROLE_B2G
from modules.safety import get_disclaimer, sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def render_tab_dashboard() -> None:
    if st.session_state.get("role") != ROLE_B2G:
        st.warning(s("기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다."))
        return

    st.markdown(f'<p class="bandabi-tiny">{s("B2G Dashboard")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('기관용 대시보드')}")
    st.caption(s(get_disclaimer("general")))
    st.info(s("이 탭은 다음 라운드에서 HTML 시안 기준으로 구현 예정입니다."))
