"""Header, tab navigation, and shell controls."""

from __future__ import annotations

import html

import streamlit as st

from components.html_assets import brand_logo_markup
from components.session_state import (
    ROLE_B2G,
    ROLE_B2C,
    TAB_DASHBOARD,
    TAB_MAIN,
    TAB_SCHEDULE,
    TAB_VISION,
    reset_auth,
)
from modules.safety import sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def _esc(value: object) -> str:
    return html.escape(str(value))


TABS = [
    (TAB_MAIN, "AI 추천 및 이동지원 연계", "fa-brain"),
    (TAB_SCHEDULE, "내 운동 일정 추천", "fa-calendar-check"),
    (TAB_VISION, "AI 기반 접근성 점검 보조", "fa-eye"),
    (TAB_DASHBOARD, "기관용 대시보드", "fa-chart-pie"),
]


def render_toast() -> None:
    message = st.session_state.get("toast_message") or ""
    if not message:
        return
    st.markdown(
        f'<div class="bandabi-toast" role="status" aria-live="polite">{_esc(s(message))}</div>',
        unsafe_allow_html=True,
    )
    st.session_state.toast_message = ""


def render_header() -> None:
    role = st.session_state.get("role")
    name = st.session_state.get("user_name") or "000"
    if role == ROLE_B2C:
        role_badge = s("이용자 모드")
        role_title = s(f"(User | {name}님)")
    elif role == ROLE_B2G:
        role_badge = s("기관 관리자")
        role_title = s("(Admin)")
    else:
        role_badge = s("세션 대기")
        role_title = s("세션 대기")

    bt_html = ""
    if role == ROLE_B2C:
        balance = int(st.session_state.get("bt_balance", 0))
        bt_html = (
            f'<span class="bandabi-badge warn">'
            f'<i class="fa-solid fa-coins" aria-hidden="true"></i> '
            f'{_esc(f"{balance:,}")} BT · '
            f'<span style="font-size:10px;font-weight:600;">{s("현금 환급·양도 불가")}</span></span>'
        )

    st.markdown(
        f"""
        <div class="bandabi-app-header">
          <div class="bandabi-header-row">
            <div class="bandabi-brand">
              {brand_logo_markup(size=48)}
              <div>
                <div class="bandabi-brand-title">
                  반다비 AI <span class="bandabi-brand-sub">{_esc(role_title)}</span>
                </div>
                <div style="margin-top:6px;">
                  <span class="bandabi-badge accent">{_esc(role_badge)}</span>
                  {bt_html}
                </div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="bandabi-toolbar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1])
    with c1:
        if st.button(s("◐ 고대비"), key="btn_high_contrast", use_container_width=True):
            st.session_state.high_contrast = not st.session_state.high_contrast
            st.rerun()
    with c2:
        if st.button(s("🎤 음성"), key="btn_voice_demo", use_container_width=True):
            st.session_state.toast_message = s(
                "음성 데모: 접근성 지원 유형을 음성 안내로 전환한 뒤 분석을 시작할 수 있습니다."
            )
            st.rerun()
    with c3:
        if st.button(s("🏠 홈"), key="btn_home", use_container_width=True):
            st.session_state.active_tab = TAB_MAIN
            st.session_state.main_step = "start"
            st.session_state.toast_message = s(f"안녕하세요, {name}님! 메인 시작 화면으로 이동했습니다.")
            st.rerun()
    with c4:
        if st.button(s("⏻"), key="btn_logout", use_container_width=True):
            reset_auth()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_tab_nav() -> None:
    role = st.session_state.get("role")
    visible_tabs = [t for t in TABS if not (t[0] == TAB_DASHBOARD and role == ROLE_B2C)]
    st.markdown('<div class="bandabi-tab-shell">', unsafe_allow_html=True)
    cols = st.columns(len(visible_tabs))
    for col, (tab_id, label, _icon) in zip(cols, visible_tabs):
        active = st.session_state.active_tab == tab_id
        with col:
            if st.button(
                s(label),
                key=f"tab_{tab_id}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                if tab_id == TAB_DASHBOARD and role != ROLE_B2G:
                    st.session_state.toast_message = s("기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다.")
                else:
                    st.session_state.active_tab = tab_id
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_tab_content() -> None:
    from views.tab_dashboard import render_tab_dashboard
    from views.tab_main_journey import render_tab_main
    from views.tab_schedule import render_tab_schedule
    from views.tab_vision import render_tab_vision

    tab = st.session_state.active_tab
    if tab == TAB_MAIN:
        render_tab_main()
    elif tab == TAB_SCHEDULE:
        render_tab_schedule()
    elif tab == TAB_VISION:
        render_tab_vision()
    elif tab == TAB_DASHBOARD:
        render_tab_dashboard()
    else:
        render_tab_main()
