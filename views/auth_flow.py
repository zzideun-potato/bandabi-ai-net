"""Prototype auth modal — no real authentication."""

from __future__ import annotations

import streamlit as st

from components.html_assets import brand_logo_markup
from components.session_state import ROLE_B2C, ROLE_B2G, complete_role_login
from modules.safety import SERVICE_DISCLAIMER, sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


@st.dialog(s("반다비 AI"), width="large")
def auth_dialog() -> None:
    step = st.session_state.auth_step
    mode = st.session_state.auth_mode

    st.markdown(
        f"""
        <div style="display:flex;gap:16px;align-items:flex-start;margin-bottom:12px;">
          {brand_logo_markup(size=72)}
          <div>
            <div style="font-size:1.35rem;font-weight:900;">반다비 AI</div>
            <div class="bandabi-mid" style="font-size:12px;line-height:1.6;margin-top:4px;">
              {s("서비스 이용을 위해 로그인하거나 회원가입을 진행하세요.") if step == "entry" else s("접속할 서비스를 선택하세요.")}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if step == "entry":
        if st.button(s("로그인 — 기존 계정으로 서비스 이어가기"), type="primary", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.session_state.auth_step = "form"
            st.rerun()
        if st.button(s("회원가입 — 접근성 지원 유형과 알림 설정을 시작"), use_container_width=True):
            st.session_state.auth_mode = "signup"
            st.session_state.auth_step = "form"
            st.rerun()

    elif step == "form":
        title = s("회원가입") if mode == "signup" else s("로그인")
        st.markdown(f"**{title}**")
        st.caption(
            s(
                "프로토타입에서는 기본 정보만 입력하고 역할 선택으로 이동합니다."
                if mode == "signup"
                else "프로토타입에서는 실제 인증 없이 다음 단계로 이동합니다."
            )
        )
        st.session_state.user_name = st.text_input(s("이름"), value=st.session_state.user_name, placeholder=s("예: 000"))
        st.session_state.user_email = st.text_input(
            s("이메일"), value=st.session_state.user_email, placeholder="user@example.com"
        )
        st.text_input(
            s("비밀번호"),
            type="password",
            placeholder=s("8자 이상(프로토타입)"),
            key="auth_password",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(s("이전"), use_container_width=True):
                st.session_state.auth_step = "entry"
                st.rerun()
        with c2:
            if st.button(s("계속"), type="primary", use_container_width=True):
                st.session_state.auth_step = "role"
                st.rerun()

    elif step == "role":
        st.markdown(f'<p class="bandabi-tiny">{s("Mode Select")}</p>', unsafe_allow_html=True)
        if st.button(s("이용자 모드 — 경로 · 동행 · 강습 · 리포트"), use_container_width=True):
            complete_role_login(ROLE_B2C, st.session_state.user_name or "000")
            st.rerun()
        if st.button(s("기관 관리자 모드 — 스케줄 · 접근성 점검 · 대시보드"), use_container_width=True):
            complete_role_login(ROLE_B2G, st.session_state.user_name or "000")
            st.rerun()
        if st.button(s("로그인/회원가입으로 돌아가기"), use_container_width=True):
            st.session_state.auth_step = "entry"
            st.rerun()

    st.markdown(
        f"""
        <div class="bandabi-modal-note" style="margin-top:12px;">
          <b>{s("민감정보 고지")}</b><br/>
          {s("본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고, 생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다.")}
        </div>
        <div class="bandabi-modal-note">{s(SERVICE_DISCLAIMER)}</div>
        """,
        unsafe_allow_html=True,
    )


def ensure_authenticated() -> bool:
    if st.session_state.get("authenticated"):
        return True
    auth_dialog()
    return False
