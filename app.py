from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="반다비 AI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

HTML_PATH = Path(__file__).parent / "bandabi_purple.html"

LANDING_CSS = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.0/css/all.min.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
<style>
#MainMenu, header, footer { visibility: hidden; height: 0 !important; }
.stApp {
  background: #e8e2f4 !important;
  font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
}
.block-container {
  padding: 1.5rem 1rem 2rem !important;
  max-width: 480px !important;
  margin: 0 auto !important;
}
.bandabi-landing-backdrop {
  min-height: calc(100vh - 3rem);
  display: flex; align-items: center; justify-content: center;
}
.bandabi-landing-card {
  width: 100%;
  background: #fff;
  border: 1px solid rgba(184,172,216,.28);
  border-radius: 2rem;
  padding: 1.75rem;
  box-shadow: 0 2px 20px rgba(109,40,217,.07);
}
.bandabi-landing-head { display: flex; gap: 1.25rem; align-items: flex-start; margin-bottom: .25rem; }
.bandabi-logo-shell {
  width: 80px; height: 80px; border-radius: 1.5rem; overflow: hidden; flex-shrink: 0;
}
.bandabi-logo-shell img { width: 100%; height: 100%; object-fit: contain; display: block; }
.bandabi-landing-title {
  margin: 0; font-size: 1.5rem; font-weight: 900; color: #2d2040; letter-spacing: -.03em;
}
.bandabi-landing-sub {
  margin: .35rem 0 0; font-size: .75rem; color: #7868a0; line-height: 1.6;
}
.bandabi-notice {
  margin-top: 1.25rem; padding: .75rem; border-radius: 1rem;
  background: #f0ecf8; border: 1px solid rgba(184,172,216,.28);
  font-size: 11px; line-height: 1.6; color: #7868a0;
}
.bandabi-notice b { color: #2d2040; }
.bandabi-mode-label {
  margin: 1.25rem 0 .5rem; font-size: .75rem; font-weight: 900;
  color: #2563eb; text-transform: uppercase; letter-spacing: .04em;
}
.bandabi-auth-error {
  margin-top: .75rem; padding: .65rem .75rem; border-radius: 1rem;
  background: #f0ecf8; border: 1px solid rgba(184,172,216,.28);
  color: #4a2d7a; font-size: .75rem; font-weight: 700;
}
.bandabi-logout-float {
  position: fixed; top: 12px; right: 12px; z-index: 999;
}
.bandabi-logout-float [data-testid="stButton"] button {
  border-radius: 999px !important; padding: .45rem .9rem !important;
  background: rgba(255,255,255,.88) !important; color: #4a2d7a !important;
  border: 1px solid rgba(184,172,216,.35) !important; font-size: .75rem !important;
  font-weight: 700 !important;
}
/* entry buttons */
.bandabi-entry [data-testid="stButton"] { margin: .5rem 0 0; }
.bandabi-entry [data-testid="stButton"] button {
  width: 100% !important; min-height: 76px !important; height: auto !important;
  border-radius: 1.5rem !important; padding: 1rem 1.1rem !important;
  text-align: left !important; justify-content: flex-start !important;
  font-weight: 900 !important; line-height: 1.35 !important; white-space: normal !important;
}
.bandabi-entry [data-testid="stButton"]:nth-of-type(1) button {
  background: #2563eb !important; color: #fff !important; border: none !important;
}
.bandabi-entry [data-testid="stButton"]:nth-of-type(2) button {
  background: #fff !important; color: #2d2040 !important;
  border: 1px solid rgba(184,172,216,.28) !important;
  box-shadow: 0 1px 8px rgba(109,40,217,.06) !important;
}
/* role buttons */
.bandabi-role [data-testid="stButton"] { margin: .5rem 0 0; }
.bandabi-role [data-testid="stButton"] button {
  width: 100% !important; min-height: 76px !important; height: auto !important;
  border-radius: 1.5rem !important; padding: 1rem 1.1rem !important;
  text-align: left !important; justify-content: flex-start !important;
  background: #fff !important; color: #2d2040 !important;
  border: 1px solid rgba(184,172,216,.28) !important;
  box-shadow: 0 1px 8px rgba(109,40,217,.06) !important;
  font-weight: 900 !important; line-height: 1.35 !important; white-space: normal !important;
}
.bandabi-role-back [data-testid="stButton"] button,
.bandabi-form-back [data-testid="stButton"] button {
  background: #f0ecf8 !important; color: #7868a0 !important;
  border: 1px solid rgba(184,172,216,.28) !important; min-height: 48px !important;
}
.bandabi-form-submit [data-testid="stButton"] button,
.bandabi-form-submit [data-testid="stFormSubmitButton"] button {
  background: #2563eb !important; color: #fff !important; border: none !important;
  min-height: 48px !important; font-weight: 900 !important;
}
/* form panel */
.bandabi-form-shell [data-testid="stForm"] {
  background: #f0ecf8; border: 1px solid rgba(184,172,216,.28);
  border-radius: 1.5rem; padding: 1rem; margin-top: 1rem;
}
.bandabi-form-shell [data-testid="stTextInput"] label p,
.bandabi-form-shell [data-testid="stTextInput"] label span {
  font-size: .75rem !important; font-weight: 700 !important; color: #7868a0 !important;
}
.bandabi-form-shell [data-testid="stTextInput"] input {
  border-radius: 1rem !important; border: 1px solid rgba(184,172,216,.28) !important;
  background: #fff !important; color: #2d2040 !important; padding: .75rem 1rem !important;
}
.bandabi-form-shell [data-testid="stTextInput"] input::placeholder { color: #b8acd8 !important; }
.bandabi-form-title { font-weight: 900; color: #2d2040; margin: 0 0 .15rem; }
.bandabi-form-help { font-size: .75rem; color: #7868a0; margin: 0 0 .75rem; }
iframe { display: block; width: 100% !important; border: 0 !important; }
.stApp:has(iframe) .block-container { max-width: 100% !important; padding: 0 !important; }
</style>
"""

AUTOCOMPLETE_JS_LOGIN = """
<script>
(function () {
  function patch(labelText, attrs) {
    const labels = Array.from(document.querySelectorAll('.bandabi-form-shell label p, .bandabi-form-shell label span'));
    const label = labels.find(function (el) { return (el.textContent || '').trim() === labelText; });
    if (!label) return;
    const wrap = label.closest('[data-testid="stTextInput"]');
    if (!wrap) return;
    const input = wrap.querySelector('input');
    if (!input) return;
    Object.keys(attrs).forEach(function (k) { input.setAttribute(k, attrs[k]); });
  }
  patch('이메일', { name: 'email', autocomplete: 'email', type: 'email' });
  patch('비밀번호', { name: 'current-password', autocomplete: 'current-password' });
})();
</script>
"""

AUTOCOMPLETE_JS_SIGNUP = """
<script>
(function () {
  function patch(labelText, attrs) {
    const labels = Array.from(document.querySelectorAll('.bandabi-form-shell label p, .bandabi-form-shell label span'));
    const label = labels.find(function (el) { return (el.textContent || '').trim() === labelText; });
    if (!label) return;
    const wrap = label.closest('[data-testid="stTextInput"]');
    if (!wrap) return;
    const input = wrap.querySelector('input');
    if (!input) return;
    Object.keys(attrs).forEach(function (k) { input.setAttribute(k, attrs[k]); });
  }
  patch('이름', { name: 'name', autocomplete: 'name' });
  patch('이메일', { name: 'email', autocomplete: 'email', type: 'email' });
  patch('비밀번호', { name: 'new-password', autocomplete: 'new-password' });
  patch('비밀번호 확인', { name: 'new-password-confirm', autocomplete: 'new-password' });
})();
</script>
"""


def load_logo_src() -> str:
    if not HTML_PATH.exists():
        return ""
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(r'<img src="(data:image/svg\+xml;base64,[^"]+)" alt="반다비 로고"', html)
    return match.group(1) if match else ""


def init_session_state() -> None:
    defaults: dict = {
        "is_authenticated": False,
        "user_name": "",
        "user_email": "",
        "role": "",
        "auth_step": "entry",
        "auth_mode": "login",
        "registered_users": {},
        "auth_error": "",
        "pending_name": "",
        "pending_email": "",
        "pending_password": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value


def reset_auth_flow() -> None:
    st.session_state.auth_step = "entry"
    st.session_state.auth_mode = "login"
    st.session_state.auth_error = ""
    st.session_state.pending_name = ""
    st.session_state.pending_email = ""
    st.session_state.pending_password = ""


def logout() -> None:
    st.session_state.is_authenticated = False
    st.session_state.user_name = ""
    st.session_state.user_email = ""
    st.session_state.role = ""
    reset_auth_flow()


def render_landing_header(subtitle: str) -> None:
    logo_src = load_logo_src()
    logo_html = (
        f'<img src="{logo_src}" alt="반다비 로고" />' if logo_src else '<div style="width:80px;height:80px;background:#4a2d7a;border-radius:1.5rem;"></div>'
    )
    st.markdown(
        f"""
        <div class="bandabi-landing-backdrop">
          <div class="bandabi-landing-card">
            <div class="bandabi-landing-head">
              <div class="bandabi-logo-shell">{logo_html}</div>
              <div style="height:80px;display:flex;flex-direction:column;justify-content:space-between;">
                <h1 class="bandabi-landing-title">반다비 AI</h1>
                <p class="bandabi-landing-sub">{subtitle}</p>
              </div>
            </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing_footer() -> None:
    st.markdown(
        """
            <div class="bandabi-notice">
              <b><i class="fa-solid fa-lock" style="color:#d97706;margin-right:4px;"></i>민감정보 고지</b><br/>
              본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고,
              생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def validate_form_step(name: str, email: str, password: str, confirm: str) -> bool:
    name = name.strip()
    email = email.strip().lower()
    if not email:
        st.session_state.auth_error = "이메일을 입력해 주세요."
        return False
    if not password:
        st.session_state.auth_error = "비밀번호를 입력해 주세요."
        return False
    if st.session_state.auth_mode == "signup":
        if not name:
            st.session_state.auth_error = "이름을 입력해 주세요."
            return False
        if len(password) < 8:
            st.session_state.auth_error = "비밀번호는 8자 이상이어야 합니다."
            return False
        if password != confirm:
            st.session_state.auth_error = "비밀번호가 일치하지 않습니다."
            return False
        if email in st.session_state.registered_users:
            st.session_state.auth_error = "이미 사용 중인 이메일입니다."
            return False
        st.session_state.pending_name = name
        st.session_state.pending_email = email
        st.session_state.pending_password = password
    else:
        user = st.session_state.registered_users.get(email)
        if not user or user.get("password") != password:
            st.session_state.auth_error = "이메일 또는 비밀번호가 올바르지 않습니다."
            return False
        st.session_state.pending_name = user["name"]
        st.session_state.pending_email = email
        st.session_state.pending_password = password
    st.session_state.auth_error = ""
    return True


def finalize_auth(role: str) -> None:
    email = st.session_state.pending_email.strip().lower()
    name = st.session_state.pending_name.strip()
    password = st.session_state.pending_password
    if st.session_state.auth_mode == "signup":
        st.session_state.registered_users[email] = {
            "name": name,
            "password": password,
            "role": role,
        }
    else:
        user = st.session_state.registered_users.get(email)
        if user:
            user["role"] = role
    st.session_state.is_authenticated = True
    st.session_state.user_name = name
    st.session_state.user_email = email
    st.session_state.role = role
    st.session_state.auth_error = ""
    reset_auth_flow()


def render_auth_page() -> None:
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    step = st.session_state.auth_step
    mode = st.session_state.auth_mode

    if step == "entry":
        render_landing_header("서비스 이용을 위해 로그인하거나<br/>회원가입을 진행하세요.")
        st.markdown('<div class="bandabi-entry">', unsafe_allow_html=True)
        if st.button("로그인\n\n기존 계정으로 서비스 이어가기", use_container_width=True, key="auth_go_login"):
            st.session_state.auth_mode = "login"
            st.session_state.auth_step = "form"
            st.session_state.auth_error = ""
            st.rerun()
        if st.button("회원가입\n\n접근성 지원 유형과 알림 설정을 시작", use_container_width=True, key="auth_go_signup"):
            st.session_state.auth_mode = "signup"
            st.session_state.auth_step = "form"
            st.session_state.auth_error = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif step == "form":
        subtitle = "로그인 후 이용자/관리자 모드를 선택하세요." if mode == "login" else "회원가입 후 이용자/관리자 모드를 선택하세요."
        render_landing_header(subtitle)
        title = "회원가입" if mode == "signup" else "로그인"
        help_text = (
            "이름, 이메일, 비밀번호를 입력하면 로컬 계정이 생성됩니다. (프로토타입용)"
            if mode == "signup"
            else "가입한 이메일과 비밀번호로 로그인합니다. (프로토타입용 로컬 인증)"
        )
        st.markdown(
            f"""
            <form autocomplete="on" style="display:none" aria-hidden="true">
              {"<input name='name' autocomplete='name' />" if mode == "signup" else ""}
              <input type="email" name="email" autocomplete="email" />
              <input type="password" name="{"new-password" if mode == "signup" else "current-password"}" autocomplete="{"new-password" if mode == "signup" else "current-password"}" />
              {"<input type='password' name='new-password-confirm' autocomplete='new-password' />" if mode == "signup" else ""}
            </form>
            <div class="bandabi-form-shell">
              <p class="bandabi-form-title">{title}</p>
              <p class="bandabi-form-help">{help_text}</p>
            """,
            unsafe_allow_html=True,
        )
        with st.form("bandabi_auth_form", clear_on_submit=False):
            name = ""
            confirm = ""
            if mode == "signup":
                name = st.text_input("이름", placeholder="예: 000")
            email = st.text_input("이메일", placeholder="user@example.com")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            if mode == "signup":
                confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="bandabi-form-back">', unsafe_allow_html=True)
                back = st.form_submit_button("이전", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="bandabi-form-submit">', unsafe_allow_html=True)
                submit = st.form_submit_button("계속", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(AUTOCOMPLETE_JS_SIGNUP if mode == "signup" else AUTOCOMPLETE_JS_LOGIN, unsafe_allow_html=True)

        if back:
            st.session_state.auth_step = "entry"
            st.session_state.auth_error = ""
            st.rerun()
        if submit and validate_form_step(name, email, password, confirm):
            st.session_state.auth_step = "role"
            st.rerun()

    elif step == "role":
        render_landing_header("접속할 서비스를 선택하세요.")
        st.markdown('<p class="bandabi-mode-label">Mode Select</p><div class="bandabi-role">', unsafe_allow_html=True)
        if st.button("이용자 모드\n\n경로 · 동행 · 강습 · 리포트", use_container_width=True, key="auth_role_b2c"):
            finalize_auth("B2C")
            st.rerun()
        if st.button("기관 관리자 모드\n\n스케줄 · 접근성 점검 보조 · 대시보드", use_container_width=True, key="auth_role_b2g"):
            finalize_auth("B2G")
            st.rerun()
        st.markdown('</div><div class="bandabi-role-back">', unsafe_allow_html=True)
        if st.button("로그인/회원가입으로 돌아가기", use_container_width=True, key="auth_role_back"):
            st.session_state.auth_step = "entry"
            st.session_state.auth_error = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.auth_error:
        st.markdown(f'<div class="bandabi-auth-error">{st.session_state.auth_error}</div>', unsafe_allow_html=True)

    render_landing_footer()


def render_app_iframe() -> None:
    if not HTML_PATH.exists():
        st.error("bandabi_purple.html 파일을 찾을 수 없습니다.")
        return

    html = HTML_PATH.read_text(encoding="utf-8")
    bootstrap = {
        "email": st.session_state.user_email,
        "name": st.session_state.user_name,
        "role": st.session_state.role,
        "streamlitAuth": True,
    }
    inject = (
        "<script>"
        f"window.BANDABI_BOOTSTRAP = {json.dumps(bootstrap, ensure_ascii=False)};"
        "window.BANDABI_STREAMLIT_AUTH = true;"
        "</script>"
    )
    if "</head>" in html:
        html = html.replace("</head>", inject + "\n</head>", 1)
    else:
        html = inject + html

    st.markdown(
        """
        <style>
        #MainMenu, header, footer { visibility: hidden; }
        .stApp { margin: 0; padding: 0; background: #e8e2f4; }
        .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    components.html(html, height=950, scrolling=True)


def main() -> None:
    init_session_state()

    if not st.session_state.is_authenticated:
        render_auth_page()
        return

    st.markdown(
        '<div class="bandabi-logout-float">',
        unsafe_allow_html=True,
    )
    if st.button("로그아웃"):
        logout()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    render_app_iframe()


main()
