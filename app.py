from __future__ import annotations

import json
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

AUTH_CSS = """
<style>
#MainMenu, header, footer { visibility: hidden; }
.stApp { background: #e8e2f4; }
.block-container { padding-top: 1.5rem !important; max-width: 720px !important; }
.bandabi-auth-title { font-size: 1.75rem; font-weight: 900; color: #2c2840; margin: 0; }
.bandabi-auth-sub { color: #9080b0; font-size: 0.85rem; margin-top: 0.35rem; }
.bandabi-auth-note { color: #b45309; font-size: 0.75rem; margin-top: 1rem; line-height: 1.5; }
.bandabi-app-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.5rem 1rem; margin-bottom: 0.25rem;
  background: rgba(255,255,255,.75); border-radius: 12px;
  border: 1px solid rgba(180,160,230,.25);
}
.bandabi-app-bar span { font-size: 0.85rem; color: #5b4d7a; font-weight: 700; }
iframe { display: block; width: 100% !important; border: 0 !important; }
.stApp .block-container:has(+ iframe), .stApp iframe { max-width: 100% !important; }
</style>
"""

AUTOCOMPLETE_JS_LOGIN = """
<script>
(function () {
  function patch(labelText, attrs) {
    const labels = Array.from(document.querySelectorAll('label p, label span, label'));
    const label = labels.find(function (el) {
      return (el.textContent || '').trim() === labelText;
    });
    if (!label) return;
    const wrap = label.closest('[data-testid="stTextInput"]') || label.closest('.stTextInput');
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
    const labels = Array.from(document.querySelectorAll('label p, label span, label'));
    const label = labels.find(function (el) {
      return (el.textContent || '').trim() === labelText;
    });
    if (!label) return;
    const wrap = label.closest('[data-testid="stTextInput"]') || label.closest('.stTextInput');
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


def init_session_state() -> None:
    defaults: dict = {
        "is_authenticated": False,
        "user_name": "",
        "user_email": "",
        "role": "",
        "auth_mode": "login",
        "registered_users": {},
        "auth_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value


def logout() -> None:
    st.session_state.is_authenticated = False
    st.session_state.user_name = ""
    st.session_state.user_email = ""
    st.session_state.role = ""
    st.session_state.auth_error = ""


def handle_signup(name: str, email: str, password: str, confirm: str, role: str) -> None:
    name = name.strip()
    email = email.strip().lower()
    if not name:
        st.session_state.auth_error = "이름을 입력해 주세요."
        return
    if not email:
        st.session_state.auth_error = "이메일을 입력해 주세요."
        return
    if len(password) < 8:
        st.session_state.auth_error = "비밀번호는 8자 이상이어야 합니다."
        return
    if password != confirm:
        st.session_state.auth_error = "비밀번호가 일치하지 않습니다."
        return
    if email in st.session_state.registered_users:
        st.session_state.auth_error = "이미 사용 중인 이메일입니다."
        return
    st.session_state.registered_users[email] = {
        "name": name,
        "password": password,
        "role": role,
    }
    st.session_state.is_authenticated = True
    st.session_state.user_name = name
    st.session_state.user_email = email
    st.session_state.role = role
    st.session_state.auth_error = ""


def handle_login(email: str, password: str, role: str) -> None:
    email = email.strip().lower()
    user = st.session_state.registered_users.get(email)
    if not user or user.get("password") != password:
        st.session_state.auth_error = "이메일 또는 비밀번호가 올바르지 않습니다."
        return
    st.session_state.is_authenticated = True
    st.session_state.user_name = user["name"]
    st.session_state.user_email = email
    st.session_state.role = role
    st.session_state.auth_error = ""
    user["role"] = role


def render_auth_page() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    st.markdown(
        '<p class="bandabi-auth-title">반다비 AI</p>'
        '<p class="bandabi-auth-sub">프로토타입용 로컬 인증 · Streamlit 최상위 화면'
        " (Chrome 비밀번호 관리자 인식 가능)</p>",
        unsafe_allow_html=True,
    )

    mode_cols = st.columns(2)
    with mode_cols[0]:
        if st.button(
            "로그인",
            use_container_width=True,
            type="primary" if st.session_state.auth_mode == "login" else "secondary",
        ):
            st.session_state.auth_mode = "login"
            st.session_state.auth_error = ""
            st.rerun()
    with mode_cols[1]:
        if st.button(
            "회원가입",
            use_container_width=True,
            type="primary" if st.session_state.auth_mode == "signup" else "secondary",
        ):
            st.session_state.auth_mode = "signup"
            st.session_state.auth_error = ""
            st.rerun()

    # Chrome 휴리스틱용 HTML form (제출은 Streamlit form이 처리)
    if st.session_state.auth_mode == "signup":
        st.html(
            """
            <form autocomplete="on" style="margin:0;padding:0;height:0;overflow:hidden;opacity:0;pointer-events:none" aria-hidden="true">
              <input type="text" name="name" autocomplete="name" tabindex="-1" />
              <input type="email" name="email" autocomplete="email" tabindex="-1" />
              <input type="password" name="new-password" autocomplete="new-password" tabindex="-1" />
              <input type="password" name="new-password-confirm" autocomplete="new-password" tabindex="-1" />
            </form>
            """,
            width=0,
            height=0,
        )
    else:
        st.html(
            """
            <form autocomplete="on" style="margin:0;padding:0;height:0;overflow:hidden;opacity:0;pointer-events:none" aria-hidden="true">
              <input type="email" name="email" autocomplete="email" tabindex="-1" />
              <input type="password" name="current-password" autocomplete="current-password" tabindex="-1" />
            </form>
            """,
            width=0,
            height=0,
        )

    with st.form("bandabi_auth_form", clear_on_submit=False):
        role_label = st.radio(
            "접속 모드",
            options=["이용자 모드 (B2C)", "기관 관리자 (B2G)"],
            horizontal=True,
        )
        role = "B2C" if role_label.startswith("이용자") else "B2G"

        name = ""
        confirm = ""
        if st.session_state.auth_mode == "signup":
            name = st.text_input("이름", placeholder="예: 홍길동")
        email = st.text_input("이메일", placeholder="user@example.com")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        if st.session_state.auth_mode == "signup":
            confirm = st.text_input(
                "비밀번호 확인",
                type="password",
                placeholder="비밀번호를 다시 입력하세요",
            )

        submitted = st.form_submit_button("계속", use_container_width=True)

    if st.session_state.auth_mode == "signup":
        st.markdown(AUTOCOMPLETE_JS_SIGNUP, unsafe_allow_html=True)
    else:
        st.markdown(AUTOCOMPLETE_JS_LOGIN, unsafe_allow_html=True)

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    st.markdown(
        '<p class="bandabi-auth-note">'
        "※ 프로토타입용 로컬 인증입니다. 실제 DB·서버 보안 인증이 아닙니다.<br/>"
        "※ Chrome 비밀번호 추천·저장 UI는 브라우저가 판단하며, 코드로 강제 표시할 수 없습니다."
        "</p>",
        unsafe_allow_html=True,
    )

    if submitted:
        if st.session_state.auth_mode == "signup":
            handle_signup(name, email, password, confirm, role)
        else:
            handle_login(email, password, role)
        if st.session_state.is_authenticated:
            st.rerun()


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


def render_app_bar() -> None:
    role_label = "이용자" if st.session_state.role == "B2C" else "기관 관리자"
    bar_left, bar_right = st.columns([5, 1])
    with bar_left:
        st.markdown(
            f'<div class="bandabi-app-bar">'
            f"<span>{st.session_state.user_name}님 · {role_label} · "
            f"{st.session_state.user_email}</span></div>",
            unsafe_allow_html=True,
        )
    with bar_right:
        if st.button("로그아웃", use_container_width=True):
            logout()
            st.rerun()


def main() -> None:
    init_session_state()

    if not st.session_state.is_authenticated:
        render_auth_page()
        return

    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    render_app_bar()
    render_app_iframe()


main()
