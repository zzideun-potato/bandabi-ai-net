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

    st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
    st.markdown(f'<p class="bandabi-tiny">{s("B2G Dashboard")}</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="bandabi-hero-title" style="font-size:1.75rem;">{s("기관용 대시보드")}</div>')
    st.markdown(
        f'<p class="bandabi-mid" style="font-size:13px;margin-top:8px;">{s(get_disclaimer("general"))}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="bandabi-soft" style="margin-top:16px;text-align:center;padding:28px;">'
        f'<i class="fa-solid fa-chart-pie" style="font-size:2rem;color:var(--mid);" aria-hidden="true"></i>'
        f'<p style="font-weight:800;margin-top:12px;">{s("이 탭은 다음 라운드에서 HTML 시안 기준으로 구현 예정입니다.")}</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
