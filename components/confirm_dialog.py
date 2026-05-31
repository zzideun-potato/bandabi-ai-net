"""Simulated confirm / reward modal — no real booking or dispatch."""

from __future__ import annotations

import os

import streamlit as st

from modules.safety import sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def apply_pending_confirm(pending: dict) -> None:
    """Apply a confirmed pending action — testable without modal widgets."""
    st.session_state.pending_confirm = None

    bt_delta = int(pending.get("bt_delta") or 0)
    if bt_delta:
        st.session_state.bt_balance = int(st.session_state.get("bt_balance", 0)) + bt_delta

    next_step = pending.get("next_step")
    if next_step:
        st.session_state.main_step = next_step

    key = pending.get("on_confirm_key")
    if key == "buddy":
        st.session_state.journey["buddy"] = s("첫 방문 버디 후보 연결 요청 등록(운영기관 검토)")
    elif key == "class":
        st.session_state.journey["class"] = s("강습·지도자 추천 등록(운영기관 검토)")
    elif key == "route":
        st.session_state.journey["route_plan"] = s("예약·이동·동행 플랜 요청 등록(운영기관 검토)")
    elif key == "guardian":
        st.session_state.journey["guardian_shared"] = True

    st.session_state.toast_message = s(
        pending.get("toast") or "운영 확정 요청이 등록되었습니다. 운영기관 검토가 필요합니다."
    )


def _render_confirm_panel(pending: dict) -> bool:
    """Inline confirm panel (AppTest-friendly). Returns True if confirmed this run."""
    st.markdown(
        f"""
        <div class="bandabi-reward-modal">
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <div class="bandabi-reward-icon" aria-hidden="true"><i class="fa-solid fa-circle-check"></i></div>
            <div>
              <div style="font-size:1.15rem;font-weight:900;">{s(pending["title"])}</div>
              <div class="bandabi-mid" style="font-size:13px;margin-top:6px;">{s(pending["subtitle"])}</div>
            </div>
          </div>
          <div class="bandabi-soft" style="margin-top:16px;line-height:1.75;">{s(pending["message"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    bt_delta = int(pending.get("bt_delta") or 0)
    if bt_delta:
        st.markdown(
            f'<span class="bandabi-badge warn">{s(f"참여 인센티브 {bt_delta}BT 적립(비현금)")}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<p class="bandabi-modal-note">{s("현금 환급·양도·재판매는 불가하며, 협약된 생활체육 서비스 혜택으로만 사용할 수 있습니다. 최종 확정은 운영기관 검토가 필요합니다.")}</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button(s("취소"), key="pending_confirm_cancel", use_container_width=True):
            st.session_state.pending_confirm = None
            st.rerun()
    with c2:
        st.markdown('<div class="bandabi-btn-confirm">', unsafe_allow_html=True)
        confirmed_btn = st.button(s("확인"), type="primary", key="pending_confirm_ok", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if confirmed_btn:
            return True
    return False


def open_confirm(
    *,
    title: str,
    subtitle: str,
    message: str,
    bt_delta: int = 0,
    next_step: str | None = None,
    on_confirm_key: str | None = None,
) -> None:
    st.session_state.pending_confirm = {
        "title": title,
        "subtitle": subtitle,
        "message": message,
        "bt_delta": bt_delta,
        "next_step": next_step,
        "on_confirm_key": on_confirm_key,
    }


def process_pending_confirm(*, dialog_confirmed: bool | None = None) -> None:
    pending = st.session_state.get("pending_confirm")
    if not pending:
        return

    confirmed = bool(dialog_confirmed)
    if dialog_confirmed is None:
        confirmed = _render_confirm_panel(pending)

    if not confirmed:
        return

    apply_pending_confirm(pending)
    if os.environ.get("BANDABI_PYTEST") != "1":
        st.rerun()
