"""Bandabi AI — Streamlit native login/signup UI (HTML-aligned, auth-only phase)."""

from __future__ import annotations

import html
from pathlib import Path
from textwrap import dedent
from typing import Any
from urllib.parse import quote

import streamlit as st


st.set_page_config(
    page_title="반다비 AI",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SENSITIVE_NOTICE = (
    "본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고, "
    "생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다."
)
FOOTNOTE = (
    "* 계정·비밀번호는 데모용으로 브라우저 저장소에만 보관되며, "
    "실제 서버 인증·암호화 보안을 제공하지 않습니다."
)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def html_block(markup: str) -> str:
    return " ".join(line.strip() for line in dedent(markup).splitlines() if line.strip())


def bandabi_icon_data_uri() -> str:
    svg_path = Path(__file__).resolve().parent / "assets" / "img" / "icon.svg"
    try:
        svg = svg_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    svg = svg.replace("#7770FF", "#4a2d7a").replace("#DAD8FF", "#d9d3ef")
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def init_state() -> None:
    defaults: dict[str, Any] = {
        "logged_in": False,
        "auth_stage": "entry",
        "auth_mode": "login",
        "user_name": "",
        "user_email": "",
        "role": "user",
        "bt_points": 3500,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def inject_auth_css() -> None:
    st.markdown(
        html_block("""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');
        #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0 !important; min-height: 0 !important; }
        [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
        .stApp {
            background: radial-gradient(1200px 680px at 50% -10%, #2f2448 0%, #1a1428 48%, #120e1a 100%);
            color: #2d2040;
            font-family: "Pretendard Variable", "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif;
        }
        .block-container {
            max-width: 100%;
            padding-top: 0;
            padding-bottom: 2rem;
        }
        .auth-shell {
            min-height: calc(100vh - 24px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 18px 0;
        }
        .auth-card {
            box-sizing: border-box;
            width: min(540px, calc(100vw - 36px));
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.18);
            border-radius: 20px;
            padding: 34px 34px 31px;
            box-shadow: 0 24px 60px rgba(74,45,122,.115);
        }
        .auth-head {
            display: flex;
            align-items: center;
            gap: 24px;
            margin-bottom: 34px;
        }
        .auth-logo {
            width: 96px;
            height: 96px;
            flex: 0 0 96px;
            border-radius: 21px;
            display: block;
        }
        .auth-title {
            margin: 0;
            color: #241936;
            font-size: 30px;
            line-height: 1.05;
            font-weight: 900;
        }
        .auth-sub {
            margin: 17px 0 0;
            color: #6f5f96;
            font-size: 14px;
            line-height: 1.65;
            font-weight: 300;
            word-break: keep-all;
        }
        .auth-choice {
            display: flex;
            align-items: center;
            gap: 18px;
            min-height: 96px;
            width: 100%;
            border-radius: 16px;
            padding: 18px 20px;
            text-decoration: none !important;
            transition: transform .15s ease, box-shadow .15s ease;
            box-sizing: border-box;
        }
        .auth-choice + .auth-choice { margin-top: 16px; }
        .auth-choice.primary {
            background: #4a2d7a;
            color: #fff !important;
            border: 1px solid #4a2d7a;
            box-shadow: 0 13px 27px rgba(74,45,122,.31);
        }
        .auth-choice.secondary {
            background: #fff;
            border: 1px solid rgba(184,172,216,.26);
            color: #241936 !important;
            box-shadow: 0 10px 24px rgba(109,40,217,.075);
        }
        .auth-choice-icon {
            width: 58px;
            height: 58px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 58px;
        }
        .auth-choice.primary .auth-choice-icon { background: rgba(255,255,255,.15); color: #fff; }
        .auth-choice.secondary .auth-choice-icon { background: #f0e3ff; color: #4a2d7a; }
        .auth-choice-title { display: block; font-size: 20px; line-height: 1.2; font-weight: 900; }
        .auth-choice-desc { display: block; margin-top: 5px; font-size: 14px; line-height: 1.38; font-weight: 300; }
        .auth-choice.secondary .auth-choice-desc { color: #7a6aa0; }
        .auth-panel {
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.34);
            border-radius: 16px;
            padding: 20px 19px 18px;
            margin-bottom: 18px;
        }
        .auth-panel-title {
            margin: 0;
            color: #241936;
            font-size: 20px;
            font-weight: 900;
        }
        .auth-panel-copy {
            margin: 8px 0 0;
            color: #7a6aa0;
            font-size: 13px;
            line-height: 1.55;
            font-weight: 300;
        }
        .auth-notice {
            margin-top: 26px;
            border-radius: 14px;
            border: 1px solid rgba(184,172,216,.32);
            background: #f0ecf8;
            color: #6f5f96;
            padding: 15px 17px;
            font-size: 12px;
            line-height: 1.72;
            font-weight: 300;
            word-break: keep-all;
        }
        .auth-notice-title {
            display: block;
            color: #4a2d7a;
            font-size: 13px;
            font-weight: 900;
            margin-bottom: 6px;
        }
        .auth-footnote {
            margin: 14px 0 0;
            color: #7a6aa0;
            text-align: center;
            font-size: 11px;
            line-height: 1.65;
            font-weight: 200;
        }
        .auth-form-wrap label, .auth-form-wrap .stTextInput label {
            color: #6f5f96 !important;
            font-size: 13px !important;
            font-weight: 900 !important;
            margin-bottom: 10px !important;
        }
        .auth-form-wrap [data-testid="stTextInput"] input {
            height: 54px;
            border-radius: 12px;
            border: 0;
            background: #ffffff;
            color: #241936;
            font-size: 16px;
            font-weight: 300;
            padding: 0 20px;
            box-shadow: none;
        }
        .auth-form-wrap [data-testid="stTextInput"] { margin-bottom: 18px; }
        .auth-form-wrap div[data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
        div[data-testid="stButton"] > button {
            min-height: 55px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 900;
            border: 1px solid rgba(184,172,216,.34);
            background: #2a2238;
            color: #e8e2f4;
        }
        .st-key-btn_auth_back div[data-testid="stButton"] > button,
        .st-key-btn_role_back div[data-testid="stButton"] > button,
        .st-key-btn_logout div[data-testid="stButton"] > button {
            background: #241c34 !important;
            color: #d8d0ea !important;
            border: 1px solid rgba(184,172,216,.22) !important;
            box-shadow: none !important;
        }
        .st-key-btn_auth_login div[data-testid="stButton"] > button,
        .st-key-btn_auth_signup div[data-testid="stButton"] > button {
            min-height: 96px;
            text-align: left;
            padding: 18px 20px;
            white-space: pre-line;
            line-height: 1.35;
        }
        .st-key-btn_auth_login div[data-testid="stButton"] > button {
            background: #4a2d7a !important;
            color: #fff !important;
            border: 1px solid #4a2d7a !important;
            box-shadow: 0 13px 27px rgba(74,45,122,.31) !important;
        }
        .st-key-btn_auth_signup div[data-testid="stButton"] > button {
            background: #fff !important;
            color: #241936 !important;
            border: 1px solid rgba(184,172,216,.26) !important;
            box-shadow: 0 10px 24px rgba(109,40,217,.075) !important;
        }
        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {
            background: #4a2d7a;
            color: #ffffff;
            border: 1px solid #4a2d7a;
            box-shadow: 0 12px 24px rgba(74,45,122,.28);
        }
        .role-card-btn div[data-testid="stButton"] > button {
            min-height: 96px;
            text-align: left;
            padding: 18px 20px;
            white-space: normal;
            line-height: 1.35;
        }
        .role-card-btn.user div[data-testid="stButton"] > button {
            background: #4a2d7a;
            color: #fff;
            border-color: #4a2d7a;
            box-shadow: 0 13px 27px rgba(74,45,122,.31);
        }
        .placeholder-card {
            max-width: 720px;
            margin: 48px auto;
            background: #fff;
            border: 1px solid rgba(184,172,216,.18);
            border-radius: 20px;
            padding: 32px;
            box-shadow: 0 24px 60px rgba(74,45,122,.115);
            text-align: center;
        }
        .placeholder-title {
            margin: 0;
            font-size: 28px;
            font-weight: 900;
            color: #241936;
        }
        .placeholder-copy {
            margin: 14px 0 0;
            color: #7a6aa0;
            font-size: 14px;
            line-height: 1.65;
        }
        @media (max-width: 640px) {
            .auth-card { padding: 26px 18px 24px; }
            .auth-head { gap: 16px; margin-bottom: 26px; }
            .auth-logo { width: 76px; height: 76px; flex-basis: 76px; }
            .auth-title { font-size: 24px; }
            .auth-sub { margin-top: 10px; font-size: 13px; }
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def logo_html(css_class: str = "auth-logo") -> str:
    icon_src = bandabi_icon_data_uri()
    if icon_src:
        return f'<img class="{css_class}" src="{icon_src}" alt="반다비">'
    return (
        f'<span class="{css_class}" style="background:#4a2d7a;color:#fff;'
        f'display:flex;align-items:center;justify-content:center;font-weight:900;font-size:30px;">B</span>'
    )


def notice_html() -> str:
    return html_block(f"""
    <div class="auth-notice">
        <span class="auth-notice-title">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="vertical-align:-2px;margin-right:4px;">
                <rect x="5" y="10" width="14" height="10" rx="2" fill="currentColor"/>
                <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
            </svg>
            민감정보 고지
        </span>
        {esc(SENSITIVE_NOTICE)}
    </div>
    <p class="auth-footnote">{esc(FOOTNOTE)}</p>
    """)


def auth_subtitle() -> str:
    stage = st.session_state.get("auth_stage", "entry")
    mode = st.session_state.get("auth_mode", "login")
    if stage == "entry":
        return "서비스 이용을 위해 로그인하거나<br>회원가입을 진행하세요."
    if stage == "role":
        return "접속할 서비스를 선택하세요."
    if mode == "signup":
        return "회원가입 후 이용자/관리자 모드를 선택하세요."
    return "로그인 후 이용자/관리자 모드를 선택하세요."


def render_auth_header() -> None:
    st.markdown(
        html_block(f"""
        <div class="auth-head">
            {logo_html()}
            <div>
                <div class="auth-title" role="heading" aria-level="1">반다비 AI</div>
                <p class="auth-sub">{auth_subtitle()}</p>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_entry() -> None:
    st.markdown('<div class="auth-shell"><section class="auth-card">', unsafe_allow_html=True)
    render_auth_header()

    if st.button("로그인\n\n기존 계정으로 서비스 이어가기", key="btn_auth_login", use_container_width=True, type="primary"):
        st.session_state.auth_mode = "login"
        st.session_state.auth_stage = "form"
        st.rerun()
    if st.button("회원가입\n\n접근성 지원 유형과 알림 설정을 시작", key="btn_auth_signup", use_container_width=True):
        st.session_state.auth_mode = "signup"
        st.session_state.auth_stage = "form"
        st.rerun()

    st.markdown(notice_html(), unsafe_allow_html=True)
    st.markdown("</section></div>", unsafe_allow_html=True)


def render_form() -> None:
    mode = st.session_state.get("auth_mode", "login")
    is_signup = mode == "signup"
    panel_title = "회원가입" if is_signup else "로그인"
    panel_copy = (
        "프로토타입에서는 기본 정보만 입력하고 역할 선택으로 이동합니다."
        if is_signup
        else "프로토타입에서는 실제 인증 없이 다음 단계로 이동합니다."
    )

    st.markdown('<div class="auth-shell"><section class="auth-card">', unsafe_allow_html=True)
    render_auth_header()
    st.markdown(
        html_block(f"""
        <div class="auth-panel">
            <div class="auth-panel-title">{esc(panel_title)}</div>
            <p class="auth-panel-copy">{esc(panel_copy)}</p>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-form-wrap">', unsafe_allow_html=True)
    if is_signup:
        st.session_state.user_name = st.text_input("이름", value=st.session_state.get("user_name") or "", placeholder="예: 000")
    st.session_state.user_email = st.text_input(
        "이메일",
        value=st.session_state.get("user_email") or "",
        placeholder="user@example.com",
    )
    st.text_input("비밀번호", type="password", placeholder="비밀번호", key="auth_password")
    if is_signup:
        st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 확인", key="auth_password_confirm")
    st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("이전", key="btn_auth_back", use_container_width=True):
            st.session_state.auth_stage = "entry"
            st.rerun()
    with b2:
        if st.button("계속", key="btn_auth_continue", type="primary", use_container_width=True):
            email = (st.session_state.get("user_email") or "").strip()
            if not email:
                st.warning("이메일을 입력해 주세요.")
            elif is_signup and not (st.session_state.get("user_name") or "").strip():
                st.warning("이름을 입력해 주세요.")
            elif is_signup and st.session_state.get("auth_password") != st.session_state.get("auth_password_confirm"):
                st.warning("비밀번호 확인이 일치하지 않습니다.")
            else:
                if not is_signup and not (st.session_state.get("user_name") or "").strip():
                    st.session_state.user_name = email.split("@")[0] or "000"
                st.session_state.auth_stage = "role"
                st.rerun()

    st.markdown(notice_html(), unsafe_allow_html=True)
    st.markdown("</section></div>", unsafe_allow_html=True)


def render_role_select() -> None:
    st.markdown('<div class="auth-shell"><section class="auth-card">', unsafe_allow_html=True)
    render_auth_header()

    st.markdown(
        html_block("""
        <div class="auth-panel">
            <div class="auth-panel-title">Mode Select</div>
            <p class="auth-panel-copy">이용자 모드 또는 기관 관리자 모드를 선택하세요.</p>
        </div>
        """),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="role-card-btn user">', unsafe_allow_html=True)
    if st.button(
        "이용자 모드\n\n경로 · 동행 · 강습 · 리포트",
        key="btn_role_user",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.role = "user"
        st.session_state.logged_in = True
        st.session_state.auth_stage = "done"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="role-card-btn">', unsafe_allow_html=True)
    if st.button(
        "기관 관리자 모드\n\n스케줄 · 접근성 점검 · 대시보드",
        key="btn_role_admin",
        use_container_width=True,
    ):
        st.session_state.role = "admin"
        st.session_state.logged_in = True
        st.session_state.auth_stage = "done"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("로그인/회원가입으로 돌아가기", key="btn_role_back", use_container_width=True):
        st.session_state.auth_stage = "entry"
        st.rerun()

    st.markdown(notice_html(), unsafe_allow_html=True)
    st.markdown("</section></div>", unsafe_allow_html=True)


def render_placeholder() -> None:
    name = st.session_state.get("user_name") or "000"
    role_label = "관리자" if st.session_state.get("role") == "admin" else "이용자"
    st.markdown(
        html_block(f"""
        <div class="placeholder-card">
            <p class="placeholder-title">반갑습니다, {esc(name)}님</p>
            <p class="placeholder-copy">
                {esc(role_label)} 모드 로그인이 완료되었습니다.<br>
                사용자 시작 화면 구현 예정
            </p>
        </div>
        """),
        unsafe_allow_html=True,
    )
    if st.button("로그아웃", key="btn_logout"):
        for key, value in {
            "logged_in": False,
            "auth_stage": "entry",
            "auth_mode": "login",
            "user_name": "",
            "user_email": "",
            "role": "user",
        }.items():
            st.session_state[key] = value
        st.rerun()


def render_auth() -> None:
    stage = st.session_state.get("auth_stage", "entry")
    if stage == "entry":
        render_entry()
    elif stage == "form":
        render_form()
    elif stage == "role":
        render_role_select()
    else:
        st.session_state.auth_stage = "entry"
        render_entry()


init_state()
inject_auth_css()

if not st.session_state.get("logged_in"):
    render_auth()
else:
    render_placeholder()
