"""Tab 2 placeholder."""

from __future__ import annotations

import streamlit as st

from modules.safety import get_disclaimer, sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def render_tab_schedule() -> None:
    st.markdown(f'<p class="bandabi-tiny">{s("Personal Schedule AI")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('내 운동 일정 추천')}")
    st.caption(s(get_disclaimer("sports")))
    st.info(s("이 탭은 다음 라운드에서 HTML 시안 기준으로 구현 예정입니다."))
