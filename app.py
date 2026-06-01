"""Bandabi AI native Streamlit prototype.

This file intentionally keeps the current prototype self-contained:
Streamlit Cloud can run it with only ``python -m streamlit run app.py``.
External services and real authentication are not invoked in this UI-first build.
"""

from __future__ import annotations

import html
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any
from urllib.parse import quote, urlencode

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover - Streamlit can still render without charts.
    pd = None

import engine_bridge


st.set_page_config(page_title="반다비 AI", page_icon="🐻", layout="wide", initial_sidebar_state="collapsed")


PRETENDARD_STACK = (
    '"Pretendard Local", "Pretendard Variable", Pretendard, '
    '"Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif'
)

USER_ROLE = "B2C"
ADMIN_ROLE = "B2G"
DEFAULT_DESTINATION = "김포 반다비체육센터"
UNAVAILABLE_DESTINATION = "김포 제2 반다비 교육거점"
UNAVAILABLE_MESSAGE = (
    "김포 제2 반다비 교육거점은 아직 등록되지 않은 예정 시설입니다. "
    "현재는 김포 반다비체육센터 기준으로 이용해 주세요."
)

SUPPORT_TYPES = [
    "휠체어 이용 또는 보행 보조 필요",
    "시각 정보 접근 지원 필요",
    "청각 안내 지원 필요",
    "천천히 단계별 안내 필요",
]

INSTRUCTORS = [
    {
        "name": "박강훈",
        "summary": "수중 생활체육 · 보행 보조 및 휠체어 이용 지원 경험",
        "time": "화·목 10:00",
        "group": "4명 소그룹",
    },
    {
        "name": "이서연",
        "summary": "소규모 순환운동 · 단계별 설명과 쉬운 동작 변형 중심",
        "time": "월·수 14:00",
        "group": "3명 소그룹",
    },
    {
        "name": "정민재",
        "summary": "기초 체력 및 균형 운동 · 보호자 공유 리포트 경험",
        "time": "금 16:00",
        "group": "1:1 사전 상담 후 소그룹",
    },
]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_bt(value: int | float) -> str:
    return f"{int(value):,}BT"


def bandabi_icon_data_uri() -> str:
    svg_path = Path(__file__).resolve().parent / "assets" / "img" / "icon.svg"
    try:
        svg = svg_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    svg = svg.replace("#7770FF", "#4a2d7a").replace("#DAD8FF", "#d9d3ef")
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def pretendard_font_data_uri() -> str:
    font_path = Path(__file__).resolve().parent / "assets" / "fonts" / "PretendardVariable.ttf"
    try:
        raw = font_path.read_bytes()
    except OSError:
        return ""
    return "data:font/ttf;base64," + base64.b64encode(raw).decode("ascii")


def zap_icon_data_uri() -> str:
    svg_path = Path(__file__).resolve().parent / "assets" / "img" / "zap.svg"
    try:
        svg = svg_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    svg = svg.replace("currentColor", "#ffffff")
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def html_block(markup: str) -> str:
    return " ".join(line.strip() for line in dedent(markup).splitlines() if line.strip())


def init_state() -> None:
    defaults: dict[str, Any] = {
        "logged_in": False,
        "authenticated": False,
        "auth_stage": "entry",
        "auth_mode": "로그인",
        "user_name": "",
        "user_email": "",
        "role": USER_ROLE,
        "bt_points": 3500,
        "bt_balance": 3500,
        "current_page": "main",
        "main_step": "start",
        "route_result": None,
        "route_analysis_result": None,
        "buddy_confirmed": False,
        "class_confirmed": False,
        "selected_schedule": None,
        "accessibility_report": None,
        "vision_result": None,
        "origin": "",
        "destination": DEFAULT_DESTINATION,
        "destination_choice": DEFAULT_DESTINATION,
        "support_type": SUPPORT_TYPES[0],
        "guardian_notify": True,
        "buddy_matching": True,
        "class_recommendation": True,
        "report_receive": True,
        "route_points_awarded": False,
        "report_points_awarded": False,
        "accessibility_points_awarded": False,
        "report_saved": False,
        "guardian_summary": "",
        "instructor_index": 0,
        "schedule_recommendations": [],
        "schedule_generated": False,
        "schedule_day_label": "화·목 중심",
        "schedule_time_label": "오전 10시 전후",
        "schedule_selected_time": "",
        "schedule_top_pick": "",
        "dashboard_log_lines": [
            "[10:04:01] 김포 반다비 운영 데이터 수집 완료",
            "[10:04:04] 지도자 유휴·이동지원 지연·접근성 제보 통합 분석 대기",
        ],
        "pending_confirm": None,
        "center_warning": False,
        "notice": "",
        "high_contrast": False,
        "vision_last_report_type": "점자블록",
        "access_facility_type": "점자블록",
        "access_disability_focus": "시각 정보 접근 지원 필요",
        "access_issue_choices": [],
        "access_analysis": None,
        "access_last_submission": None,
        "access_show_draft": False,
        "access_recent_reports": [
            {
                "id": "RPT-2401",
                "facility": "점자블록",
                "location": "1층 로비",
                "grade": "점검 필요",
                "score": 78,
                "status": "검토 필요",
            },
            {
                "id": "RPT-2398",
                "facility": "접근 가능한 화장실",
                "location": "2층",
                "grade": "양호",
                "score": 42,
                "status": "조치 완료 · 운영기관 확인 완료",
            },
        ],
        "auth_name": "",
        "auth_email": "",
        "auth_password": "",
        "auth_password_confirm": "",
        "signup_role_choice": "이용자 (User)",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    qp = st.query_params
    if qp.get("resume") == "1":
        st.session_state.logged_in = True
        st.session_state.authenticated = True
        st.session_state.user_name = qp.get("user", st.session_state.get("user_name", "")) or "안소연"
        st.session_state.user_email = qp.get("email", st.session_state.get("user_email", ""))
        role_qp = qp.get("role")
        if role_qp == ADMIN_ROLE:
            st.session_state.role = ADMIN_ROLE
        elif role_qp == USER_ROLE:
            st.session_state.role = USER_ROLE
        if not st.session_state.get("_resume_nav_loaded"):
            st.session_state._resume_nav_loaded = True
            page = qp.get("page", "main")
            st.session_state.current_page = (
                page if page in {"main", "schedule", "accessibility", "dashboard"} else "main"
            )
            step = qp.get("step", "start")
            if step == "buddy":
                step = "care"
            st.session_state.main_step = (
                step if step in {"start", "route", "care", "class", "report", "guardian"} else "start"
            )

    if st.session_state.get("destination") == UNAVAILABLE_DESTINATION:
        st.session_state.destination = DEFAULT_DESTINATION
    if st.session_state.get("destination_choice") == UNAVAILABLE_DESTINATION:
        st.session_state.destination_choice = DEFAULT_DESTINATION


def inject_css() -> None:
    high = bool(st.session_state.get("high_contrast"))
    bg = "#000000" if high else "#e8e2f4"
    card = "#000000" if high else "#ffffff"
    surface = "#000000" if high else "#f0ecf8"
    ink = "#16121f" if high else "#2d2040"
    mid = "#4a4656" if high else "#7868a0"

    font_data_uri = pretendard_font_data_uri()
    font_face = (
        f"""
        @font-face {{
            font-family: "Pretendard Local";
            src: url("{font_data_uri}") format("truetype");
            font-weight: 45 920;
            font-style: normal;
            font-display: swap;
        }}
        """
        if font_data_uri
        else ""
    )

    zap_uri = zap_icon_data_uri()
    st.markdown(
        f"""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');
        {font_face}
        :root {{
            --bandabi-bg: {bg};
            --bandabi-card: {card};
            --bandabi-surface: {surface};
            --bandabi-ink: {ink};
            --bandabi-mid: {mid};
            --bandabi-lav: #b8acd8;
            --bandabi-line: rgba(119, 96, 160, .24);
            --bandabi-accent: #4a2d7a;
            --bandabi-accent-2: #6b4fa0;
            --bandabi-green: #2f8a58;
            --bandabi-danger: #9d3654;
        }}

        #MainMenu, footer {{ visibility: hidden; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        .stApp {{
            background: var(--bandabi-bg);
            color: var(--bandabi-ink);
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", "Apple SD Gothic Neo",
                "Malgun Gothic", system-ui, sans-serif;
            font-optical-sizing: auto;
            -webkit-font-smoothing: antialiased;
            text-rendering: geometricPrecision;
            overflow-x: hidden;
        }}
        .block-container {{
            max-width: 1360px;
            padding-top: .85rem;
            padding-bottom: 5rem;
        }}
        .block-container:has(.auth-entry-page),
        .block-container:has(.auth-form-page) {{
            padding-top: 0.5rem;
            padding-bottom: 2.5rem;
        }}
        h1, h2, h3, p, label, span, div, a, button, input, select, textarea, li, td, th {{
            font-family: "Pretendard Local", "Pretendard Variable", Pretendard, "Apple SD Gothic Neo",
                "Malgun Gothic", system-ui, sans-serif !important;
            letter-spacing: 0;
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stSelectbox"],
        [data-testid="stMultiSelect"],
        [data-testid="stTextInput"],
        [data-testid="stTextArea"],
        [data-testid="stFileUploader"],
        [data-testid="stExpander"],
        [data-testid="stButton"],
        [data-testid="stCheckbox"],
        [data-baseweb="select"],
        [data-baseweb="input"],
        [data-baseweb="textarea"],
        [data-baseweb="popover"] {{
            font-family: "Pretendard Local", "Pretendard Variable", Pretendard, "Apple SD Gothic Neo",
                "Malgun Gothic", system-ui, sans-serif !important;
        }}
        .material-icons,
        .material-icons-outlined,
        .material-icons-round,
        .material-symbols-outlined,
        .material-symbols-rounded,
        .material-symbols-sharp,
        [class*="material-icons"],
        [class*="material-symbols"] {{
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons", sans-serif !important;
            font-weight: normal !important;
            font-style: normal !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: "liga" !important;
            -webkit-font-smoothing: antialiased !important;
            font-feature-settings: "liga" !important;
        }}
        [data-baseweb="select"] [data-baseweb="icon"] {{
            width: 18px !important;
            height: 18px !important;
            min-width: 18px !important;
            font-size: 0 !important;
            display: grid !important;
            place-items: center !important;
            color: transparent !important;
        }}
        [data-baseweb="select"] [data-baseweb="icon"]::before {{
            content: "";
            width: 14px;
            height: 14px;
            background: #7c5fb8;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") center / contain no-repeat;
        }}
        [data-baseweb="select"] [data-baseweb="icon"] svg {{
            display: none !important;
        }}
        .bandabi-header {{
            position: sticky;
            top: 0;
            z-index: 20;
            background: rgba(232,226,244,.94);
            backdrop-filter: blur(14px);
            border: 1px solid var(--bandabi-line);
            border-radius: 16px;
            padding: 14px 18px;
            box-shadow: 0 8px 24px rgba(109,40,217,.08);
            margin-bottom: 10px;
        }}
        .brand-mark {{
            display: inline-flex;
            width: 46px;
            height: 46px;
            align-items: center;
            justify-content: center;
            border-radius: 14px;
            background: var(--bandabi-accent);
            color: #fff;
            font-weight: 900;
            font-size: 18px;
            margin-right: 12px;
            box-shadow: 0 4px 14px rgba(109,40,217,.18);
        }}
        .brand-title {{
            color: var(--bandabi-ink);
            font-size: 18px;
            line-height: 1.1;
            font-weight: 900;
            margin: 0;
        }}
        .brand-subtitle {{
            color: var(--bandabi-mid);
            font-size: 12px;
            margin-top: 4px;
            line-height: 1.55;
            font-weight: 700;
        }}
        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }}
        .chip {{
            display: inline-flex;
            align-items: center;
            min-height: 32px;
            border-radius: 999px;
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            color: var(--bandabi-accent);
            padding: 5px 11px;
            font-size: 11px;
            font-weight: 800;
        }}
        .section-card, .metric-card, .soft-card, .auth-card {{
            background: var(--bandabi-card);
            border: 1px solid var(--bandabi-line);
            border-radius: 18px;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 8px 24px rgba(109,40,217,.09),
                0 1px 0 rgba(255,255,255,.90) inset;
        }}
        .section-card {{
            padding: 24px;
            margin: 12px 0 14px;
        }}
        .soft-card {{
            padding: 18px;
            min-height: 122px;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .soft-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 16px 40px rgba(109,40,217,.14);
        }}
        .metric-card {{
            padding: 16px;
            min-height: 112px;
        }}
        .tiny-label {{
            color: var(--bandabi-accent-2);
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 0 0 8px;
        }}
        .section-title {{
            color: var(--bandabi-ink);
            font-family: {PRETENDARD_STACK} !important;
            font-variation-settings: "wght" 900;
            font-weight: 900;
            font-size: clamp(24px, 2.4vw, 30px);
            line-height: 1.12;
            margin: 0;
        }}
        .section-copy {{
            color: var(--bandabi-mid);
            font-size: 13px;
            line-height: 1.65;
            margin: 10px 0 0;
        }}
        .metric-label {{
            color: var(--bandabi-mid);
            font-size: 12px;
            font-weight: 800;
            margin-bottom: 14px;
        }}
        .metric-value {{
            color: var(--bandabi-ink);
            font-size: 24px;
            font-weight: 900;
            line-height: 1.08;
        }}
        .metric-caption {{
            color: var(--bandabi-mid);
            font-size: 12px;
            line-height: 1.55;
            margin-top: 10px;
        }}
        .flow-steps {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0 16px;
        }}
        .flow-step {{
            border-radius: 14px;
            border: 1px solid var(--bandabi-line);
            background: var(--bandabi-surface);
            color: var(--bandabi-mid);
            padding: 10px 12px;
            font-size: 12px;
            font-weight: 800;
        }}
        .flow-step.active {{
            background: var(--bandabi-accent);
            color: #fff;
            box-shadow: 0 8px 22px rgba(74,45,122,.28);
        }}
        .flow-step.done {{
            background: rgba(184,172,216,.28);
            color: var(--bandabi-accent);
        }}
        .notice-box {{
            border-radius: 18px;
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            color: var(--bandabi-mid);
            padding: 15px 16px;
            font-size: 12px;
            line-height: 1.7;
        }}
        .auth-card {{
            padding: 0;
            margin-top: 0;
        }}
        .auth-entry-page {{
            min-height: calc(100vh - 96px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px 0 40px;
            box-sizing: border-box;
        }}
        .auth-entry-card {{
            box-sizing: border-box;
            width: min(540px, calc(100vw - 36px));
            min-height: 598px;
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.18);
            border-radius: 20px;
            padding: 34px 34px 31px;
            box-shadow: 0 24px 60px rgba(74,45,122,.115);
        }}
        .auth-entry-head {{
            display: flex;
            align-items: center;
            gap: 24px;
            margin-bottom: 34px;
        }}
        .auth-entry-copy {{
            padding-top: 2px;
            word-break: keep-all;
        }}
        .auth-entry-logo {{
            width: 96px;
            height: 96px;
            flex: 0 0 96px;
            display: block;
            border-radius: 21px;
        }}
        .auth-entry-title {{
            margin: 0;
            color: #2d2040;
            font-family: {PRETENDARD_STACK};
            font-size: 30px;
            line-height: 1.05;
            font-weight: 900;
        }}
        .auth-entry-sub {{
            margin: 17px 0 0 !important;
            color: #7868a0;
            font-size: 14px !important;
            line-height: 1.65 !important;
            font-weight: 300 !important;
            word-break: keep-all;
        }}
        .auth-choice {{
            position: relative;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            gap: 18px;
            min-height: 96px;
            width: 100%;
            border-radius: 16px;
            padding: 18px 20px;
            text-decoration: none !important;
            transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        }}
        .auth-choice + .auth-choice {{
            margin-top: 16px;
        }}
        .auth-choice:hover {{
            transform: translateY(-2px);
        }}
        .auth-choice.primary {{
            background: #4a2d7a;
            color: #fff !important;
            border: 1px solid #4a2d7a;
            box-shadow: 0 13px 27px rgba(74,45,122,.31);
        }}
        .auth-choice.secondary {{
            background: #fff;
            border: 1px solid rgba(184,172,216,.26);
            color: #2d2040 !important;
            box-shadow: 0 10px 24px rgba(109,40,217,.075);
        }}
        .auth-choice-icon {{
            width: 58px;
            height: 58px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 58px;
        }}
        .auth-choice.primary .auth-choice-icon {{
            background: rgba(255,255,255,.15);
            color: #ffffff;
        }}
        .auth-choice.secondary .auth-choice-icon {{
            background: #f0e3ff;
            color: #4a2d7a;
        }}
        .auth-choice-text {{
            display: block;
            padding-top: 1px;
            word-break: keep-all;
        }}
        .auth-choice-title {{
            display: block;
            font-family: {PRETENDARD_STACK};
            font-size: 20px;
            line-height: 1.2;
            font-weight: 900;
            color: inherit;
        }}
        .auth-choice-desc {{
            display: block;
            margin-top: 5px;
            font-size: 14px;
            line-height: 1.38;
            font-weight: 300;
            color: inherit;
        }}
        .auth-choice.secondary .auth-choice-desc {{
            color: #7868a0;
        }}
        .auth-notice {{
            margin-top: 26px;
            border-radius: 14px;
            border: 1px solid rgba(184,172,216,.32);
            background: #f0ecf8;
            color: #7868a0;
            padding: 15px 17px 15px;
            font-size: 12px;
            line-height: 1.72;
            font-weight: 300;
            word-break: keep-all;
        }}
        .auth-notice-title {{
            display: block;
            color: #4a2d7a;
            font-size: 13px;
            line-height: 1.35;
            font-weight: 900;
            margin-bottom: 6px;
        }}
        .auth-footnote {{
            margin: 0 auto !important;
            padding-top: 14px;
            width: 100%;
            color: #7868a0;
            text-align: center;
            font-size: 11px !important;
            line-height: 1.65 !important;
            font-weight: 200 !important;
            word-break: keep-all;
            white-space: nowrap !important;
        }}
        .auth-form-card {{
            box-sizing: border-box;
            width: min(540px, calc(100vw - 36px));
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.18);
            border-radius: 20px;
            padding: 34px 34px 28px;
            box-shadow: 0 24px 60px rgba(74,45,122,.115);
            font-family: {PRETENDARD_STACK};
        }}
        .auth-form-page {{
            min-height: calc(100vh - 96px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px 0 40px;
            box-sizing: border-box;
        }}
        .auth-form-head {{
            display: flex;
            align-items: flex-start;
            gap: 24px;
            margin-bottom: 28px;
        }}
        .auth-form-logo {{
            width: 96px;
            height: 96px;
            flex: 0 0 96px;
            display: block;
            border-radius: 21px;
        }}
        .auth-form-copy {{
            padding-top: 3px;
            word-break: keep-all;
        }}
        .auth-form-title {{
            margin: 0;
            color: #4a2d7a;
            font-family: {PRETENDARD_STACK};
            font-size: 30px;
            line-height: 1.05;
            font-weight: 900;
        }}
        .auth-form-sub {{
            margin: 36px 0 0 !important;
            color: #7868a0;
            font-size: 14px !important;
            line-height: 1.65 !important;
            font-weight: 300 !important;
            word-break: keep-all;
        }}
        .signup-panel-title {{
            margin: 0;
            color: #4a2d7a;
            font-size: 20px;
            line-height: 1.25;
            font-weight: 900;
        }}
        .signup-panel-copy {{
            margin: 10px 0 26px !important;
            color: #7868a0;
            font-size: 13px !important;
            line-height: 1.55 !important;
            font-weight: 300 !important;
            word-break: keep-all;
        }}
        .signup-panel {{
            box-sizing: border-box;
            width: 100%;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.34);
            border-radius: 16px;
            padding: 24px 20px 22px;
        }}
        .signup-field {{
            display: block;
            margin-top: 22px;
        }}
        .signup-panel .signup-field:first-of-type {{
            margin-top: 0;
        }}
        .signup-label {{
            display: block;
            margin: 0 0 14px;
            color: #7868a0;
            font-size: 13px;
            line-height: 1.25;
            font-weight: 900;
        }}
        .signup-input {{
            box-sizing: border-box;
            width: 100%;
            height: 54px;
            border: 0;
            border-radius: 12px;
            background: #ffffff;
            padding: 0 20px;
            color: #4a2d7a;
            font-family: {PRETENDARD_STACK};
            font-size: 16px;
            font-weight: 300;
            outline: none;
            box-shadow: none;
        }}
        .signup-input::placeholder {{
            color: #b8acd8;
            opacity: 1;
            font-weight: 300;
        }}
        .signup-role-links {{
            display: flex;
            gap: 8px;
        }}
        .signup-role-link {{
            box-sizing: border-box;
            flex: 1 1 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 48px;
            border-radius: 12px;
            border: 1px solid rgba(184,172,216,.34);
            background: #ffffff;
            color: #7868a0 !important;
            font-size: 14px;
            font-weight: 800;
            text-decoration: none !important;
        }}
        .signup-role-link.active {{
            background: #4a2d7a;
            color: #ffffff !important;
            border-color: #4a2d7a;
            box-shadow: 0 8px 18px rgba(74,45,122,.22);
        }}
        .role-select-panel {{
            margin-top: 20px;
        }}
        .role-select-kicker {{
            margin: 0 0 12px;
            color: #7868a0;
            font-size: 11px;
            line-height: 1.2;
            font-weight: 900;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .role-select-card {{
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-top: 10px;
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid rgba(184,172,216,.34);
            background: #ffffff;
            color: #4a2d7a !important;
            text-decoration: none !important;
            box-shadow: 0 10px 24px rgba(74,45,122,.06);
        }}
        .role-select-card:first-of-type {{
            margin-top: 0;
        }}
        .role-select-card:hover {{
            border-color: rgba(74,45,122,.42);
            box-shadow: 0 12px 28px rgba(74,45,122,.12);
        }}
        .role-select-card-inner {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .role-select-icon {{
            width: 48px;
            height: 48px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .role-select-icon.user {{
            background: rgba(59,130,246,.12);
            color: #2563eb;
        }}
        .role-select-icon.admin {{
            background: rgba(109,49,237,.12);
            color: #6d31ed;
        }}
        .role-select-title {{
            margin: 0;
            font-size: 16px;
            font-weight: 900;
            color: #4a2d7a;
        }}
        .role-select-copy {{
            margin: 4px 0 0 !important;
            font-size: 12px !important;
            line-height: 1.45 !important;
            font-weight: 300 !important;
            color: #7868a0 !important;
        }}
        .role-select-back {{
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 55px;
            margin-top: 14px;
            border-radius: 12px;
            border: 1px solid rgba(184,172,216,.34);
            background: #f0ecf8;
            color: #4a2d7a !important;
            font-size: 16px;
            font-weight: 900;
            text-decoration: none !important;
        }}
        .auth-form-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        .auth-form-action,
        button.auth-form-action {{
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 1 1 0;
            height: 55px;
            border-radius: 12px;
            text-decoration: none !important;
            font-family: {PRETENDARD_STACK};
            font-size: 16px;
            font-weight: 900;
            cursor: pointer;
        }}
        button.auth-form-action {{
            width: 100%;
            appearance: none;
            -webkit-appearance: none;
        }}
        .auth-form-action.back {{
            background: #f0ecf8;
            color: #4a2d7a;
            border: 1px solid rgba(184,172,216,.34);
            box-shadow: none;
        }}
        .auth-form-action.next {{
            background: #4a2d7a;
            color: #ffffff;
            border: 1px solid #4a2d7a;
            box-shadow: 0 12px 24px rgba(74,45,122,.28);
        }}
        .auth-form-notice {{
            margin-top: 22px;
        }}
        .auth-form-card .auth-notice,
        .auth-form-card .auth-notice-title,
        .auth-form-card .auth-footnote {{
            color: #7868a0;
        }}
        .auth-form-card .auth-notice-title {{
            color: #4a2d7a;
        }}
        .signup-role-radio [data-testid="stRadio"] > div {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .signup-role-radio [data-testid="stRadio"] label {{
            min-width: calc(50% - 4px);
            flex: 1 1 calc(50% - 4px);
            justify-content: center;
            min-height: 48px;
            border-radius: 12px;
            border: 1px solid rgba(184,172,216,.34) !important;
            background: #ffffff;
            color: #7868a0 !important;
            font-weight: 800 !important;
            margin: 0 !important;
            padding: 10px 12px !important;
        }}
        .signup-role-radio [data-testid="stRadio"] label:has(input:checked) {{
            background: #4a2d7a !important;
            color: #ffffff !important;
            border-color: #4a2d7a !important;
            box-shadow: 0 8px 18px rgba(74,45,122,.22);
        }}
        .signup-role-radio [data-testid="stRadio"] label > div:first-child {{
            display: none;
        }}
        .auth-form-btn-row {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
            align-items: stretch;
        }}
        .auth-form-btn-row .stButton {{
            flex: 1 1 0;
            margin: 0;
        }}
        .auth-form-btn-row .stButton > button {{
            width: 100%;
            min-height: 55px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 900;
            box-shadow: none;
        }}
        .st-key-auth_signup_continue > button,
        .st-key-auth_login_continue > button {{
            background: #4a2d7a !important;
            color: #ffffff !important;
            border: 1px solid #4a2d7a !important;
            box-shadow: 0 12px 24px rgba(74,45,122,.28) !important;
        }}
        .st-key-role_pick_user > button,
        .st-key-role_pick_admin > button {{
            min-height: 108px;
            border-radius: 16px !important;
            border: 1px solid rgba(184,172,216,.34) !important;
            background: #ffffff !important;
            color: #4a2d7a !important;
            font-weight: 900 !important;
            line-height: 1.45 !important;
            white-space: pre-line !important;
        }}
        .st-key-role_pick_user > button:hover,
        .st-key-role_pick_admin > button:hover {{
            border-color: #4a2d7a !important;
            box-shadow: 0 10px 20px rgba(74,45,122,.16) !important;
        }}
        @media (max-width: 640px) {{
            .auth-entry-card, .auth-form-card {{
                padding: 26px 18px 24px;
            }}
            .auth-entry-head {{
                gap: 16px;
                margin-bottom: 26px;
            }}
            .auth-entry-logo {{
                width: 76px;
                height: 76px;
                flex-basis: 76px;
            }}
            .auth-entry-title {{
                font-size: 24px;
            }}
            .auth-form-head {{
                gap: 16px;
                margin-bottom: 26px;
            }}
            .auth-form-logo {{
                width: 76px;
                height: 76px;
                flex-basis: 76px;
            }}
            .auth-form-title {{
                font-size: 24px;
            }}
            .auth-form-sub {{
                margin-top: 18px !important;
                font-size: 13px !important;
            }}
            .auth-entry-sub {{
                margin-top: 10px;
                font-size: 13px;
            }}
            .auth-choice {{
                min-height: 88px;
                padding: 16px;
            }}
            .auth-footnote {{
                width: 94%;
                white-space: normal;
            }}
        }}
        .stButton > button {{
            min-height: 42px;
            border-radius: 12px;
            border: 1px solid rgba(74,45,122,.22);
            background: #ffffff;
            color: var(--bandabi-ink);
            font-weight: 800;
            box-shadow: none;
            white-space: normal;
            line-height: 1.25;
        }}
        .stButton > button:hover {{
            border-color: rgba(74,45,122,.45);
            color: var(--bandabi-accent);
            transform: translateY(-1px);
        }}
        .stButton > button[kind="primary"] {{
            background: var(--bandabi-accent);
            color: #fff;
            border-color: var(--bandabi-accent);
            box-shadow: 0 4px 14px rgba(109,40,217,.24);
        }}
        .stButton > button[kind="primary"]:hover {{
            background: var(--bandabi-accent-2);
            color: #fff;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
            border-radius: 15px;
            border-color: rgba(119, 96, 160, .26);
            background: #fff;
        }}
        [data-testid="stFileUploader"] {{
            background: rgba(255,255,255,.72);
            border: 1px dashed rgba(119, 96, 160, .35);
            border-radius: 20px;
            padding: 12px;
        }}
        .stAlert {{
            border-radius: 18px;
        }}
        .disclaimer {{
            color: var(--bandabi-mid);
            font-size: 11px;
            line-height: 1.7;
            margin: 2px 0 12px;
        }}
        .journey-shell {{
            max-width: 1380px;
            margin: 0 auto;
        }}
        .tab-shell {{
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            border-radius: 14px;
            padding: 4px;
            margin: 0 0 14px;
            box-shadow: 0 1px 4px rgba(109,40,217,.05);
        }}
        .tab-shell [data-testid="stRadio"] {{
            margin: 0;
        }}
        .tab-shell [data-testid="stRadio"] > div {{
            display: flex;
            flex-wrap: nowrap;
            gap: 4px;
            overflow-x: auto;
        }}
        .tab-shell [data-testid="stRadio"] label {{
            min-width: max-content;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 0;
            border: 1px solid transparent;
            color: var(--bandabi-mid) !important;
            font-weight: 800 !important;
        }}
        .tab-shell [data-testid="stRadio"] label:has(input:checked) {{
            background: var(--bandabi-accent);
            color: #fff !important;
            box-shadow: 0 4px 14px rgba(109,40,217,.22);
        }}
        .tab-shell [data-testid="stRadio"] label:has(input:checked) * {{
            color: #fff !important;
        }}
        .tab-shell [data-testid="stRadio"] label > div:first-child {{
            display: none;
        }}
        .st-key-nav_radio {{
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            border-radius: 14px;
            padding: 4px;
            box-shadow: 0 1px 4px rgba(109,40,217,.05);
            margin-bottom: 14px;
        }}
        .st-key-nav_radio [data-testid="stRadio"] > div:last-child {{
            display: flex;
            flex-wrap: nowrap;
            gap: 4px;
            overflow-x: auto;
        }}
        .st-key-nav_radio label[data-baseweb="radio"] {{
            min-width: max-content;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 0;
            border: 1px solid transparent;
            color: var(--bandabi-mid) !important;
            font-weight: 800 !important;
        }}
        .st-key-nav_radio label[data-baseweb="radio"] > div:first-child {{
            display: none;
        }}
        .st-key-nav_radio label[data-baseweb="radio"]:has(input:checked) {{
            background: var(--bandabi-accent);
            color: #fff !important;
            box-shadow: 0 4px 14px rgba(109,40,217,.22);
        }}
        .st-key-nav_radio label[data-baseweb="radio"]:has(input:checked) * {{
            color: #fff !important;
        }}
        .tab-shell .stButton > button {{
            min-height: 40px;
            border-radius: 10px;
            border-color: transparent;
            background: transparent;
            color: var(--bandabi-mid);
            box-shadow: none;
            font-size: 13px;
            font-weight: 800;
        }}
        .route-map {{
            border-radius: 18px;
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            padding: 10px;
            margin-top: 14px;
        }}
        .route-map text {{
            font-family: {PRETENDARD_STACK} !important;
            letter-spacing: 0 !important;
        }}
        .route-line {{
            stroke-dasharray: 14 10;
            animation: routeDash 1.3s linear infinite;
        }}
        @keyframes routeDash {{
            to {{ stroke-dashoffset: -48; }}
        }}
        .route-warning-panel {{
            margin-top: 14px;
            border-radius: 16px;
            background: rgba(240,236,248,.72);
            border: 1px solid var(--bandabi-line);
            padding: 14px 16px;
        }}
        .route-warning-title {{
            margin: 0 0 9px;
            color: var(--bandabi-ink);
            font-size: 14px;
            font-weight: 900;
        }}
        .route-warning-list {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
            margin: 0;
            padding: 0;
            list-style: none;
        }}
        .route-warning-list li {{
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid rgba(119,96,160,.18);
            color: var(--bandabi-mid);
            font-size: 12px;
            font-weight: 700;
            line-height: 1.55;
            padding: 10px 12px;
        }}
        .route-detail-card {{
            min-height: 178px;
            padding: 16px;
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 18px;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 8px 24px rgba(109,40,217,.09),
                0 1px 0 rgba(255,255,255,.90) inset;
        }}
        .route-detail-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .route-detail-label {{
            color: var(--bandabi-mid);
            font-size: 12px;
            font-weight: 900;
        }}
        .route-detail-badge {{
            display: inline-flex;
            align-items: center;
            min-height: 24px;
            padding: 0 9px;
            border-radius: 999px;
            background: var(--bandabi-surface);
            color: var(--bandabi-accent);
            border: 1px solid var(--bandabi-line);
            font-size: 10px;
            font-weight: 900;
            white-space: nowrap;
        }}
        .route-detail-value {{
            color: var(--bandabi-ink);
            font-size: 20px;
            font-weight: 900;
            line-height: 1.22;
            margin: 0;
        }}
        .route-detail-caption {{
            color: var(--bandabi-mid);
            font-size: 12px;
            line-height: 1.5;
            margin: 8px 0 0;
        }}
        .route-detail-list {{
            margin: 10px 0 0;
            padding-left: 15px;
            color: var(--bandabi-mid);
            font-size: 11px;
            line-height: 1.6;
        }}
        .confirm-action .stButton > button,
        .confirm-action .stButton > button[kind="primary"] {{
            background: #a8e6c4 !important;
            color: #1a5c38 !important;
            border: 1px solid rgba(80,180,120,.25) !important;
            box-shadow: none !important;
        }}
        .st-key-route_plan_banner {{
            border-radius: 32px;
            background: linear-gradient(90deg, #edf8f2 0%, #f0ecf8 100%);
            border: 1px solid rgba(80,180,120,.22);
            padding: 18px 20px 14px;
            margin-top: 14px;
        }}
        .st-key-route_plan_banner [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .st-key-route_plan_banner [data-testid="stHorizontalBlock"] {{
            align-items: center;
            gap: 14px;
        }}
        .route-plan-title {{
            margin: 0;
            font-size: 16px;
            font-weight: 900;
            color: var(--bandabi-ink);
            line-height: 1.35;
        }}
        .route-plan-sub {{
            margin: 6px 0 0;
            font-size: 13px;
            color: var(--bandabi-mid);
            line-height: 1.55;
        }}
        .st-key-route_plan_banner .st-key-route_retry > button {{
            background: #e8e4f0 !important;
            color: #4a2d7a !important;
            border: 1px solid var(--bandabi-line) !important;
            box-shadow: none !important;
            font-weight: 800 !important;
            min-height: 48px;
            border-radius: 16px !important;
        }}
        .st-key-route_plan_banner .confirm-action .stButton > button {{
            min-height: 48px;
            border-radius: 16px !important;
            font-weight: 800 !important;
        }}
        .pending-confirm-actions {{
            margin-top: 22px;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .pending-confirm-btn {{
            min-width: 104px;
            height: 46px;
            padding: 0 18px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none !important;
            font-size: 15px;
            font-weight: 900;
            line-height: 1;
            box-sizing: border-box;
            cursor: pointer;
        }}
        .pending-confirm-btn-cancel {{
            background: #ffffff;
            color: #4a2d7a !important;
            border: 1px solid var(--bandabi-line);
        }}
        .pending-confirm-btn-ok {{
            background: #6d28d9;
            color: #ffffff !important;
            border: 0;
            box-shadow: 0 6px 18px rgba(109,40,217,.24);
        }}
        .st-key-care_action_row,
        .st-key-class_action_row,
        .st-key-pending_action_row {{
            margin-top: 20px;
        }}
        .step-action-links {{
            margin-top: 24px;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 18px;
            width: 100%;
        }}
        .step-action-link {{
            box-sizing: border-box;
            width: 258px;
            min-height: 50px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none !important;
            font-family: {PRETENDARD_STACK};
            font-size: 14px;
            font-weight: 900;
            line-height: 1;
        }}
        .step-action-link.secondary {{
            background: #ffffff;
            color: #2d2040 !important;
            border: 1px solid rgba(184,172,216,.58);
            box-shadow: 0 4px 12px rgba(74,45,122,.04);
        }}
        .step-action-link.primary {{
            background: #4a2d7a;
            color: #ffffff !important;
            border: 1px solid #4a2d7a;
            box-shadow: 0 10px 22px rgba(74,45,122,.28);
        }}
        .st-key-care_action_row [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-class_action_row [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-pending_action_row [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .st-key-care_skip > button,
        .st-key-class_next > button {{
            background: #f43f5e !important;
            color: #fff !important;
            border: 1px solid rgba(244,63,94,.35) !important;
            box-shadow: none !important;
            font-weight: 800 !important;
            min-height: 48px;
            border-radius: 16px !important;
        }}
        .st-key-care_action_row .confirm-action .stButton > button,
        .st-key-class_action_row .confirm-action .stButton > button,
        .st-key-pending_action_row .stButton > button {{
            min-height: 48px;
            border-radius: 16px !important;
            font-weight: 800 !important;
        }}
        .report-native-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-top: 16px;
        }}
        .report-native-card {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 18px;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 8px 24px rgba(109,40,217,.09),
                0 1px 0 rgba(255,255,255,.90) inset;
            padding: 22px 24px;
            min-height: 156px;
        }}
        .report-native-card.wide {{
            grid-column: 1 / -1;
            min-height: 118px;
        }}
        .report-native-label {{
            margin: 0 0 12px;
            color: var(--bandabi-accent-2);
            font-size: 13px;
            font-weight: 900;
            line-height: 1.2;
        }}
        .report-native-value {{
            margin: 0;
            color: var(--bandabi-ink);
            font-size: 34px;
            font-weight: 900;
            line-height: 1.08;
        }}
        .report-native-copy {{
            margin: 12px 0 0;
            color: var(--bandabi-mid);
            font-size: 14px;
            font-weight: 500;
            line-height: 1.65;
        }}
        .report-native-list {{
            margin: 14px 0 0;
            padding: 0;
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .report-native-list li {{
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            border-radius: 999px;
            background: var(--bandabi-surface);
            color: var(--bandabi-accent);
            border: 1px solid var(--bandabi-line);
            padding: 0 11px;
            font-size: 11px;
            font-weight: 900;
        }}
        .st-key-report_action_row {{
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
        }}
        .st-key-report_action_row [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .st-key-report_action_row .stButton {{
            width: 320px;
            margin-left: auto;
        }}
        .st-key-report_action_row .stButton > button {{
            min-height: 52px;
            border-radius: 16px !important;
            background: #4a2d7a !important;
            border: 1px solid #4a2d7a !important;
            color: #ffffff !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 22px rgba(74,45,122,.28) !important;
        }}
        .user-topbar-brand .brand-logo-shell,
        .user-header .brand-logo-shell {{
            width: 62px;
            height: 62px;
            border-radius: 20px;
            overflow: hidden;
            background: #4a2d7a;
            flex: 0 0 62px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .user-topbar-brand .brand-logo-img,
        .user-header .brand-logo-img {{
            width: 100%;
            height: 100%;
            display: block;
            object-fit: cover;
        }}
        .user-topbar-shell {{
            width: 100vw;
            max-width: 100vw;
            margin-left: calc(50% - 50vw);
            margin-right: calc(50% - 50vw);
            margin-top: -0.85rem;
            margin-bottom: 14px;
            position: sticky;
            top: 0;
            z-index: 40;
        }}
        .user-topbar {{
            background: rgba(236, 232, 246, .92);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(180, 166, 214, .42);
            box-shadow: none;
        }}
        .user-topbar-inner {{
            max-width: 1360px;
            margin: 0 auto;
            padding: 12px 18px;
            display: flex;
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
        }}
        .user-topbar-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
            flex: 0 0 auto;
        }}
        .user-topbar-copy {{
            min-width: 0;
        }}
        .user-topbar-title {{
            margin: 0;
            font-size: 18px;
            line-height: 1.2;
            white-space: nowrap;
        }}
        .user-topbar-title-main {{
            color: #4e3688;
            font-weight: 900;
            letter-spacing: 0;
        }}
        .user-topbar-title-user {{
            color: #7a67a7;
            font-size: 14px;
            font-weight: 800;
            margin-left: 4px;
        }}
        .user-topbar-badges {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
        }}
        .topbar-badge {{
            display: inline-flex;
            align-items: center;
            min-height: 28px;
            border-radius: 14px;
            background: rgba(240,236,248,.9);
            border: 1px solid rgba(184, 172, 216, .4);
            color: #725e9f;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 800;
            white-space: nowrap;
            gap: 5px;
        }}
        .topbar-badge-token small {{
            color: #8f7db7;
            font-size: 10px;
            font-weight: 800;
        }}
        .topbar-badge-token svg {{
            width: 15px;
            height: 15px;
        }}
        .user-topbar-nav {{
            overflow-x: auto;
            padding: 2px 0;
            flex: 1 1 640px;
            display: flex;
            justify-content: center;
        }}
        .app-tab-track {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            width: 100%;
            max-width: 640px;
            background: rgba(240,236,248,.9);
            border: 1px solid rgba(184, 172, 216, .4);
            border-radius: 16px;
            padding: 4px;
            box-shadow: none;
        }}
        .app-tab {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            flex: 1 1 0;
            justify-content: center;
            min-height: 48px;
            border-radius: 10px;
            padding: 0 14px;
            color: #6f5a98 !important;
            font-size: 14px;
            font-weight: 900 !important;
            line-height: 1.2;
            text-decoration: none !important;
            white-space: nowrap;
            transition: background .15s ease, color .15s ease, box-shadow .15s ease;
        }}
        .app-tab svg {{
            flex: 0 0 18px;
            width: 18px;
            height: 18px;
            stroke-width: 2.35;
        }}
        .app-tab.active {{
            background: #4a2d7a;
            color: #ffffff !important;
            font-weight: 700;
            box-shadow: 0 4px 14px rgba(109, 40, 217, .22);
        }}
        .app-tab.active svg {{
            color: #ffffff;
        }}
        .user-topbar-tools {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            flex: 0 0 auto;
        }}
        .app-tool-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            min-height: 40px;
            border-radius: 14px;
            background: rgba(240,236,248,.9);
            border: 1px solid rgba(184, 172, 216, .4);
            color: #7868a0 !important;
            padding: 0 14px;
            font-size: 14px;
            font-weight: 800;
            text-decoration: none !important;
            white-space: nowrap;
            transition: border-color .15s ease, color .15s ease;
        }}
        .app-tool-btn:hover {{
            border-color: rgba(74, 45, 122, .34);
            color: #4a2d7a !important;
        }}
        .app-tool-btn.icon-only {{
            width: 40px;
            padding: 0;
        }}
        .app-tool-btn svg {{
            display: block;
            width: 17px;
            height: 17px;
        }}
        @media (min-width: 981px) {{
            .user-topbar-inner {{
                flex-direction: row;
                align-items: center;
                justify-content: space-between;
            }}
        }}
        @media (max-width: 640px) {{
            .user-topbar-title {{
                font-size: 16px;
                white-space: normal;
            }}
            .user-topbar-title-user {{
                font-size: 13px;
            }}
            .topbar-badge {{
                font-size: 11px;
            }}
            .topbar-badge-token small {{
                font-size: 10px;
            }}
            .app-tab {{
                flex: 0 0 auto;
                padding: 0 11px;
                font-size: 12px;
            }}
            .app-tool-btn {{
                font-size: 13px;
            }}
        }}
        .start-screen {{
            width: 100%;
        }}
        .st-key-start_shell {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 32px;
            padding: 34px 38px 30px;
            max-width: 1040px;
            margin: 0 auto;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 10px 28px rgba(109,40,217,.10),
                0 1px 0 rgba(255,255,255,.92) inset;
        }}
        .st-key-start_shell [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .start-card {{
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
        }}
        .start-kicker {{
            color: #6b4fa0;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 0;
        }}
        .start-greeting {{
            color: #2d2040 !important;
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", sans-serif !important;
            font-size: 50px !important;
            font-weight: 900 !important;
            line-height: 1.08;
            letter-spacing: -0.02em !important;
            margin: 14px 0 0;
        }}
        .start-lead {{
            color: #2d2040;
            font-size: 18px;
            line-height: 1.5;
            font-weight: 300;
            margin: 16px 0 0;
        }}
        .start-copy {{
            color: #b8acd8;
            font-size: 13px;
            line-height: 1.65;
            font-weight: 240;
            margin: 10px 0 0;
        }}
        .start-grid-shell {{
            margin-top: 34px;
        }}
        .start-label {{
            display: block;
            color: #7868a0;
            font-size: 13px;
            font-weight: 800;
            margin: 0 0 10px;
        }}
        .start-fields [data-testid="stSelectbox"],
        .start-fields [data-testid="stTextInput"] {{
            margin-bottom: 14px;
        }}
        .start-fields [data-testid="stSelectbox"] label,
        .start-fields [data-testid="stTextInput"] label {{
            display: none;
        }}
        .start-fields [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        .start-fields [data-testid="stTextInput"] input {{
            min-height: 58px;
            border-radius: 16px;
            border-color: rgba(119, 96, 160, .22);
            background: #fff;
            color: #4a2d7a;
            font-size: 15px;
            font-weight: 500;
        }}
        .start-fields [data-testid="stTextInput"] input::placeholder {{
            color: #b7abcf;
            opacity: 1;
            font-weight: 500;
        }}
        .start-tile-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }}
        .start-tile {{
            min-height: 64px;
            border-radius: 16px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.22);
            color: #4a2d7a;
            font-size: 15px;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 14px 10px;
        }}
        .start-action-wrap {{
            margin-top: 12px;
        }}
        .start-ai-link {{
            height: 82px;
            min-height: 82px;
            max-height: 82px;
            border-radius: 22px;
            font-size: 22px;
            font-weight: 900 !important;
            letter-spacing: 0;
            box-shadow: 0 12px 24px rgba(74,45,122,.28);
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            background: #4a2d7a;
            color: #fff !important;
            text-decoration: none !important;
            width: 100%;
            box-sizing: border-box;
            line-height: 1;
        }}
        .start-ai-icon {{
            width: 26px;
            height: 26px;
            display: block;
            flex: 0 0 26px;
        }}
        .st-key-btn_ai_start > button {{
            min-height: 82px;
            border-radius: 22px;
            font-size: 22px;
            font-weight: 900;
            letter-spacing: 0;
            box-shadow: 0 12px 24px rgba(74,45,122,.28);
            padding-top: 18px;
            padding-bottom: 18px;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 10px !important;
        }}
        .st-key-btn_ai_start > button p {{
            font-size: 22px;
            font-weight: 900;
            margin: 0;
            line-height: 1;
        }}
        .st-key-btn_ai_start button[kind="primary"] {{
            min-height: 82px !important;
        }}
        .st-key-btn_ai_start > button::before {{
            content: "";
            display: inline-block;
            width: 26px;
            height: 26px;
            background-image: url("{zap_uri}");
            background-repeat: no-repeat;
            background-size: contain;
            background-position: center;
            flex: 0 0 26px;
        }}
        .start-footnote {{
            color: #b8acd8;
            font-size: 12px;
            line-height: 1.65;
            font-weight: 300;
            margin: 30px 0 0;
        }}
        .st-key-schedule_shell {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 30px;
            padding: 30px 30px 28px;
            max-width: 1380px;
            width: min(1380px, calc(100vw - 330px));
            margin: 5px auto 0;
            position: relative;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 20px rgba(109,40,217,.07);
        }}
        .schedule-kicker {{
            color: #6b4fa0;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: .11em;
            margin: 0;
        }}
        .schedule-title {{
            color: #2d2040 !important;
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", sans-serif !important;
            font-size: 38px !important;
            font-weight: 900 !important;
            letter-spacing: -0.02em !important;
            margin: 4px 0 0;
            line-height: 1.05;
        }}
        .schedule-sub {{
            margin: 12px 0 18px;
            color: #7a6aa1;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.55;
        }}
        .st-key-schedule_find_btn > button {{
            min-height: 58px;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 900;
            white-space: nowrap;
            box-shadow: 0 10px 22px rgba(74,45,122,.22);
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
        }}
        .st-key-schedule_find_btn > button::before {{
            content: "";
            width: 18px;
            height: 18px;
            flex: 0 0 18px;
            background-color: #fff;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.3-4.3'/%3E%3C/svg%3E") center / contain no-repeat;
        }}
        .schedule-find-link {{
            min-height: 58px;
            border-radius: 16px;
            padding: 0 22px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #4a2d7a;
            color: #fff !important;
            text-decoration: none !important;
            border: 0;
            cursor: pointer;
            font-size: 16px;
            font-weight: 900 !important;
            white-space: nowrap;
            box-shadow: 0 10px 22px rgba(74,45,122,.22);
            width: auto;
            min-width: 200px;
            align-self: flex-start;
        }}
        .schedule-find-form {{
            margin: 0;
            display: flex;
            justify-content: flex-end;
        }}
        .schedule-find-link svg {{
            width: 19px;
            height: 19px;
            flex: 0 0 19px;
        }}
        .st-key-schedule_pref_card,
        .st-key-schedule_criteria_card,
        .st-key-schedule_result_card {{
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.22);
            border-radius: 22px;
            padding: 20px;
            box-shadow: none;
        }}
        .st-key-schedule_criteria_card {{
            margin-top: 14px;
        }}
        .st-key-schedule_result_card {{
            min-height: 218px;
        }}
        .schedule-card-title {{
            margin: 0 0 14px;
            color: #2f2350;
            font-size: 18px;
            font-weight: 900;
            line-height: 1.2;
            display: inline-flex;
            align-items: center;
            gap: 9px;
        }}
        .schedule-card-title svg {{
            width: 18px;
            height: 18px;
            color: #4a2d7a;
            flex: 0 0 18px;
        }}
        .schedule-label {{
            display: block;
            color: #7a6aa1;
            font-size: 13px;
            font-weight: 800;
            margin: 10px 0 8px;
        }}
        .st-key-schedule_pref_card [data-testid="stSelectbox"] label {{
            display: none;
        }}
        .st-key-schedule_pref_card [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            min-height: 52px;
            border-radius: 14px;
            border-color: rgba(119, 96, 160, .22);
            background: #fff;
            color: #4a2d7a;
            font-size: 14px;
            font-weight: 500;
        }}
        .schedule-toggle-row {{
            margin-top: 10px;
        }}
        .schedule-criteria-list {{
            color: #5e4f84;
            font-size: 14px;
            line-height: 1.9;
            font-weight: 500;
            margin: 0;
        }}
        .schedule-criteria-list b {{
            color: #3f3068;
            font-weight: 900;
        }}
        .schedule-result-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 2px 0 14px;
        }}
        .schedule-status-chip {{
            display: inline-flex;
            align-items: center;
            min-height: 32px;
            border-radius: 999px;
            border: 1px solid rgba(184,172,216,.35);
            background: #f6f3fc;
            color: #6d5f90;
            font-size: 13px;
            font-weight: 700;
            padding: 0 14px;
        }}
        .schedule-empty {{
            min-height: 210px;
            display: grid;
            place-items: center;
            text-align: center;
            color: #4c3b74;
        }}
        .schedule-empty-icon {{
            width: 44px;
            height: 44px;
            margin: 0 auto 12px;
            color: #344154;
        }}
        .schedule-empty .big {{
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", sans-serif !important;
            font-size: 20px !important;
            font-weight: 900 !important;
            letter-spacing: -0.01em !important;
            line-height: 1.35;
            color: #2f2350;
            max-width: 520px;
        }}
        .schedule-empty .small {{
            margin-top: 8px;
            font-size: 15px;
            color: #8575ad;
            font-weight: 500;
        }}
        .schedule-native-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
        }}
        .schedule-native-head > div:first-child {{
            flex: 1 1 auto;
            min-width: 0;
        }}
        .schedule-native-grid {{
            display: grid;
            grid-template-columns: 5fr 7fr;
            gap: 22px;
            margin-top: 24px;
        }}
        .schedule-left-stack {{
            display: grid;
            gap: 14px;
        }}
        .schedule-soft {{
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 22px;
            padding: 20px;
            box-shadow: none;
        }}
        .schedule-soft-title {{
            margin: 0 0 18px;
            color: #2f2350 !important;
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", sans-serif !important;
            font-size: 20px !important;
            font-weight: 900 !important;
            letter-spacing: -0.01em !important;
            display: flex;
            align-items: center;
            gap: 9px;
            line-height: 1.2;
        }}
        .schedule-soft-title svg {{
            width: 20px;
            height: 20px;
            color: #4a2d7a;
            flex: 0 0 20px;
        }}
        .schedule-field-label {{
            display: block;
            color: #7a6aa1;
            font-size: 12px;
            font-weight: 800;
            margin: 0 0 8px;
        }}
        .schedule-control {{
            width: 100%;
            min-height: 52px;
            border-radius: 14px;
            border: 1px solid rgba(119,96,160,.22);
            background: #fff;
            color: #4a2d7a;
            font-size: 14px;
            font-weight: 500;
            padding: 0 14px;
            margin-bottom: 16px;
            appearance: auto;
        }}
        .schedule-check-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 2px;
        }}
        .schedule-check {{
            min-height: 48px;
            border-radius: 16px;
            background: rgba(255,255,255,.32);
            border: 1px solid rgba(184,172,216,.22);
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 12px;
            color: #5e4f84;
            font-size: 13px;
            font-weight: 600;
        }}
        .schedule-check span:first-child {{
            width: 17px;
            height: 17px;
            border-radius: 5px;
            background: #7c5fb8;
            color: #fff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 900;
        }}
        .schedule-rule-list {{
            color: #6f5d95;
            font-size: 14px;
            line-height: 1.9;
            font-weight: 500;
            margin: 0;
        }}
        .schedule-rule-list b {{
            color: #4a2d7a;
            font-weight: 900;
            margin-right: 4px;
        }}
        .schedule-result-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 2px 0 14px;
        }}
        .schedule-result-panel {{
            min-height: 218px;
            border-radius: 22px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.28);
            display: grid;
            place-items: center;
            text-align: center;
            padding: 28px;
        }}
        .schedule-result-panel.has-results {{
            display: block;
            min-height: 0;
            padding: 0;
            background: transparent;
            border: 0;
            border-radius: 0;
            text-align: left;
        }}
        .schedule-result-card {{
            width: 100%;
            text-align: left;
            background: rgba(255,255,255,.42);
            border: 1px solid rgba(184,172,216,.24);
            border-radius: 18px;
            padding: 14px 16px;
            margin: 8px 0;
            color: #4a2d7a;
            font-size: 14px;
            line-height: 1.5;
        }}
        .schedule-result-stack {{
            display: grid;
            gap: 14px;
        }}
        .schedule-slot-card {{
            display: block;
            width: 100%;
            text-align: left;
            text-decoration: none !important;
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 24px;
            padding: 22px 24px;
            min-height: 145px;
            box-shadow: 0 6px 18px rgba(109,40,217,.08);
            transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
            color: inherit;
        }}
        .schedule-slot-card:hover {{
            border-color: rgba(109,40,217,.34);
            box-shadow: 0 4px 20px rgba(109,40,217,.12);
            transform: translateY(-1px);
        }}
        .schedule-slot-card.primary,
        .schedule-slot-card.selected {{
            border-color: rgba(109,40,217,.34);
        }}
        .schedule-slot-head {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        @media (min-width: 640px) {{
            .schedule-slot-head {{
                flex-direction: row;
                align-items: center;
                justify-content: space-between;
            }}
        }}
        .schedule-slot-rank {{
            margin: 0;
            font-size: 12px;
            font-weight: 900;
        }}
        .schedule-slot-rank.purple {{ color: #6b4fa0; }}
        .schedule-slot-rank.blue {{ color: #5b7fd4; }}
        .schedule-slot-rank.amber {{ color: #b07a20; }}
        .schedule-slot-title {{
            margin: 4px 0 0;
            color: #2d2040;
            font-size: 30px;
            font-weight: 900;
            line-height: 1.15;
        }}
        .schedule-slot-date {{
            font-size: 18px;
            font-weight: 700;
            color: #7a6aa1;
        }}
        .schedule-slot-reason {{
            margin: 8px 0 0;
            color: #7a6aa1;
            font-size: 14px;
            line-height: 1.55;
        }}
        .schedule-slot-badge {{
            display: inline-flex;
            align-items: center;
            min-height: 28px;
            border-radius: 999px;
            padding: 0 12px;
            font-size: 12px;
            font-weight: 900;
            white-space: nowrap;
        }}
        .schedule-slot-badge.good {{
            background: rgba(80,170,120,.14);
            border: 1px solid rgba(80,170,120,.28);
            color: #1f7a52;
        }}
        .schedule-slot-badge.normal {{
            background: rgba(91,127,212,.12);
            border: 1px solid rgba(91,127,212,.24);
            color: #4a2d7a;
        }}
        .schedule-slot-badge.warn {{
            background: rgba(255,196,90,.18);
            border: 1px solid rgba(180,130,40,.22);
            color: #8a5a00;
        }}
        .schedule-optimize-result {{
            margin-top: 16px;
            padding: 21px 22px;
            border-radius: 18px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.28);
            color: #b8acd8;
            font-size: 16px;
            font-weight: 500;
            line-height: 1.65;
        }}
        .schedule-optimize-result b {{
            color: #a99bcd;
            font-weight: 900;
        }}
        .schedule-confirm-box {{
            margin-top: 2px;
            padding: 24px 26px;
            border-radius: 24px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.28);
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        @media (min-width: 768px) {{
            .schedule-confirm-box {{
                flex-direction: row;
                align-items: center;
                justify-content: space-between;
            }}
        }}
        .schedule-confirm-title {{
            margin: 0;
            color: #2d2040;
            font-size: 19px;
            font-weight: 900;
        }}
        .schedule-confirm-copy {{
            margin: 6px 0 0;
            color: #7a6aa1;
            font-size: 14px;
            line-height: 1.55;
        }}
        .schedule-confirm-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 56px;
            border-radius: 16px;
            padding: 0 24px;
            background: #a8e6c4;
            border: 1px solid rgba(80,180,120,.25);
            color: #1a5c38 !important;
            font-size: 15px;
            font-weight: 900;
            text-decoration: none !important;
            white-space: nowrap;
        }}
        .schedule-toast {{
            position: fixed;
            left: 50%;
            bottom: 18px;
            transform: translateX(-50%);
            z-index: 60;
            min-height: 56px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.32);
            color: #2d2040;
            padding: 0 28px;
            font-size: 16px;
            font-weight: 900;
            box-shadow: 0 10px 28px rgba(74,45,122,.16);
        }}
        .schedule-status-chip.ready {{
            background: rgba(74,45,122,.08);
            border-color: rgba(109,40,217,.22);
            color: #6b4fa0;
        }}
        .schedule-empty-icon {{
            width: 46px;
            height: 46px;
            margin: 0 auto 12px;
            color: #344154;
        }}
        @media (max-width: 900px) {{
            .schedule-native-head,
            .schedule-native-grid {{
                grid-template-columns: 1fr;
                display: grid;
            }}
            .schedule-find-link {{
                width: 100%;
            }}
            .st-key-schedule_shell {{
                width: 100%;
                left: auto;
                transform: none;
            }}
        }}
        .st-key-access_left_card,
        .st-key-access_right_card {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 32px;
            padding: 22px 22px 20px;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 8px 24px rgba(109,40,217,.09);
            min-height: 100%;
        }}
        .st-key-access_left_card [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-access_right_card [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .access-vision-grid-wrap {{
            margin-top: 4px;
        }}
        .access-head-row {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .access-head-row h3 {{
            margin: 4px 0 0;
            color: #2d2040;
            font-size: 24px;
            font-weight: 900;
            line-height: 1.15;
        }}
        .st-key-access_scan_btn {{
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
        }}
        .st-key-access_scan_btn > button {{
            min-height: 44px;
            border-radius: 16px;
            font-size: 14px;
            font-weight: 900;
            padding: 0 16px;
            box-shadow: 0 8px 18px rgba(74,45,122,.22);
        }}
        .st-key-access_scan_btn > button::before {{
            content: "📷";
            margin-right: 6px;
        }}
        .access-upload-panel {{
            margin-top: 4px;
            padding: 16px 18px;
            border-radius: 22px;
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
        }}
        .access-upload-title {{
            margin: 0;
            color: #2d2040;
            font-size: 14px;
            font-weight: 900;
        }}
        .access-upload-copy {{
            margin: 8px 0 12px;
            color: #7868a0;
            font-size: 12px;
            line-height: 1.65;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] {{
            margin-top: 0;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] label {{
            display: none !important;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
            background: transparent;
            border: none;
            padding: 0;
            min-height: 0;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] > div {{
            padding: 0 !important;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {{
            display: none !important;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {{
            color: #7a6aa1;
            font-size: 13px;
            font-weight: 700;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] button {{
            background: #4a2d7a !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            min-height: 42px !important;
            padding: 0 16px !important;
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] button::after {{
            content: "사진 선택";
        }}
        .st-key-access_left_card [data-testid="stFileUploader"] button span {{
            display: none;
        }}
        .access-preview-dark {{
            margin-top: 14px;
            border-radius: 24px;
            background: #0f172a;
            border: 1px solid rgba(184,172,216,.22);
            padding: 14px;
            overflow: hidden;
        }}
        .access-vision-result {{
            margin-top: 14px;
            padding: 14px 16px;
            border-radius: 18px;
            background: #0f172a;
            border: 1px solid rgba(51,65,85,.65);
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.65;
        }}
        .access-vision-result strong {{
            color: #fecaca;
        }}
        .access-vision-result .access-vision-alert {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}
        .access-vision-icon {{
            width: 44px;
            height: 44px;
            border-radius: 16px;
            display: grid;
            place-items: center;
            flex: 0 0 44px;
            background: rgba(239,68,68,.15);
            color: #fca5a5;
        }}
        .access-vision-alert-title {{
            margin: 0;
            color: #fecaca;
            font-size: 15px;
            font-weight: 900;
        }}
        .access-vision-alert-copy {{
            margin: 6px 0 0;
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.6;
        }}
        .access-bottom-actions {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 14px;
        }}
        .st-key-access_reward_btn > button {{
            min-height: 48px;
            border-radius: 16px;
            font-weight: 900;
            background: rgba(255, 196, 90, .22) !important;
            color: #6b4fa0 !important;
            border: 1px solid rgba(180, 130, 40, .22) !important;
        }}
        .st-key-access_draft_btn > button {{
            min-height: 48px;
            border-radius: 16px;
            font-weight: 900;
            background: #4a2d7a !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 8px 18px rgba(74,45,122,.22);
        }}
        .access-map-card {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 24px;
            padding: 16px;
            box-shadow: 0 1px 8px rgba(109,40,217,.05);
        }}
        .access-kicker {{
            color: #6b4fa0;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 0;
        }}
        .access-title {{
            color: #2d2040;
            font-size: clamp(26px, 3vw, 32px);
            font-weight: 900;
            margin: 6px 0 0;
            line-height: 1.1;
        }}
        .access-sub {{
            color: #7a6aa1;
            font-size: 14px;
            line-height: 1.55;
            margin: 10px 0 0;
        }}
        .access-top-grid {{
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr);
            gap: 20px;
            margin-top: 22px;
        }}
        .access-preview-caption {{
            margin-top: 10px;
            text-align: center;
            color: #94a3b8;
            font-size: 13px;
        }}
        .access-map-list {{
            display: grid;
            gap: 12px;
            margin-top: 16px;
        }}
        .access-map-item {{
            display: flex;
            gap: 12px;
            align-items: flex-start;
            padding: 16px;
            border-radius: 24px;
            border: 1px solid var(--bandabi-line);
            background: #ffffff;
            box-shadow: 0 1px 8px rgba(109,40,217,.05);
        }}
        .access-map-item.warn {{
            background: rgba(255, 236, 240, .82);
            border-color: rgba(220, 120, 140, .18);
        }}
        .access-map-item.done {{
            background: rgba(232, 248, 240, .88);
            border-color: rgba(80, 170, 120, .18);
        }}
        .access-map-icon {{
            width: 44px;
            height: 44px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 44px;
        }}
        .access-map-item.warn .access-map-icon {{
            background: rgba(220, 80, 100, .14);
            color: #c0395b;
        }}
        .access-map-item.done .access-map-icon {{
            background: rgba(60, 130, 95, .14);
            color: #1f7a52;
        }}
        .access-map-title {{
            margin: 0;
            color: #2d2040;
            font-size: 15px;
            font-weight: 900;
        }}
        .access-map-meta {{
            margin: 4px 0 0;
            color: #7868a0;
            font-size: 12px;
            line-height: 1.55;
        }}
        .access-section-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            margin-top: 18px;
        }}
        .access-soft {{
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
            border-radius: 20px;
            padding: 16px 18px;
        }}
        .access-soft-title {{
            margin: 0 0 10px;
            color: #4a2d7a;
            font-size: 14px;
            font-weight: 900;
        }}
        .access-result-card {{
            margin-top: 18px;
            padding: 18px;
            border-radius: 22px;
            border: 1px solid var(--bandabi-line);
            background: #ffffff;
        }}
        .access-grade-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .access-grade-badge {{
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            padding: 0 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 800;
        }}
        .access-grade-good {{ background: rgba(80,170,120,.14); color: #1f7a52; }}
        .access-grade-caution {{ background: rgba(255, 196, 90, .18); color: #8a5a00; }}
        .access-grade-check {{ background: rgba(220, 120, 140, .14); color: #b4234a; }}
        .access-grade-admin {{ background: rgba(74,45,122,.14); color: #4a2d7a; }}
        .access-score-ring {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-top: 8px;
        }}
        .access-score-value {{
            color: #4a2d7a;
            font-size: 34px;
            font-weight: 900;
            line-height: 1;
        }}
        .access-score-label {{
            color: #7868a0;
            font-size: 12px;
            font-weight: 700;
        }}
        .access-metric-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 12px;
        }}
        .access-metric {{
            padding: 12px;
            border-radius: 16px;
            background: var(--bandabi-surface);
            border: 1px solid var(--bandabi-line);
        }}
        .access-metric-label {{
            color: #7868a0;
            font-size: 11px;
            font-weight: 700;
        }}
        .access-metric-value {{
            color: #2d2040;
            font-size: 13px;
            font-weight: 800;
            margin-top: 4px;
            line-height: 1.45;
        }}
        .access-impact-list, .access-action-list {{
            margin: 0;
            padding-left: 18px;
            color: #4a2d7a;
            font-size: 12px;
            line-height: 1.65;
        }}
        .access-action-block {{
            margin-top: 10px;
        }}
        .access-action-block b {{
            color: #4a2d7a;
            font-size: 12px;
        }}
        .access-complete-card {{
            margin-top: 16px;
            padding: 18px;
            border-radius: 22px;
            background: rgba(240, 236, 248, .85);
            border: 1px solid var(--bandabi-line);
        }}
        .access-complete-title {{
            margin: 0;
            color: #4a2d7a;
            font-size: 16px;
            font-weight: 900;
        }}
        .access-complete-meta {{
            margin: 8px 0 0;
            color: #7868a0;
            font-size: 12px;
            line-height: 1.65;
        }}
        .access-recent-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-top: 14px;
        }}
        .access-recent-card {{
            padding: 14px;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
        }}
        .access-recent-card b {{
            color: #2d2040;
            font-size: 13px;
        }}
        .access-recent-card p {{
            margin: 6px 0 0;
            color: #7868a0;
            font-size: 11px;
            line-height: 1.55;
        }}
        @media (max-width: 980px) {{
            .access-section-grid,
            .access-recent-grid,
            .access-bottom-actions {{
                grid-template-columns: 1fr;
            }}
            .st-key-access_scan_btn {{
                margin-top: 0;
            }}
        }}
        .access-native-grid {{
            width: min(1380px, calc(100vw - 330px));
            margin: 5px auto 0;
            position: relative;
            left: 50%;
            transform: translateX(-50%);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 26px;
        }}
        .access-native-shell {{
            width: min(1380px, calc(100vw - 330px));
            margin: 5px auto 0;
            position: relative;
            left: 50%;
            transform: translateX(-50%);
        }}
        .st-key-access_left_native,
        .st-key-access_right_native,
        .access-native-card {{
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 32px;
            padding: 26px;
            min-height: 860px;
            box-shadow:
                0 2px 6px rgba(109,40,217,.06),
                0 10px 28px rgba(109,40,217,.10),
                0 1px 0 rgba(255,255,255,.92) inset;
        }}
        .st-key-access_left_native [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-access_right_native [data-testid="stVerticalBlockBorderWrapper"] {{
            border: none;
            padding: 0;
        }}
        .access-native-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
        }}
        .access-native-heading {{
            color: #2d2040 !important;
            font-family: "Pretendard Local", "Pretendard Variable", "Pretendard", sans-serif !important;
            font-size: 31px !important;
            font-weight: 900 !important;
            letter-spacing: -0.02em !important;
            margin: 5px 0 0;
            line-height: 1.1;
        }}
        .access-scan-link {{
            min-width: 100px;
            min-height: 58px;
            border-radius: 16px;
            background: #4a2d7a;
            color: #ffffff !important;
            text-decoration: none !important;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 17px;
            font-weight: 900;
            box-shadow: 0 10px 22px rgba(74,45,122,.24);
        }}
        .access-scan-link svg {{
            width: 20px;
            height: 20px;
        }}
        .access-upload-native {{
            margin-top: 24px;
            padding: 20px 22px;
            border-radius: 22px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.32);
        }}
        .access-upload-native .access-upload-copy {{
            margin-bottom: 16px;
        }}
        .access-upload-action-row {{
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }}
        .access-upload-slot {{
            flex: 0 0 auto;
        }}
        .access-upload-name-slot {{
            flex: 1 1 180px;
            display: flex;
            align-items: center;
            min-height: 42px;
        }}
        .access-upload-visual-btn {{
            min-height: 42px;
            border-radius: 14px;
            padding: 0 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #4a2d7a;
            color: #ffffff;
            font-size: 14px;
            font-weight: 900;
            box-shadow: 0 10px 22px rgba(74,45,122,.18);
        }}
        .access-upload-visual-btn svg {{
            width: 17px;
            height: 17px;
        }}
        .access-upload-file-name {{
            color: #7a6aa1;
            font-size: 13px;
            font-weight: 600;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"],
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] {{
            margin: 0;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] label,
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] label,
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] label {{
            display: none !important;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"],
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"],
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
            background: transparent;
            border: none;
            padding: 0;
            min-height: 0;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"],
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"],
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {{
            display: none !important;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] button,
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] button,
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] button {{
            min-height: 42px !important;
            border-radius: 14px !important;
            padding: 0 16px !important;
            background: #4a2d7a !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 22px rgba(74,45,122,.18) !important;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] button span,
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] button span,
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] button span {{
            display: none !important;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] button::after,
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] button::after,
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] button::after {{
            content: "사진 선택";
            font-size: 14px;
            font-weight: 900;
        }}
        .st-key-access_left_native [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
        .st-key-access_photo_upload_wrap [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
        .st-key-access_left_native [data-testid="column"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {{
            display: none !important;
        }}
        .topbar-badge-admin {{
            background: rgba(74,45,122,.10);
            border-color: rgba(109,40,217,.22);
            color: #6b4fa0;
        }}
        .admin-tab-track {{
            flex-wrap: wrap;
        }}
        .dashboard-native-shell,
        .dashboard-native-shell * {{
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-native-shell {{
            display: grid;
            gap: 20px;
            margin-top: 0;
        }}
        .dashboard-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }}
        @media (max-width: 980px) {{
            .dashboard-kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        .dashboard-kpi-card {{
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 32px;
            padding: 16px;
            box-shadow: 0 1px 8px rgba(109,40,217,.06);
        }}
        .dashboard-kpi-icon {{
            width: 20px;
            height: 20px;
            color: #6b4fa0;
        }}
        .dashboard-kpi-label {{
            margin: 12px 0 0;
            color: #7a6aa1;
            font-size: 12px;
            font-weight: 700;
        }}
        .dashboard-kpi-value {{
            margin: 4px 0 0;
            color: #2d2040;
            font-size: 24px;
            font-weight: 900;
            line-height: 1.15;
        }}
        .dashboard-kpi-value.purple {{ color: #6b4fa0; }}
        .dashboard-kpi-value.amber {{ color: #b07a20; }}
        .dashboard-kpi-value.blue {{ color: #5b7fd4; }}
        .dashboard-panel {{
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 32px;
            padding: 20px;
            box-shadow: 0 2px 20px rgba(109,40,217,.07);
        }}
        .dashboard-panel-title {{
            margin: 0;
            color: #2d2040;
            font-size: 18px;
            font-weight: 900;
        }}
        .dashboard-board-shell,
        .dashboard-board-shell p,
        .dashboard-board-shell th,
        .dashboard-board-shell td,
        .dashboard-board-shell a,
        .dashboard-board-shell b,
        .dashboard-board-shell span,
        .dashboard-board-shell div {{
            font-family: {PRETENDARD_STACK} !important;
            letter-spacing: 0;
        }}
        .dashboard-board-title {{
            margin: 6px 0 0;
            color: #2d2040;
            font-size: 24px;
            font-weight: 900;
            line-height: 1.2;
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-board-kicker {{
            color: #6b4fa0;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 0;
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-board-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }}
        .dashboard-dispatch-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 46px;
            border-radius: 16px;
            padding: 0 16px;
            background: #4a2d7a;
            color: #fff !important;
            font-size: 14px;
            font-weight: 900;
            text-decoration: none !important;
            box-shadow: 0 10px 22px rgba(74,45,122,.22);
            white-space: nowrap;
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-table-wrap {{
            margin-top: 20px;
            overflow-x: auto;
        }}
        .dashboard-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-table th {{
            text-align: left;
            color: #7a6aa1;
            font-weight: 800;
            padding: 12px;
            border-bottom: 1px solid rgba(184,172,216,.28);
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-table td {{
            padding: 12px;
            color: #4a2d7a;
            border-bottom: 1px solid rgba(184,172,216,.16);
            font-family: {PRETENDARD_STACK} !important;
        }}
        .dashboard-table td.status-warn {{ color: #b07a20; text-align: right; font-weight: 800; }}
        .dashboard-table td.status-danger {{ color: #b4234a; text-align: right; font-weight: 900; }}
        .dashboard-log-feed {{
            margin-top: 20px;
            padding: 16px;
            border-radius: 16px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.28);
            min-height: 112px;
            max-height: 112px;
            overflow-y: auto;
            font-size: 11px;
            line-height: 1.7;
            color: #7a6aa1;
        }}
        .dashboard-log-feed p {{
            margin: 0;
        }}
        .dashboard-api-section {{
            margin-top: 20px;
            padding: 18px 20px;
            border-radius: 24px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.24);
        }}
        .dashboard-api-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 14px;
        }}
        .dashboard-api-item {{
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.24);
            border-radius: 14px;
            padding: 12px 14px;
            font-size: 13px;
            line-height: 1.55;
            color: #7a6aa1;
        }}
        .dashboard-api-item.wide {{
            grid-column: 1 / -1;
        }}
        .dashboard-api-item b {{
            color: #4a2d7a;
            font-weight: 900;
        }}
        .dashboard-kpi-shell {{
            margin-bottom: 0 !important;
            display: block;
        }}
        div[data-testid="element-container"]:has(.dashboard-kpi-shell) + div[data-testid="element-container"]:has(iframe) {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        div[data-testid="stHtml"] iframe {{
            border: 0;
        }}
        div[data-testid="stHtml"],
        div[data-testid="element-container"]:has(iframe) {{
            margin-top: 0 !important;
            margin-bottom: 20px !important;
        }}
        .stMarkdown .dashboard-board-title,
        [data-testid="stMarkdownContainer"] .dashboard-board-title {{
            font-family: {PRETENDARD_STACK} !important;
            font-weight: 900 !important;
            font-size: 24px !important;
            line-height: 1.2 !important;
            color: #2d2040 !important;
            margin: 6px 0 0 !important;
        }}
        [data-testid="stMarkdownContainer"] .dashboard-board-shell,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell * {{
            font-family: {PRETENDARD_STACK} !important;
        }}
        .access-detail-native {{
            margin-top: 16px;
            padding: 18px 18px 16px;
            border-radius: 22px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.32);
        }}
        .access-detail-form {{
            margin: 0;
            display: grid;
            gap: 14px;
        }}
        .access-native-label {{
            display: block;
            color: #7a6aa1;
            font-size: 12px;
            font-weight: 800;
            margin: 0 0 8px;
        }}
        .access-native-select {{
            width: 100%;
            min-height: 50px;
            border-radius: 16px;
            border: 1px solid rgba(119,96,160,.18);
            background-color: #ffffff;
            color: #2d2040;
            font-size: 14px;
            font-weight: 500;
            padding: 0 42px 0 14px;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237c5fb8' stroke-width='2.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 14px center;
            background-size: 16px;
        }}
        .access-detail-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 2px;
        }}
        .access-detail-button {{
            min-height: 48px;
            border-radius: 14px;
            border: 0;
            padding: 0 18px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 900;
            cursor: pointer;
        }}
        .access-detail-button.primary {{
            background: #4a2d7a;
            color: #ffffff;
            box-shadow: 0 10px 22px rgba(74,45,122,.18);
        }}
        .access-detail-button.secondary {{
            background: #ffffff;
            color: #4a2d7a;
            border: 1px solid rgba(184,172,216,.34);
        }}
        .access-detail-button svg {{
            width: 16px;
            height: 16px;
        }}
        .access-preview-native {{
            margin-top: 22px;
            border-radius: 24px;
            background: #0f172a;
            border: 1px solid rgba(184,172,216,.24);
            padding: 18px;
            overflow: hidden;
        }}
        .access-preview-native svg {{
            display: block;
            width: 100%;
            height: 294px;
        }}
        .access-note-native {{
            margin-top: 18px;
            padding: 15px 18px;
            border-radius: 18px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.32);
            color: #2d2040;
            font-size: 14px;
            line-height: 1.7;
        }}
        .access-action-native-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 14px;
        }}
        .access-action-link {{
            min-height: 54px;
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            text-decoration: none !important;
            font-size: 15px;
            font-weight: 900;
        }}
        .access-action-link.reward {{
            background: #8170ac;
            color: #ffffff !important;
            border: 1px solid rgba(129,112,172,.24);
        }}
        .access-action-link.draft {{
            background: #6d28d9;
            color: #ffffff !important;
            box-shadow: 0 10px 22px rgba(109,40,217,.20);
        }}
        .access-action-link svg {{
            width: 18px;
            height: 18px;
        }}
        .access-map-native-list {{
            display: grid;
            gap: 16px;
            margin-top: 28px;
        }}
        .access-map-native-item {{
            display: flex;
            align-items: center;
            gap: 16px;
            min-height: 92px;
            padding: 18px 20px;
            border-radius: 22px;
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.26);
            box-shadow: 0 8px 22px rgba(109,40,217,.08);
        }}
        .access-map-native-icon {{
            width: 52px;
            height: 52px;
            border-radius: 16px;
            display: grid;
            place-items: center;
            flex: 0 0 52px;
        }}
        .access-map-native-icon.warn {{
            background: #fde1e6;
            color: #4a2d7a;
        }}
        .access-map-native-icon.done {{
            background: #d9f3ea;
            color: #4a2d7a;
        }}
        .access-map-native-icon svg {{
            width: 22px;
            height: 22px;
        }}
        .access-map-native-title {{
            margin: 0;
            color: #2d2040;
            font-size: 18px;
            font-weight: 900;
            line-height: 1.25;
        }}
        .access-map-native-meta {{
            margin: 6px 0 0;
            color: #7868a0;
            font-size: 13px;
            line-height: 1.55;
        }}
        .access-hidden-tools {{
            max-width: 1380px;
            margin: 18px auto 0;
        }}
        .access-report-native {{
            width: min(1380px, calc(100vw - 330px));
            margin: 18px auto 0;
            position: relative;
            left: 50%;
            transform: translateX(-50%);
            background: #ffffff;
            border: 1px solid var(--bandabi-line);
            border-radius: 28px;
            padding: 24px;
            box-shadow: 0 10px 28px rgba(109,40,217,.09);
        }}
        .access-report-native h3 {{
            margin: 0 0 14px;
            color: #2d2040;
            font-size: 21px;
            font-weight: 900;
        }}
        .access-report-native-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }}
        .access-draft-overlay {{
            position: fixed;
            inset: 0;
            z-index: 90;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 42px 18px;
            background: rgba(232,226,244,.78);
            backdrop-filter: blur(10px);
            overflow-y: auto;
        }}
        .access-draft-modal {{
            width: min(920px, calc(100vw - 44px));
            max-height: calc(100vh - 84px);
            overflow-y: auto;
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 18px;
            padding: 28px 28px 30px;
            box-shadow: 0 24px 70px rgba(74,45,122,.17);
        }}
        .access-draft-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(184,172,216,.25);
        }}
        .access-draft-title {{
            margin: 5px 0 0;
            color: #2d2040;
            font-size: 27px;
            font-weight: 900;
            line-height: 1.12;
        }}
        .access-draft-copy {{
            margin: 8px 0 0;
            color: #7c5fb8;
            font-size: 14px;
            line-height: 1.5;
            font-weight: 500;
        }}
        .access-draft-close {{
            width: 52px;
            height: 52px;
            border-radius: 16px;
            background: #f0ecf8;
            color: #4a2d7a !important;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none !important;
            border: 1px solid rgba(184,172,216,.35);
            flex: 0 0 52px;
        }}
        .access-draft-close svg {{
            width: 22px;
            height: 22px;
        }}
        .access-draft-form-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-top: 24px;
        }}
        .access-draft-label {{
            display: block;
            color: #7c5fb8;
            font-size: 13px;
            font-weight: 900;
            margin: 0 0 10px;
        }}
        .access-draft-input,
        .access-draft-textarea {{
            box-sizing: border-box;
            width: 100%;
            border: 1px solid rgba(184,172,216,.28);
            background: #ffffff;
            color: #4a2d7a;
            border-radius: 16px;
            font-size: 15px;
            font-weight: 500;
            line-height: 1.7;
            padding: 14px 18px;
        }}
        .access-draft-input {{
            min-height: 58px;
        }}
        .access-draft-section {{
            margin-top: 24px;
            border-radius: 22px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.30);
            padding: 20px;
        }}
        .access-draft-section-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 14px;
        }}
        .access-draft-section-title {{
            margin: 0;
            color: #2d2040;
            font-size: 20px;
            font-weight: 900;
            display: inline-flex;
            align-items: center;
            gap: 9px;
        }}
        .access-draft-section-title svg {{
            width: 21px;
            height: 21px;
            color: #6d28d9;
        }}
        .access-draft-mini-link {{
            min-height: 40px;
            border-radius: 14px;
            padding: 0 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #f6f3fc;
            color: #4a2d7a !important;
            border: 1px solid rgba(184,172,216,.35);
            text-decoration: none !important;
            font-size: 13px;
            font-weight: 900;
            white-space: nowrap;
        }}
        .access-draft-textarea {{
            min-height: 300px;
            resize: vertical;
            white-space: pre-wrap;
        }}
        .access-draft-pre {{
            margin: 0;
            min-height: 220px;
            overflow-x: auto;
            border-radius: 16px;
            background: rgba(30, 25, 38, .45);
            color: #ffffff;
            border: 1px solid rgba(74,45,122,.18);
            padding: 18px;
            font-size: 12px;
            line-height: 1.7;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace !important;
        }}
        .access-draft-warning {{
            margin: 14px 0 0;
            color: #8a5a00;
            font-size: 12px;
            line-height: 1.5;
            font-weight: 700;
        }}
        .access-draft-actions {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 22px;
        }}
        .access-draft-action {{
            min-height: 52px;
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            text-decoration: none !important;
            font-size: 14px;
            font-weight: 900;
            color: #ffffff !important;
        }}
        .access-draft-action.neutral {{ background: #514463; }}
        .access-draft-action.ready {{ background: #4a2d7a; }}
        .access-draft-action.submit {{ background: #6d28d9; }}
        .access-draft-action svg {{
            width: 18px;
            height: 18px;
        }}
        @media (max-width: 980px) {{
            .access-native-grid,
            .access-native-shell {{
                width: 100%;
                left: auto;
                transform: none;
            }}
            .st-key-access_left_native,
            .st-key-access_right_native,
            .access-native-card {{
                min-height: auto;
            }}
            .access-report-native {{
                width: 100%;
                left: auto;
                transform: none;
            }}
            .access-draft-form-grid,
            .access-draft-actions,
            .access-report-native-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        @media (max-width: 760px) {{
            .block-container {{ padding: 1rem 1rem 4rem; }}
            .section-card, .auth-card {{ padding: 20px; border-radius: 18px; }}
            .brand-title {{ font-size: 17px; }}
            .section-title {{ font-size: 25px; }}
            .metric-value {{ font-size: 24px; }}
            .route-warning-list {{ grid-template-columns: 1fr; }}
            .step-action-links {{
                justify-content: stretch;
                flex-direction: column;
            }}
            .step-action-link {{
                width: 100%;
            }}
            .report-native-grid {{
                grid-template-columns: 1fr;
            }}
            .report-native-card.wide {{
                grid-column: auto;
            }}
            .st-key-report_action_row .stButton {{
                width: 100%;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def role_label(role: str | None = None) -> str:
    value = role or st.session_state.get("role")
    return "기관 관리자 모드" if value == ADMIN_ROLE else "이용자 모드"


def add_points(amount: int, point_key: str) -> None:
    if st.session_state.get(point_key):
        return
    st.session_state.bt_points = int(st.session_state.get("bt_points", 3500)) + amount
    st.session_state.bt_balance = st.session_state.bt_points
    st.session_state[point_key] = True


def reset_user_flow() -> None:
    st.session_state.main_step = "start"
    st.session_state.route_result = None
    st.session_state.route_analysis_result = None
    st.session_state.buddy_confirmed = False
    st.session_state.class_confirmed = False
    st.session_state.report_saved = False
    st.session_state.guardian_summary = ""
    st.session_state.pending_confirm = None


def block_unavailable_destination() -> None:
    if st.session_state.get("destination_choice") == UNAVAILABLE_DESTINATION:
        st.session_state.destination_choice = DEFAULT_DESTINATION
        st.session_state.destination = DEFAULT_DESTINATION
        st.session_state.center_warning = True
        st.session_state.notice = UNAVAILABLE_MESSAGE
    else:
        st.session_state.destination = DEFAULT_DESTINATION


def metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{esc(label)}</div>
            <div class="metric-value">{esc(value)}</div>
            <div class="metric-caption">{esc(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def route_detail_card(
    label: str,
    value: str,
    caption: str = "",
    *,
    details: list[Any] | None = None,
    badge: str = "",
) -> None:
    badge_html = f'<span class="route-detail-badge">{esc(badge)}</span>' if badge else ""
    detail_html = ""
    if details:
        detail_html = "<ul class='route-detail-list'>" + "".join(
            f"<li>{esc(item)}</li>" for item in details if str(item).strip()
        ) + "</ul>"
    st.markdown(
        f"""
        <div class="route-detail-card">
            <div class="route-detail-top">
                <span class="route-detail-label">{esc(label)}</span>
                {badge_html}
            </div>
            <p class="route-detail-value">{esc(value)}</p>
            <p class="route-detail-caption">{esc(caption)}</p>
            {detail_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def soft_card(kicker: str, title: str, body: str, chips: list[str] | None = None) -> None:
    chip_html = ""
    if chips:
        chip_html = "<div class='chip-row'>" + "".join(
            f"<span class='chip'>{esc(chip)}</span>" for chip in chips
        ) + "</div>"
    st.markdown(
        f"""
        <div class="soft-card">
            <p class="tiny-label">{esc(kicker)}</p>
            <h3 style="margin:0;color:var(--bandabi-ink);font-size:24px;font-weight:900;line-height:1.18;">{esc(title)}</h3>
            <p class="section-copy" style="font-size:13px;margin-top:12px;">{esc(body)}</p>
            {chip_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(kicker: str, title: str, copy: str, chips: list[str] | None = None) -> None:
    chip_html = ""
    if chips:
        chip_html = "<div class='chip-row'>" + "".join(
            f"<span class='chip'>{esc(chip)}</span>" for chip in chips
        ) + "</div>"
    st.markdown(
        f"""
        <div class="section-card">
            <p class="tiny-label">{esc(kicker)}</p>
            <h1 class="section-title">{esc(title)}</h1>
            <p class="section-copy">{esc(copy)}</p>
            {chip_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def signup_role_from_choice() -> str:
    choice = st.session_state.get("signup_role_choice", "이용자 (User)")
    return ADMIN_ROLE if "Admin" in str(choice) else USER_ROLE


def _normalize_demo_identity_fields(raw_name: str, raw_email: str) -> tuple[str, str]:
    """이름 칸에 이메일이 들어온 경우(자동완성·오입력) 보정."""
    name = (raw_name or "").strip()
    email = (raw_email or "").strip()
    if "@" in name and not email:
        email, name = name, ""
    if "@" in name:
        name = ""
    return name, email


def _resolve_demo_auth_identity() -> tuple[str, str]:
    """데모 폼 제출값(auth_user/auth_email)만 세션에 반영."""
    qp_name, qp_email = _normalize_demo_identity_fields(
        st.query_params.get("auth_user") or st.query_params.get("user") or "",
        st.query_params.get("auth_email") or st.query_params.get("email") or "",
    )
    name = qp_name or "안소연"
    email = qp_email
    st.session_state.auth_name = name
    st.session_state.login_name = name
    st.session_state.user_name = name
    st.session_state.auth_email = email
    st.session_state.login_email = email
    st.session_state.user_email = email
    return name, email


def finalize_app_entry(role: str) -> None:
    name = (st.session_state.get("user_name") or st.session_state.get("auth_name") or "").strip() or "안소연"
    email = (st.session_state.get("auth_email") or st.session_state.get("user_email") or "").strip()
    st.session_state.user_name = name
    st.session_state.user_email = email
    st.session_state.logged_in = True
    st.session_state.authenticated = True
    st.session_state.role = role
    st.session_state.current_page = "dashboard" if role == ADMIN_ROLE else "main"
    st.session_state.main_step = "start"
    st.session_state.auth_stage = "entry"
    st.session_state.bt_points = int(st.session_state.get("bt_points", 3500))
    st.session_state.bt_balance = st.session_state.bt_points


def render_auth() -> None:
    query_auth = st.query_params.get("auth")
    if query_auth == "entry":
        st.session_state.auth_stage = "entry"
        st.session_state.auth_mode = "로그인"
        st.session_state.auth_name = ""
        st.session_state.auth_email = ""
        try:
            del st.query_params["auth"]
        except Exception:
            pass
    if query_auth == "signup_done":
        _resolve_demo_auth_identity()
        st.session_state.auth_mode = "회원가입"
        st.session_state.auth_stage = "role_select"
        signup_role_qp = st.query_params.get("signup_role")
        if signup_role_qp == "admin":
            st.session_state.signup_role_choice = "기관 관리자 (Admin)"
        elif signup_role_qp == "user":
            st.session_state.signup_role_choice = "이용자 (User)"
        try:
            del st.query_params["auth"]
            for key in ("signup_role", "auth_user", "auth_email", "user", "email", "role"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass
        st.rerun()
    if query_auth == "login_done":
        _resolve_demo_auth_identity()
        st.session_state.auth_mode = "로그인"
        st.session_state.auth_stage = "role_select"
        try:
            del st.query_params["auth"]
            for key in ("auth_user", "auth_email", "user", "email", "role"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass
        st.rerun()
    if query_auth == "enter_app":
        qp_user, qp_email = _normalize_demo_identity_fields(
            st.query_params.get("auth_user") or st.query_params.get("user") or "",
            st.query_params.get("auth_email") or st.query_params.get("email") or "",
        )
        if qp_user:
            st.session_state.user_name = qp_user
            st.session_state.auth_name = qp_user
            st.session_state.login_name = qp_user
        if qp_email:
            st.session_state.user_email = qp_email
            st.session_state.auth_email = qp_email
            st.session_state.login_email = qp_email
        role_qp = st.query_params.get("role")
        if role_qp == ADMIN_ROLE:
            chosen_role = ADMIN_ROLE
        elif role_qp == USER_ROLE:
            chosen_role = USER_ROLE
        elif st.session_state.get("auth_mode") == "회원가입":
            chosen_role = signup_role_from_choice()
        else:
            chosen_role = USER_ROLE
        finalize_app_entry(chosen_role)
        try:
            del st.query_params["auth"]
            for key in ("role", "auth_user", "auth_email", "user", "email"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass
        st.rerun()
    if query_auth in {"login", "signup"}:
        st.session_state.auth_stage = "form"
        st.session_state.auth_mode = "로그인" if query_auth == "login" else "회원가입"
        st.session_state.auth_name = ""
        st.session_state.auth_email = ""
        if query_auth == "signup":
            signup_role_qp = st.query_params.get("signup_role") or st.query_params.get("role")
            if signup_role_qp == "admin":
                st.session_state.signup_role_choice = "기관 관리자 (Admin)"
            elif signup_role_qp == "user":
                st.session_state.signup_role_choice = "이용자 (User)"
        try:
            del st.query_params["auth"]
            for key in ("signup_role", "role", "auth_user", "auth_email"):
                if key in st.query_params:
                    del st.query_params[key]
        except Exception:
            pass

    if st.session_state.get("auth_stage", "entry") == "role_select":
        preview_name = (st.session_state.get("user_name") or "반다비").strip()
        user_qp = urlencode(
            {
                "auth_user": preview_name,
                "auth_email": st.session_state.get("user_email") or "",
            }
        )
        icon_src = bandabi_icon_data_uri()
        logo_html = (
            f'<img class="auth-form-logo" src="{icon_src}" alt="반다비">'
            if icon_src
            else '<span class="auth-form-logo" style="background:#4a2d7a;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:30px;">B</span>'
        )
        st.markdown(
            html_block(f"""
            <div class="auth-form-page">
                <section class="auth-form-card" aria-label="반다비 AI 모드 선택">
                    <div class="auth-form-head">
                        {logo_html}
                        <div class="auth-form-copy">
                            <div class="auth-form-title" role="heading" aria-level="1">반다비 AI</div>
                            <p class="auth-form-sub">{esc(preview_name)}님, 접속할 서비스를 선택하세요.</p>
                        </div>
                    </div>
                    <div class="role-select-panel">
                        <p class="role-select-kicker">Mode Select</p>
                        <a class="role-select-card" href="?auth=enter_app&amp;role={USER_ROLE}&amp;{user_qp}" target="_self">
                            <div class="role-select-card-inner">
                                <div class="role-select-icon user" aria-hidden="true">
                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                                        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                                        <path d="M5 20c1.2-3.5 4-5.5 7-5.5s5.8 2 7 5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                    </svg>
                                </div>
                                <div>
                                    <p class="role-select-title">이용자 모드</p>
                                    <p class="role-select-copy">경로 · 동행 · 강습 · 리포트</p>
                                </div>
                            </div>
                        </a>
                        <a class="role-select-card" href="?auth=enter_app&amp;role={ADMIN_ROLE}&amp;{user_qp}" target="_self">
                            <div class="role-select-card-inner">
                                <div class="role-select-icon admin" aria-hidden="true">
                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                                        <rect x="4" y="8" width="16" height="12" rx="2" stroke="currentColor" stroke-width="2"/>
                                        <path d="M8 8V6a4 4 0 0 1 8 0v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                        <path d="M12 12v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                    </svg>
                                </div>
                                <div>
                                    <p class="role-select-title">기관 관리자 모드</p>
                                    <p class="role-select-copy">스케줄 · 접근성 점검 보조 · 대시보드</p>
                                </div>
                            </div>
                        </a>
                        <a class="role-select-back" href="?auth=entry" target="_self">로그인/회원가입으로 돌아가기</a>
                    </div>
                </section>
            </div>
            """),
            unsafe_allow_html=True,
        )
        return

    if st.session_state.get("auth_stage", "entry") == "entry":
        icon_src = bandabi_icon_data_uri()
        logo_html = (
            f'<img class="auth-entry-logo" src="{icon_src}" alt="반다비">'
            if icon_src
            else '<span class="auth-entry-logo" style="background:#4a2d7a;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:30px;">B</span>'
        )
        st.markdown(
            html_block(f"""
            <div class="auth-entry-page">
                <section class="auth-entry-card" aria-label="반다비 AI 시작">
                    <div class="auth-entry-head">
                        {logo_html}
                        <div class="auth-entry-copy">
                            <div class="auth-entry-title" role="heading" aria-level="1">반다비 AI</div>
                            <p class="auth-entry-sub">서비스 이용을 위해 로그인하거나<br>회원가입을 진행하세요.</p>
                        </div>
                    </div>

                    <a class="auth-choice primary" href="?auth=login" target="_self" aria-label="로그인">
                        <span class="auth-choice-icon" aria-hidden="true">
                            <svg width="29" height="29" viewBox="0 0 24 24" fill="none">
                                <path d="M15 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M10 17l5-5-5-5" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M15 12H3" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </span>
                        <span class="auth-choice-text">
                            <span class="auth-choice-title">로그인</span>
                            <span class="auth-choice-desc">기존 계정으로 서비스 이어가기</span>
                        </span>
                    </a>

                    <a class="auth-choice secondary" href="?auth=signup" target="_self" aria-label="회원가입">
                        <span class="auth-choice-icon" aria-hidden="true">
                            <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
                                <path d="M15 19a6 6 0 0 0-12 0" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                <path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" fill="currentColor"/>
                                <path d="M19 8v6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                                <path d="M22 11h-6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                            </svg>
                        </span>
                        <span class="auth-choice-text">
                            <span class="auth-choice-title">회원가입</span>
                            <span class="auth-choice-desc">접근성 지원 유형과 알림 설정을 시작</span>
                        </span>
                    </a>

                    <div class="auth-notice">
                        <span class="auth-notice-title">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="vertical-align:-2px;margin-right:4px;">
                                <rect x="5" y="10" width="14" height="10" rx="2" fill="currentColor"/>
                                <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                            </svg>
                            민감정보 고지
                        </span>
                        본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고,
                        생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다.
                    </div>

                    <p class="auth-footnote">
                        * 계정·비밀번호는 데모용으로 브라우저 저장소에만 보관되며,<br>
                        실제 서버 인증·암호화 보안을 제공하지 않습니다.
                    </p>
                </section>
            </div>
            """),
            unsafe_allow_html=True,
        )
        return

    icon_src = bandabi_icon_data_uri()
    auth_mode = st.session_state.get("auth_mode", "로그인")
    subtitle = (
        "회원가입 후 이용자/관리자 모드를 선택하세요."
        if auth_mode == "회원가입"
        else "로그인 후 이용자/관리자 모드를 선택하세요."
    )
    logo_html = (
        f'<img class="auth-form-logo" src="{icon_src}" alt="반다비">'
        if icon_src
        else '<span class="auth-form-logo" style="background:#4a2d7a;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:30px;">B</span>'
    )

    if auth_mode == "회원가입":
        role_choice = st.session_state.get("signup_role_choice", "이용자 (User)")
        user_role_active = " active" if "User" in str(role_choice) else ""
        admin_role_active = " active" if "Admin" in str(role_choice) else ""
        signup_role_param = "admin" if "Admin" in str(role_choice) else "user"
        st.markdown(
            html_block(f"""
            <div class="auth-form-page">
                <section class="auth-form-card" aria-label="반다비 AI 회원가입">
                    <div class="auth-form-head">
                        {logo_html}
                        <div class="auth-form-copy">
                            <div class="auth-form-title" role="heading" aria-level="1">반다비 AI</div>
                            <p class="auth-form-sub">{esc(subtitle)}</p>
                        </div>
                    </div>
                    <form method="get" action="" class="auth-demo-form">
                        <input type="hidden" name="auth" value="signup_done">
                        <input type="hidden" name="signup_role" value="{signup_role_param}">
                        <div class="signup-panel">
                            <div class="signup-panel-title">회원가입</div>
                            <p class="signup-panel-copy">프로토타입에서는 기본 정보만 입력하고 역할 선택으로 이동합니다.</p>

                            <label class="signup-field">
                                <span class="signup-label">이름</span>
                                <input id="bandabi-auth-name" class="signup-input" type="text" name="auth_user" placeholder="예: 홍길동" autocomplete="given-name" inputmode="text">
                            </label>
                            <label class="signup-field">
                                <span class="signup-label">이메일</span>
                                <input id="bandabi-auth-email" class="signup-input" type="email" name="auth_email" placeholder="user@example.com" autocomplete="email" inputmode="email">
                            </label>
                            <label class="signup-field">
                                <span class="signup-label">비밀번호</span>
                                <input class="signup-input" type="password" name="auth_password_demo" placeholder="비밀번호" autocomplete="new-password">
                            </label>
                            <label class="signup-field">
                                <span class="signup-label">비밀번호 확인</span>
                                <input class="signup-input" type="password" name="auth_password_confirm_demo" placeholder="비밀번호 확인" autocomplete="new-password">
                            </label>
                            <div class="signup-field">
                                <span class="signup-label">회원 유형</span>
                                <div class="signup-role-links">
                                    <a class="signup-role-link{user_role_active}" href="?auth=signup&amp;signup_role=user" target="_self">이용자 (User)</a>
                                    <a class="signup-role-link{admin_role_active}" href="?auth=signup&amp;signup_role=admin" target="_self">기관 관리자 (Admin)</a>
                                </div>
                            </div>
                        </div>

                        <div class="auth-form-buttons">
                            <a class="auth-form-action back" href="?auth=entry" target="_self">이전</a>
                            <button type="submit" class="auth-form-action next">계속</button>
                        </div>
                    </form>

                    <div class="auth-notice auth-form-notice">
                        <span class="auth-notice-title">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="vertical-align:-2px;margin-right:4px;">
                                <rect x="5" y="10" width="14" height="10" rx="2" fill="currentColor"/>
                                <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                            </svg>
                            민감정보 고지
                        </span>
                        본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고,
                        생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다.
                    </div>
                    <p class="auth-footnote">
                        * 계정·비밀번호는 데모용으로 브라우저 저장소에만 보관되며,<br>
                        실제 서버 인증·암호화 보안을 제공하지 않습니다.
                    </p>
                </section>
            </div>
            """),
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        html_block(f"""
        <div class="auth-form-page">
            <section class="auth-form-card" aria-label="반다비 AI 로그인">
                <div class="auth-form-head">
                    {logo_html}
                    <div class="auth-form-copy">
                        <div class="auth-form-title" role="heading" aria-level="1">반다비 AI</div>
                        <p class="auth-form-sub">{esc(subtitle)}</p>
                    </div>
                </div>
                <form method="get" action="" class="auth-demo-form">
                    <input type="hidden" name="auth" value="login_done">
                    <div class="signup-panel">
                        <div class="signup-panel-title">로그인</div>
                        <p class="signup-panel-copy">프로토타입에서는 실제 인증 없이 다음 단계로 이동합니다.</p>

                        <label class="signup-field">
                            <span class="signup-label">이름</span>
                            <input id="bandabi-auth-name" class="signup-input" type="text" name="auth_user" placeholder="예: 홍길동" autocomplete="given-name" inputmode="text">
                        </label>
                        <label class="signup-field">
                            <span class="signup-label">이메일</span>
                            <input id="bandabi-auth-email" class="signup-input" type="email" name="auth_email" placeholder="user@example.com" autocomplete="email" inputmode="email">
                        </label>
                        <label class="signup-field">
                            <span class="signup-label">비밀번호</span>
                            <input class="signup-input" type="password" name="auth_password_demo" placeholder="비밀번호" autocomplete="current-password">
                        </label>
                    </div>

                    <div class="auth-form-buttons">
                        <a class="auth-form-action back" href="?auth=entry" target="_self">이전</a>
                        <button type="submit" class="auth-form-action next">계속</button>
                    </div>
                </form>

                <div class="auth-notice auth-form-notice">
                    <span class="auth-notice-title">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="vertical-align:-2px;margin-right:4px;">
                            <rect x="5" y="10" width="14" height="10" rx="2" fill="currentColor"/>
                            <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                        </svg>
                        민감정보 고지
                    </span>
                    본 서비스는 장애 진단명이나 이동 지원 난이도를 기준으로 이용자를 분류하지 않고,
                    생활체육 참여에 필요한 이동·안내·동행·접근성 지원 유형을 기준으로 맞춤 정보를 제공합니다.
                </div>
                <p class="auth-footnote">
                    * 계정·비밀번호는 데모용으로 브라우저 저장소에만 보관되며,<br>
                    실제 서버 인증·암호화 보안을 제공하지 않습니다.
                </p>
            </section>
        </div>
        """),
        unsafe_allow_html=True,
    )


USER_TABS: list[tuple[str, str, str]] = [
    ("main", "AI 추천 및 이동지원 연계", "brain"),
    ("schedule", "내 운동 일정 추천", "calendar_check"),
    ("accessibility", "AI 기반 접근성 점검 보조", "eye"),
]

ADMIN_TABS: list[tuple[str, str, str]] = [
    *USER_TABS,
    ("dashboard", "기관용 대시보드", "chart_pie"),
]


def tab_icon_svg(kind: str) -> str:
    if kind == "brain":
        brain_path = Path(__file__).resolve().parent / "assets" / "img" / "brain.svg"
        try:
            return brain_path.read_text(encoding="utf-8")
        except OSError:
            pass
    icons = {
        "calendar_check": """
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="4" y="6" width="16" height="14" rx="3" stroke="currentColor" stroke-width="2"/>
                <path d="M8 4v4M16 4v4M4 10h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M9 15l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        """,
        "eye": """
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M2.5 12C4.6 7.8 8 5.5 12 5.5s7.4 2.3 9.5 6.5c-2.1 4.2-5.5 6.5-9.5 6.5S4.6 16.2 2.5 12Z" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="2.8" stroke="currentColor" stroke-width="2"/>
            </svg>
        """,
        "chart_pie": """
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 3v9h9a9 9 0 0 0-9-9Z" fill="currentColor" opacity=".35"/>
                <path d="M12 3a9 9 0 0 1 9 9h-9V3Z" fill="currentColor"/>
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
            </svg>
        """,
    }
    return icons.get(kind, "")


def handle_user_chrome_query() -> None:
    changed = False

    def sync_access_controls_from_query() -> tuple[str, str, list[str]]:
        facility = st.query_params.get("access_facility_type")
        focus = st.query_params.get("access_focus")
        try:
            issues = [x for x in st.query_params.get_all("access_issue") if x]
        except Exception:
            issue = st.query_params.get("access_issue", "")
            issues = [issue] if issue else []
        if facility in ACCESS_FACILITY_TYPES:
            st.session_state.access_facility_type = facility
        if focus in ACCESS_DISABILITY_FOCUS:
            st.session_state.access_disability_focus = focus
        cleaned_issues = [issue for issue in issues if issue in ACCESS_ISSUE_OPTIONS]
        if "access_issue" in st.query_params:
            st.session_state.access_issue_choices = cleaned_issues
        elif cleaned_issues:
            st.session_state.access_issue_choices = cleaned_issues
        return (
            st.session_state.get("access_facility_type", "점자블록"),
            st.session_state.get("access_disability_focus", "시각 정보 접근 지원 필요"),
            st.session_state.get("access_issue_choices") or [],
        )

    nav_tab = st.query_params.get("nav_tab")
    allowed_tabs = {"main", "schedule", "accessibility"}
    if st.session_state.get("role") == ADMIN_ROLE:
        allowed_tabs.add("dashboard")
    if nav_tab in allowed_tabs:
        st.session_state.current_page = nav_tab
        if nav_tab != "main":
            st.session_state.pending_confirm = None
        changed = True
    action = st.query_params.get("action")
    if action == "high_contrast":
        st.session_state.high_contrast = not bool(st.session_state.get("high_contrast"))
        changed = True
    elif action == "voice":
        st.session_state.notice = "음성 안내는 프로토타입 데모 기능입니다."
        changed = True
    elif action == "start_ai":
        incoming_origin = (st.query_params.get("origin") or "").strip()
        if incoming_origin:
            st.session_state.origin = incoming_origin
        start_analysis()
        changed = True
    elif action == "pending_ok":
        apply_pending_confirm()
        changed = True
    elif action == "pending_cancel":
        _cancel_pending_confirm()
        changed = True
    elif action == "care_skip":
        st.session_state.buddy_confirmed = False
        st.session_state.main_step = "class"
        st.session_state.current_page = "main"
        st.session_state.notice = "버디 매칭을 건너뛰고 강습·지도자 추천으로 이동합니다."
        changed = True
    elif action == "care_confirm":
        open_confirm(
            "버디 매칭 확정 요청이 등록되었습니다.",
            "상호 동의와 관리자 확인 후 연결됩니다.",
            "첫 방문 버디 후보 연결 요청이 등록되었습니다. 실명·연락처는 확정 전 비공개로 유지됩니다.",
            "class",
            confirm_buddy=True,
            toast="버디 후보가 임시 확정되었습니다. 강습·지도자 추천으로 이동합니다.",
        )
        st.session_state.current_page = "main"
        changed = True
    elif action == "class_next":
        st.session_state.instructor_index = (int(st.session_state.get("instructor_index", 0)) + 1) % len(INSTRUCTORS)
        st.session_state.main_step = "class"
        st.session_state.current_page = "main"
        changed = True
    elif action == "class_confirm":
        open_confirm(
            "강습·지도자 추천이 확정되었습니다.",
            "운동 참여 결과를 리포트 화면에서 확인합니다.",
            "추천 지도자와 강습 선택이 등록되었습니다. 본 내용은 생활체육 참여 지원을 위한 참고자료입니다.",
            "report",
            confirm_class=True,
            toast="강습 추천이 확정되었습니다. 생활체육 리포트로 이동합니다.",
        )
        st.session_state.current_page = "main"
        changed = True
    elif action == "schedule_find":
        day_map = {
            "화·목 중심": ["화", "목"],
            "월·수 중심": ["월", "수"],
            "주말 가능": ["토", "일"],
        }
        incoming_day = st.query_params.get("schedule_day_label")
        incoming_time = st.query_params.get("schedule_time_label")
        if incoming_day in day_map:
            st.session_state.schedule_day_label = incoming_day
        if incoming_time in {"오전 10시 전후", "오후 2시 전후", "오후 4시 전후"}:
            st.session_state.schedule_time_label = incoming_time
        day_label = st.session_state.get("schedule_day_label", "화·목 중심")
        time_label = st.session_state.get("schedule_time_label", "오전 10시 전후")
        recommendations = make_schedule_recommendations(day_map.get(day_label, ["화", "목"]), time_label)
        st.session_state.schedule_recommendations = recommendations
        st.session_state.schedule_generated = True
        st.session_state.schedule_selected_time = ""
        st.session_state.schedule_top_pick = recommendations[0]["full_label"] if recommendations else ""
        st.session_state.current_page = "schedule"
        changed = True
    elif action == "schedule_select":
        selected = st.query_params.get("schedule_time", "")
        if selected:
            st.session_state.schedule_selected_time = selected
            st.session_state.current_page = "schedule"
            changed = True
    elif action == "dashboard_dispatch":
        if st.session_state.get("role") == ADMIN_ROLE:
            logs = list(st.session_state.get("dashboard_log_lines") or [])
            logs.extend(
                [
                    "[10:08:21] 노쇼 공백 감지 · 대기자 2명 알림 발송",
                    "[10:08:28] 1순위 대기자 수락 · 슬롯 임시 확정",
                ]
            )
            st.session_state.dashboard_log_lines = logs[-8:]
            st.session_state.current_page = "dashboard"
            st.session_state.notice = "대체 매칭 알림 mock 로그가 추가되었습니다."
            changed = True
    elif action == "schedule_continue":
        st.session_state.selected_schedule = st.session_state.get("schedule_selected_time") or st.session_state.get("schedule_top_pick")
        st.session_state.current_page = "main"
        st.session_state.main_step = "route"
        st.session_state.notice = "선택한 시간 기준으로 예약 흐름을 이어갑니다."
        changed = True
    elif action == "access_scan":
        facility_type, focus, issues = sync_access_controls_from_query()
        access_run_scan(
            facility_type,
            focus,
            issues,
            st.session_state.get("access_photo_upload") is not None,
        )
        st.session_state.current_page = "accessibility"
        changed = True
    elif action == "access_submit":
        facility_type, focus, issues = sync_access_controls_from_query()
        current = access_run_scan(
            facility_type,
            focus,
            issues,
            st.session_state.get("access_photo_upload") is not None,
        )
        entry = register_accessibility_submission(current)
        st.session_state.current_page = "accessibility"
        st.session_state.notice = f"제보 {entry['id']}가 접수 대기 상태로 등록되었습니다. 관리자 확인이 필요합니다."
        changed = True
    elif action == "access_reward":
        facility_type, focus, issues = sync_access_controls_from_query()
        current = st.session_state.get("access_analysis") or access_run_scan(
            facility_type,
            focus,
            issues,
            st.session_state.get("access_photo_upload") is not None,
        )
        register_accessibility_submission(current)
        add_points(200, "accessibility_points_awarded")
        st.session_state.current_page = "accessibility"
        st.session_state.notice = "접근성 제보 참여 인센티브 200BT가 적립되었습니다. 현금 환급·양도·재판매는 불가합니다."
        changed = True
    elif action == "access_draft":
        facility_type, focus, issues = sync_access_controls_from_query()
        if not st.session_state.get("access_analysis"):
            access_run_scan(
                facility_type,
                focus,
                issues,
                st.session_state.get("access_photo_upload") is not None,
            )
        st.session_state.access_show_draft = True
        st.session_state.current_page = "accessibility"
        changed = True
    elif action == "access_close_draft":
        st.session_state.access_show_draft = False
        st.session_state.current_page = "accessibility"
        changed = True
    elif action == "access_prepare_draft":
        facility_type, focus, issues = sync_access_controls_from_query()
        if not st.session_state.get("access_analysis"):
            access_run_scan(
                facility_type,
                focus,
                issues,
                st.session_state.get("access_photo_upload") is not None,
            )
        st.session_state.access_show_draft = True
        st.session_state.current_page = "accessibility"
        st.session_state.notice = "SendGrid payload 미리보기를 갱신했습니다."
        changed = True
    elif action == "access_send_draft":
        facility_type, focus, issues = sync_access_controls_from_query()
        report = st.session_state.get("access_analysis")
        if not report:
            report = access_run_scan(
                facility_type,
                focus,
                issues,
                st.session_state.get("access_photo_upload") is not None,
            )
        send_result = engine_bridge.send_access_official_email(
            report, default_destination=DEFAULT_DESTINATION
        )
        st.session_state.access_show_draft = True
        st.session_state.access_last_send = {
            "ok": send_result.get("ok"),
            "data_status": send_result.get("data_status"),
        }
        st.session_state.current_page = "accessibility"
        if send_result.get("ok"):
            st.session_state.notice = (
                "SendGrid로 공문 초안 발송을 요청했습니다. "
                "담당자 확인 후 공식 절차로 이어질 수 있습니다."
            )
        else:
            st.session_state.notice = str(
                send_result.get("message", "SendGrid 발송에 실패했습니다. 설정과 수신 주소를 확인해 주세요.")
            )
        changed = True
    elif action == "access_submit_draft":
        st.session_state.access_show_draft = False
        st.session_state.current_page = "accessibility"
        st.session_state.notice = "공문 초안 검토 요청이 등록되었습니다. 발송은 발송 준비 버튼에서 시도할 수 있습니다."
        changed = True
    elif action == "logout":
        st.session_state.logged_in = False
        st.session_state.authenticated = False
        st.session_state.auth_stage = "entry"
        st.session_state.current_page = "main"
        st.session_state.main_step = "start"
        st.session_state.pending_confirm = None
        st.session_state.auth_name = ""
        st.session_state.auth_email = ""
        for key in ("resume", "page", "step", "role", "user", "email"):
            if key in st.query_params:
                try:
                    del st.query_params[key]
                except Exception:
                    pass
        changed = True
    for key in (
        "nav_tab",
        "action",
        "schedule_time",
        "schedule_day_label",
        "schedule_time_label",
        "access_facility_type",
        "access_focus",
        "access_issue",
        "pending_next",
        "pending_point_key",
        "pending_bt_delta",
        "pending_confirm_buddy",
        "pending_confirm_class",
    ):
        if key in st.query_params:
            try:
                del st.query_params[key]
            except Exception:
                pass
    if changed and st.session_state.get("logged_in"):
        st.query_params["resume"] = "1"
        st.query_params["page"] = st.session_state.get("current_page", "main")
        st.query_params["step"] = st.session_state.get("main_step", "start")
        st.query_params["role"] = st.session_state.get("role", USER_ROLE)
        if st.session_state.get("user_name"):
            st.query_params["user"] = st.session_state.get("user_name")
        if st.session_state.get("user_email"):
            st.query_params["email"] = st.session_state.get("user_email")
    if changed:
        st.rerun()


def sync_resume_query_params() -> None:
    if not st.session_state.get("logged_in"):
        return
    st.query_params["resume"] = "1"
    st.query_params["page"] = st.session_state.get("current_page", "main")
    st.query_params["step"] = st.session_state.get("main_step", "start")
    st.query_params["role"] = st.session_state.get("role", USER_ROLE)
    if st.session_state.get("user_name"):
        st.query_params["user"] = st.session_state.get("user_name")
    if st.session_state.get("user_email"):
        st.query_params["email"] = st.session_state.get("user_email")


def render_user_topbar() -> None:
    name = st.session_state.get("user_name") or "반다비"
    points_value = int(st.session_state.get("bt_points", 3500))
    current_page = st.session_state.get("current_page", "main")
    icon_src = bandabi_icon_data_uri()
    logo_html = (
        f'<img class="brand-logo-img" src="{icon_src}" alt="반다비">'
        if icon_src
        else '<span class="brand-mark" style="margin:0;width:48px;height:48px;border-radius:18px;">B</span>'
    )

    tab_links = []
    base_query = {
        "resume": "1",
        "role": st.session_state.get("role", USER_ROLE),
        "user": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
        "step": st.session_state.get("main_step", "start"),
    }
    for page, label, icon_kind in USER_TABS:
        active = " active" if current_page == page else ""
        q = dict(base_query)
        q["nav_tab"] = page
        q["page"] = page
        href = "?" + urlencode({k: v for k, v in q.items() if v != ""})
        tab_links.append(
            f'<a class="app-tab{active}" href="{href}" target="_self">'
            f"{tab_icon_svg(icon_kind)}{esc(label)}</a>"
        )

    st.markdown(
        html_block(f"""
        <div class="user-topbar-shell">
            <header class="user-topbar" aria-label="반다비 AI 이용자 헤더">
                <div class="user-topbar-inner">
                    <div class="user-topbar-brand">
                        <div class="brand-logo-shell">{logo_html}</div>
                        <div class="user-topbar-copy">
                            <div class="user-topbar-title" role="heading" aria-level="1">
                                <span class="user-topbar-title-main">반다비 AI</span>
                                <span class="user-topbar-title-user">(User | {esc(name)}님)</span>
                            </div>
                            <div class="user-topbar-badges">
                                <span class="topbar-badge">이용자 모드</span>
                                <span class="topbar-badge topbar-badge-token">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                        <ellipse cx="12" cy="6.5" rx="7" ry="2.8" fill="currentColor" opacity=".22"/>
                                        <path d="M5 6.5v9c0 1.7 3.1 3 7 3s7-1.3 7-3v-9" stroke="currentColor" stroke-width="2"/>
                                        <ellipse cx="12" cy="6.5" rx="7" ry="2.8" stroke="currentColor" stroke-width="2"/>
                                        <path d="M5 11c0 1.7 3.1 3 7 3s7-1.3 7-3M5 14.5c0 1.7 3.1 3 7 3s7-1.3 7-3" stroke="currentColor" stroke-width="1.7"/>
                                    </svg>
                                    {points_value:,} BT
                                    <small>현금 환급·양도 불가</small>
                                </span>
                            </div>
                        </div>
                    </div>

                    <nav class="user-topbar-nav" aria-label="주요 메뉴">
                        <div class="app-tab-track">
                            {"".join(tab_links)}
                        </div>
                    </nav>

                    <div class="user-topbar-tools">
                        <a class="app-tool-btn" href="?action=high_contrast" target="_self" aria-label="고대비">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 3v18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                <path d="M12 3a9 9 0 0 1 0 18" fill="currentColor" opacity=".45"/>
                                <path d="M12 3a9 9 0 0 0 0 18" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            고대비
                        </a>
                        <a class="app-tool-btn" href="?action=voice" target="_self" aria-label="음성">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <rect x="9" y="4" width="6" height="11" rx="3" stroke="currentColor" stroke-width="2"/>
                                <path d="M6 11a6 6 0 0 0 12 0M12 17v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                            음성
                        </a>
                        <a class="app-tool-btn icon-only" href="?action=logout" target="_self" aria-label="로그아웃">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 3v9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                <path d="M8.5 6.5a7.5 7.5 0 1 0 9.7 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </header>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_admin_topbar() -> None:
    current_page = st.session_state.get("current_page", "dashboard")
    icon_src = bandabi_icon_data_uri()
    logo_html = (
        f'<img class="brand-logo-img" src="{icon_src}" alt="반다비">'
        if icon_src
        else '<span class="brand-mark" style="margin:0;width:48px;height:48px;border-radius:18px;">B</span>'
    )

    tab_links = []
    base_query = {
        "resume": "1",
        "role": ADMIN_ROLE,
        "user": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
        "step": st.session_state.get("main_step", "start"),
    }
    for page, label, icon_kind in ADMIN_TABS:
        active = " active" if current_page == page else ""
        q = dict(base_query)
        q["nav_tab"] = page
        q["page"] = page
        href = "?" + urlencode({k: v for k, v in q.items() if v != ""})
        tab_links.append(
            f'<a class="app-tab{active}" href="{href}" target="_self">'
            f"{tab_icon_svg(icon_kind)}{esc(label)}</a>"
        )

    st.markdown(
        html_block(f"""
        <div class="user-topbar-shell admin-topbar-shell">
            <header class="user-topbar admin-topbar" aria-label="반다비 AI 관리자 헤더">
                <div class="user-topbar-inner">
                    <div class="user-topbar-brand">
                        <div class="brand-logo-shell">{logo_html}</div>
                        <div class="user-topbar-copy">
                            <div class="user-topbar-title" role="heading" aria-level="1">
                                <span class="user-topbar-title-main">반다비 AI</span>
                                <span class="user-topbar-title-user">(Admin)</span>
                            </div>
                            <div class="user-topbar-badges">
                                <span class="topbar-badge topbar-badge-admin">기관 관리자</span>
                            </div>
                        </div>
                    </div>

                    <nav class="user-topbar-nav" aria-label="관리자 주요 메뉴">
                        <div class="app-tab-track admin-tab-track">
                            {"".join(tab_links)}
                        </div>
                    </nav>

                    <div class="user-topbar-tools">
                        <a class="app-tool-btn" href="?action=high_contrast" target="_self" aria-label="고대비">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 3v18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                <path d="M12 3a9 9 0 0 1 0 18" fill="currentColor" opacity=".45"/>
                                <path d="M12 3a9 9 0 0 0 0 18" stroke="currentColor" stroke-width="2"/>
                            </svg>
                            고대비
                        </a>
                        <a class="app-tool-btn" href="?action=voice" target="_self" aria-label="음성">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <rect x="9" y="4" width="6" height="11" rx="3" stroke="currentColor" stroke-width="2"/>
                                <path d="M6 11a6 6 0 0 0 12 0M12 17v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                            음성
                        </a>
                        <a class="app-tool-btn icon-only" href="?action=logout" target="_self" aria-label="로그아웃">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 3v9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                <path d="M8.5 6.5a7.5 7.5 0 1 0 9.7 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </header>
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_header() -> None:
    name = st.session_state.get("user_name") or "반다비"
    st.markdown(
        f"""
        <div class="bandabi-header">
            <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;flex-wrap:wrap;">
                <div style="display:flex;align-items:center;min-width:260px;">
                    <span class="brand-mark">B</span>
                    <div>
                        <p class="brand-title">반다비 AI</p>
                        <p class="brand-subtitle">{esc(role_label())} · {esc(name)}님</p>
                    </div>
                </div>
                <div class="chip-row" style="justify-content:flex-end;margin-top:0;">
                    <span class="chip">{esc(role_label())}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    btn_cols = st.columns([1, 1, 5, 1])
    with btn_cols[0]:
        if st.button("고대비", key="btn_high_contrast"):
            st.session_state.high_contrast = not bool(st.session_state.get("high_contrast"))
            st.rerun()
    with btn_cols[1]:
        if st.button("로그아웃", key="btn_logout"):
            for key in ("logged_in", "authenticated"):
                st.session_state[key] = False
            st.session_state.current_page = "main"
            st.session_state.pending_confirm = None
            st.rerun()

    st.markdown(
        """
        <p class="disclaimer">
        본 서비스는 생활체육 참여와 접근성 확인을 돕는 참고용 화면입니다.
        의료 진단, 처방, 치료 효과 판단, 법적 적합 판정 또는 행정 처분 판단을 대체하지 않습니다.
        </p>
        """,
        unsafe_allow_html=True,
    )


def nav_button(label: str, page: str, key: str) -> None:
    if st.button(label, key=key, type="primary" if st.session_state.current_page == page else "secondary"):
        if page == "dashboard" and st.session_state.get("role") != ADMIN_ROLE:
            st.session_state.notice = "기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다."
            st.session_state.current_page = "main"
        else:
            st.session_state.current_page = page
        st.rerun()


def render_nav() -> None:
    if st.session_state.get("role") == USER_ROLE:
        return

    st.markdown('<div class="tab-shell">', unsafe_allow_html=True)
    if st.session_state.get("role") == ADMIN_ROLE:
        st.radio("탭", ["기관용 대시보드"], index=0, horizontal=True, label_visibility="collapsed")
        st.session_state.current_page = "dashboard"
        st.markdown("</div>", unsafe_allow_html=True)
        return

    labels = ["AI 추천 및 이동지원 연계", "내 운동 일정 추천", "AI 기반 접근성 점검 보조"]
    page_by_label = {
        "AI 추천 및 이동지원 연계": "main",
        "내 운동 일정 추천": "schedule",
        "AI 기반 접근성 점검 보조": "accessibility",
    }
    label_by_page = {value: key for key, value in page_by_label.items()}
    current_label = label_by_page.get(st.session_state.get("current_page", "main"), labels[0])
    selected_label = st.radio(
        "탭",
        labels,
        index=labels.index(current_label),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
    )
    st.session_state.current_page = page_by_label[selected_label]

    if st.session_state.get("current_page") == "dashboard":
        st.session_state.notice = "기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다."
        st.session_state.current_page = "main"
    st.markdown("</div>", unsafe_allow_html=True)


def render_notice() -> None:
    if st.session_state.get("center_warning"):
        st.warning(UNAVAILABLE_MESSAGE)
        st.session_state.center_warning = False

    notice = st.session_state.get("notice")
    if notice:
        st.info(notice)
        st.session_state.notice = ""


def render_flow_steps() -> None:
    if st.session_state.get("main_step") == "start":
        return
    order = ["route", "care", "class", "report"]
    labels = {
        "route": "MAIN01 경로분석",
        "care": "MAIN02 버디",
        "class": "Program AI",
        "report": "MAIN03 리포트",
    }
    current = st.session_state.get("main_step", "route")
    current_index = order.index(current) if current in order else len(order)
    html_steps = []
    for index, step in enumerate(order):
        status = "active" if step == current else "done" if index < current_index else ""
        html_steps.append(f"<span class='flow-step {status}'>{esc(labels[step])}</span>")
    st.markdown(f"<div class='flow-steps'>{''.join(html_steps)}</div>", unsafe_allow_html=True)


def build_route_analysis() -> dict[str, Any]:
    origin = st.session_state.get("origin") or "김포 구래역 1번 출구"
    support = st.session_state.get("support_type") or SUPPORT_TYPES[0]
    return engine_bridge.run_route_analysis(
        origin,
        DEFAULT_DESTINATION,
        support,
        buddy_matching=bool(st.session_state.get("buddy_matching")),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        force_refresh_apis=bool(st.session_state.pop("route_api_force_refresh", False)),
    )


def route_map_svg(result: dict[str, Any]) -> str:
    """Small native SVG that follows the current route/API result."""
    route_map = result.get("route_map") if isinstance(result.get("route_map"), dict) else {}
    transfers_text = str(result.get("transfers") or route_map.get("transfers") or "0회")
    transfer_digits = "".join(ch for ch in transfers_text if ch.isdigit())
    transfer_count = int(transfer_digits or 0)
    route_note = str(route_map.get("facility") or result.get("facility_access") or "센터 진입 동선 확인")
    time_note = str(route_map.get("total") or result.get("total_time") or "예상 시간")
    bus_note = str(route_map.get("bus") or result.get("bus_number") or "버스 확인")
    weather_note = str(route_map.get("weather") or result.get("weather_adjustment") or "날씨 확인")
    caution_note = str(route_map.get("caution") or "주의 지점 확인")
    middle_label = "환승2" if transfer_count >= 2 else "환승" if transfer_count == 1 else "버스"
    risk = str(result.get("walk_risk", "중간"))
    caution_color = "#9d3654" if "중간" in risk or "높" in risk else "#6b4fa0"
    bus_short = bus_note if len(bus_note) <= 12 else bus_note[:11] + "…"
    weather_short = weather_note if len(weather_note) <= 28 else weather_note[:27] + "…"
    caution_short = caution_note if len(caution_note) <= 32 else caution_note[:31] + "…"
    route_short = route_note if len(route_note) <= 30 else route_note[:29] + "…"
    return f"""
    <div class="route-map">
      <svg viewBox="0 0 860 310" style="display:block;width:100%;height:auto;" role="img" aria-label="추천 경로 도식">
        <defs>
          <linearGradient id="routeGradientNative" x1="0" x2="1">
            <stop offset="0%" stop-color="#4a2d7a"/>
            <stop offset="100%" stop-color="#b8acd8"/>
          </linearGradient>
        </defs>
        <path d="M100 205 C205 205, 235 125, 345 125 S 520 195, 625 180 S 730 105, 790 105"
          fill="none" stroke="#dcd4ec" stroke-width="28" stroke-linecap="round"/>
        <path class="route-line" d="M100 205 C205 205, 235 125, 345 125 S 520 195, 625 180 S 730 105, 790 105"
          fill="none" stroke="url(#routeGradientNative)" stroke-width="10" stroke-linecap="round"/>
        <circle cx="90" cy="205" r="27" fill="#dcfce7"/>
        <circle cx="340" cy="125" r="27" fill="#e0f2fe"/>
        <circle cx="625" cy="180" r="27" fill="#f3e8ff"/>
        <circle cx="790" cy="105" r="27" fill="#fef3c7"/>
        <text x="90" y="211" text-anchor="middle" fill="#166534" font-size="13" font-weight="900">출발</text>
        <text x="340" y="131" text-anchor="middle" fill="#0e7490" font-size="13" font-weight="900">{esc(middle_label)}</text>
        <text x="625" y="186" text-anchor="middle" fill="#6d28d9" font-size="13" font-weight="900">하차</text>
        <text x="790" y="111" text-anchor="middle" fill="#92400e" font-size="13" font-weight="900">센터</text>
        <text x="252" y="96" fill="#7868a0" font-size="14" font-weight="800">{esc(time_note)}</text>
        <text x="300" y="160" fill="#0e7490" font-size="12" font-weight="800">{esc(bus_short)}</text>
        <text x="560" y="224" fill="#7868a0" font-size="14">{esc(route_short)}</text>
        <text x="410" y="164" fill="{caution_color}" font-size="13" font-weight="900">{esc(caution_short)}</text>
        <text x="510" y="76" fill="#7868a0" font-size="12" font-weight="700">{esc(weather_short)}</text>
      </svg>
    </div>
    """


def start_analysis() -> None:
    if st.session_state.get("destination_choice") == UNAVAILABLE_DESTINATION:
        block_unavailable_destination()
        return
    st.session_state.destination = DEFAULT_DESTINATION
    st.session_state.route_public_api_cache = None
    st.session_state.route_api_force_refresh = True
    st.session_state.route_result = None
    st.session_state.route_analysis_result = None
    st.session_state.route_inputs_fingerprint = ""
    st.session_state.main_step = "route"
    st.session_state.current_page = "main"
    st.session_state.pending_confirm = None


def open_confirm(title: str, subtitle: str, message: str, next_step: str, **extra: Any) -> None:
    st.session_state.pending_confirm = {
        "title": title,
        "subtitle": subtitle,
        "message": message,
        "next_step": next_step,
        **extra,
    }


def render_step_action_buttons(
    *,
    container_key: str,
    secondary_label: str,
    secondary_key: str,
    primary_label: str = "확정하기",
    primary_key: str,
    on_secondary: Any,
    on_primary: Any,
    align: str = "end",
) -> None:
    """HTML `flex justify-end gap-3` — secondary + confirm on the right."""
    with st.container(key=container_key):
        if align == "end":
            spacer, actions = st.columns([1.65, 1], gap="small")
            with spacer:
                pass
            target = actions
        else:
            target = st.container()
        with target:
            btn_cols = st.columns(2, gap="small")
            with btn_cols[0]:
                st.button(
                    secondary_label,
                    key=secondary_key,
                    use_container_width=True,
                    on_click=on_secondary,
                )
            with btn_cols[1]:
                st.markdown('<div class="confirm-action">', unsafe_allow_html=True)
                st.button(
                    primary_label,
                    key=primary_key,
                    type="primary",
                    use_container_width=True,
                    on_click=on_primary,
                )
                st.markdown("</div>", unsafe_allow_html=True)


def _cancel_pending_confirm() -> None:
    st.session_state.pending_confirm = None


def apply_pending_confirm() -> None:
    pending = st.session_state.get("pending_confirm") or {}
    next_step = (
        pending.get("next_step")
        or st.query_params.get("pending_next")
        or st.query_params.get("step")
        or st.session_state.get("main_step", "start")
    )
    if next_step not in {"start", "route", "care", "class", "report", "guardian"}:
        next_step = "start"

    point_key = pending.get("point_key") or st.query_params.get("pending_point_key")
    point_amounts = {
        "route_points_awarded": 500,
        "report_points_awarded": 300,
        "accessibility_points_awarded": 200,
    }
    if point_key in point_amounts:
        try:
            bt_delta = int(
                pending.get("bt_delta")
                or st.query_params.get("pending_bt_delta")
                or point_amounts[point_key]
            )
        except (TypeError, ValueError):
            bt_delta = point_amounts[point_key]
        add_points(point_amounts.get(str(point_key), bt_delta), str(point_key))

    if pending.get("confirm_buddy") or st.query_params.get("pending_confirm_buddy") == "1":
        st.session_state.buddy_confirmed = True
    if pending.get("confirm_class") or st.query_params.get("pending_confirm_class") == "1":
        st.session_state.class_confirmed = True
    st.session_state.main_step = next_step
    st.session_state.current_page = "main"
    st.session_state.notice = pending.get("toast", "")
    st.session_state.pending_confirm = None
    sync_resume_query_params()


def main_resume_query(*, extra: dict[str, str] | None = None) -> dict[str, str]:
    query = {
        "resume": "1",
        "page": "main",
        "step": st.session_state.get("main_step", "start"),
        "role": st.session_state.get("role", USER_ROLE),
        "user": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
    }
    if extra:
        query.update(extra)
    return {k: v for k, v in query.items() if v != ""}


def render_pending_confirm() -> None:
    pending = st.session_state.get("pending_confirm")
    if not pending:
        return
    next_step = str(pending.get("next_step") or st.session_state.get("main_step", "start"))
    ok_extra = {
        "action": "pending_ok",
        "step": next_step,
        "pending_next": next_step,
    }
    if pending.get("point_key"):
        ok_extra["pending_point_key"] = str(pending.get("point_key"))
        ok_extra["pending_bt_delta"] = str(pending.get("bt_delta", ""))
    if pending.get("confirm_buddy"):
        ok_extra["pending_confirm_buddy"] = "1"
    if pending.get("confirm_class"):
        ok_extra["pending_confirm_class"] = "1"

    cancel_href = "?" + urlencode(main_resume_query(extra={"action": "pending_cancel"}))
    ok_href = "?" + urlencode(main_resume_query(extra=ok_extra))
    st.markdown(
        f"""
        <div class="section-card pending-confirm-card">
            <p class="tiny-label">Confirm</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-weight:900;">{esc(pending.get("title", "확정 요청"))}</h2>
            <p class="section-copy">{esc(pending.get("subtitle", ""))}</p>
            <div class="notice-box" style="margin-top:16px;">{esc(pending.get("message", ""))}</div>
            <div class="pending-confirm-actions">
                <a class="pending-confirm-btn pending-confirm-btn-cancel" href="{esc(cancel_href)}" target="_self">취소</a>
                <a class="pending-confirm-btn pending-confirm-btn-ok" href="{esc(ok_href)}" target="_self">확인</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start() -> None:
    name = st.session_state.get("user_name") or "반다비"
    with st.container(key="start_shell"):
        st.markdown(
            html_block(f"""
                <section class="start-card">
                    <p class="start-kicker">Start</p>
                    <h2 class="start-greeting">반갑습니다, {esc(name)}님 :)</h2>
                    <p class="start-lead">오늘 운동, 갈 수 있는 경로부터 확인해요.</p>
                    <p class="start-copy">필요한 정보만 입력하면 경로·동행·강습·리포트 화면이 순서대로 이어집니다.</p>
            """),
            unsafe_allow_html=True,
        )

        st.markdown('<div class="start-grid-shell">', unsafe_allow_html=True)
        col1, col2 = st.columns([1.05, 1])
        with col1:
            st.markdown('<div class="start-fields">', unsafe_allow_html=True)
            st.markdown('<span class="start-label">접근성 지원 필요 유형</span>', unsafe_allow_html=True)
            st.selectbox(
                "접근성 지원 필요 유형",
                SUPPORT_TYPES,
                key="support_type",
                label_visibility="collapsed",
            )
            st.markdown('<span class="start-label">출발지</span>', unsafe_allow_html=True)
            st.text_input(
                "출발지",
                key="origin",
                label_visibility="collapsed",
                placeholder="예: 김포 구래역 1번 출구",
            )
            st.markdown('<span class="start-label">목적지</span>', unsafe_allow_html=True)
            st.selectbox(
                "목적지",
                [DEFAULT_DESTINATION, UNAVAILABLE_DESTINATION],
                key="destination_choice",
                on_change=block_unavailable_destination,
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                html_block("""
                <div class="start-tile-grid">
                    <div class="start-tile">보호자 알림</div>
                    <div class="start-tile">버디 매칭</div>
                    <div class="start-tile">강습 추천</div>
                    <div class="start-tile">리포트 수신</div>
                </div>
                """),
                unsafe_allow_html=True,
            )
            st.markdown('<div class="start-action-wrap">', unsafe_allow_html=True)
            start_href = "?" + urlencode(
                {
                    "resume": "1",
                    "page": "main",
                    "step": "start",
                    "role": st.session_state.get("role", USER_ROLE),
                    "user": st.session_state.get("user_name", ""),
                    "email": st.session_state.get("user_email", ""),
                    "origin": st.session_state.get("origin") or "",
                    "action": "start_ai",
                }
            )
            zap_src = zap_icon_data_uri()
            st.markdown(
                f'<a class="start-ai-link" href="{esc(start_href)}" target="_self">'
                f'<img class="start-ai-icon" src="{esc(zap_src)}" alt="">AI 추천 시작</a>',
                unsafe_allow_html=True,
            )
            st.components.v1.html(
                """
                <script>
                (function () {
                  const root = window.parent.document;
                  const link = root.querySelector(".start-action-wrap a.start-ai-link");
                  if (!link || link.dataset.originBound === "1") return;
                  link.dataset.originBound = "1";
                  link.addEventListener("click", function () {
                    const inputs = root.querySelectorAll('[data-testid="stTextInput"] input');
                    let origin = "";
                    for (const input of inputs) {
                      const placeholder = input.getAttribute("placeholder") || "";
                      if (placeholder.includes("구래역") || placeholder.includes("출발")) {
                        origin = (input.value || "").trim();
                        break;
                      }
                    }
                    if (!origin) return;
                    try {
                      const url = new URL(link.href, window.parent.location.href);
                      url.searchParams.set("origin", origin);
                      link.href = url.pathname + url.search;
                    } catch (err) {}
                  });
                })();
                </script>
                """,
                height=0,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("selected_schedule"):
            st.info(f"선택한 일정: {st.session_state.selected_schedule}")

        st.markdown(
            """
            <p class="start-footnote">
                본 AI 결과는 이용자 편의를 위한 추천 정보이며, 최종 이용 여부와 운영 확정은 이용자 및 운영기관이 결정합니다.
            </p>
            </section>
            """,
            unsafe_allow_html=True,
        )


def _route_inputs_fingerprint() -> str:
    return "|".join(
        [
            str(st.session_state.get("origin") or ""),
            str(st.session_state.get("destination") or DEFAULT_DESTINATION),
            str(st.session_state.get("support_type") or ""),
            str(st.session_state.get("destination_choice") or ""),
        ]
    )


def render_route() -> None:
    fingerprint = _route_inputs_fingerprint()
    cached = st.session_state.get("route_result")
    need_build = (
        not cached
        or st.session_state.get("route_inputs_fingerprint") != fingerprint
        or st.session_state.get("route_api_force_refresh")
    )
    if need_build:
        with st.spinner("이동 가능성을 계산하고 있어요..."):
            cached = build_route_analysis()
        st.session_state.route_result = cached
        st.session_state.route_analysis_result = cached
        st.session_state.route_inputs_fingerprint = fingerprint
        st.session_state.route_api_force_refresh = False
    result = cached
    route_warnings = result.get("route_warnings") or []
    warning_items = route_warnings[:4] or ["현장 상황에 따라 승하차 위치와 센터 진입 동선은 한 번 더 확인해 주세요."]
    warning_html = "".join(f"<li>{esc(item)}</li>" for item in warning_items)
    bus_detail = result.get("bus_detail") if isinstance(result.get("bus_detail"), dict) else {}
    weather_detail = result.get("weather_detail") if isinstance(result.get("weather_detail"), dict) else {}
    facility_detail = result.get("facility_detail") if isinstance(result.get("facility_detail"), dict) else {}
    distance = result.get("distance_km")
    time_caption = f"좌표 기준 약 {distance}km · {result.get('generated_at', '')}" if distance not in (None, "") else "좌표·API 조합 참고"

    section_intro(
        "MAIN01",
        "AI 기반 도착 가능성 / 경로분석",
        result.get("status_line", "연동 상태 확인 중") + ". 장거리 출발지는 비현실적인 짧은 시간으로 표시하지 않습니다.",
        [result["origin"], result["destination"], result["support"]],
    )

    st.markdown(
        html_block(f"""
        <div class="section-card">
            <p class="tiny-label">추천 경로</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-size:24px;font-weight:900;line-height:1.28;">{esc(result["recommended_route"])}</h2>
            <p class="section-copy">{esc(result["opinion"])}</p>
            {route_map_svg(result)}
            <div class="route-warning-panel">
                <p class="route-warning-title">주의해야 할 점</p>
                <ul class="route-warning-list">{warning_html}</ul>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    with cols[0]:
        metric_card("총 시간", result["total_time"], time_caption)
    with cols[1]:
        metric_card("도보", result["walk_time"], "센터 주변 마지막 접근 구간 포함")
    with cols[2]:
        metric_card("환승", result["transfers"], f"{result.get('bus_number') or '버스 노선'} 기준 확인")
    with cols[3]:
        metric_card("대체 이동수단", result["alternative"], "이동지원센터 연계 검토")

    cols = st.columns(4)
    with cols[0]:
        route_detail_card(
            "도보 위험도",
            result["walk_risk"],
            "보행 환경과 마지막 접근 구간 확인",
            details=warning_items[:2],
            badge="AI score",
        )
    with cols[1]:
        route_detail_card(
            "날씨 보정",
            weather_detail.get("headline") or "날씨 확인 필요",
            weather_detail.get("caution") or result["weather_adjustment"],
            details=weather_detail.get("details") or [result["weather_adjustment"]],
            badge=weather_detail.get("badge", ""),
        )
    with cols[2]:
        route_detail_card(
            "시설 접근성",
            result["facility_access"],
            facility_detail.get("caption") or "센터 주출입구, 승강기, 접근 가능한 화장실 확인",
            details=facility_detail.get("details") or ["주출입구", "승강기", "접근 가능한 화장실"],
            badge=facility_detail.get("badge", ""),
        )
    with cols[3]:
        route_detail_card(
            "버스 도착",
            result["bus_arrival"],
            bus_detail.get("caption") or "TAGO 버스 도착 정보",
            details=bus_detail.get("details") or [result.get("bus_number", ""), "출발 전 재확인 권장"],
            badge=bus_detail.get("badge", ""),
        )

    st.markdown(
        """
        <div class="notice-box">
        운영 확정 요청을 등록하면 참여 인센티브 500BT가 적립됩니다. 반다비 포인트는 현금 환급·양도·재판매가 불가합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    def _route_retry() -> None:
        st.session_state.main_step = "start"
        st.rerun()

    def _route_confirm() -> None:
        open_confirm(
            "운영 확정 요청이 등록되었습니다.",
            "예약·이동·동행 플랜이 다음 단계로 연결됩니다.",
            "참여 인센티브 500BT가 적립됩니다. 현금 환급·양도·재판매는 불가하며 생활체육 서비스 혜택으로만 사용할 수 있습니다.",
            "care",
            bt_delta=500,
            point_key="route_points_awarded",
            toast="경로가 확정되었습니다. 버디 추천 화면으로 이동합니다.",
        )

    with st.container(key="route_plan_banner"):
        copy_col, action_col = st.columns([1.45, 1], gap="medium")
        with copy_col:
            st.markdown(
                """
                <p class="route-plan-title">예약·이동·동행 플랜이 준비됐어요</p>
                <p class="route-plan-sub">확정하면 버디 후보와 강습 추천으로 이어집니다.</p>
                """,
                unsafe_allow_html=True,
            )
        with action_col:
            btn_cols = st.columns(2, gap="small")
            with btn_cols[0]:
                if st.button("다시하기", key="route_retry", use_container_width=True):
                    _route_retry()
            with btn_cols[1]:
                st.markdown('<div class="confirm-action">', unsafe_allow_html=True)
                st.button(
                    "확정하기",
                    key="route_confirm",
                    type="primary",
                    use_container_width=True,
                    on_click=_route_confirm,
                )
                st.markdown("</div>", unsafe_allow_html=True)


def buddy_for_support() -> dict[str, str]:
    support = st.session_state.get("support_type", SUPPORT_TYPES[0])
    if "시각" in support:
        return {"name": "이하늘", "meta": "음성 안내 선호 · 오전 시간대 · 같은 센터 이용"}
    if "청각" in support:
        return {"name": "문서우", "meta": "문자 안내 선호 · 접수 동선 경험 · 같은 프로그램 이용"}
    if "단계" in support:
        return {"name": "최다온", "meta": "천천히 안내 가능 · 소그룹 참여 경험 · 첫 방문 동행"}
    return {"name": "김지오", "meta": "같은 시간대 · 수중 생활체육 이용 · 같은 센터 이용"}


def render_buddy() -> None:
    buddy = buddy_for_support()
    section_intro(
        "MAIN02",
        "인증 기반 버디 후보 추천",
        "혼자 이동하는 부담을 줄이고, 기관 확인 후 버디와 함께 체육 시설을 이용합니다.",
        ["실명·연락처 확정 전 비공개", "상호 동의", "관리자 확인 필요"],
    )

    cols = st.columns(3)
    with cols[0]:
        soft_card("첫 방문 버디", f"{buddy['name']} 회원", buddy["meta"], ["동행 후보", "신고·차단 지원"])
    with cols[1]:
        soft_card("센터 도우미", "500m 전 대기", "센터 도착 전 안내 데스크 연결과 동선 확인을 돕습니다.", ["운영 확인"])
    with cols[2]:
        soft_card("보호자 모드", "출석 알림 공유", "강습 확정 후 보호자에게 공유할 요약 문구를 준비합니다.", ["개인정보 최소화"])

    st.markdown(
        """
        <div class="notice-box">
        버디 매칭은 기관 인증 이용자에 한해 제공되며, 상호 동의 및 관리자 확인 후 연결됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    skip_href = "?" + urlencode(main_resume_query(extra={"action": "care_skip", "step": "class"}))
    confirm_href = "?" + urlencode(main_resume_query(extra={"action": "care_confirm", "step": "care"}))
    st.markdown(
        f"""
        <div class="step-action-links">
            <a class="step-action-link secondary" href="{esc(skip_href)}" target="_self">건너뛰기</a>
            <a class="step-action-link primary" href="{esc(confirm_href)}" target="_self">확정하기</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def current_instructor() -> dict[str, str]:
    idx = int(st.session_state.get("instructor_index", 0)) % len(INSTRUCTORS)
    return INSTRUCTORS[idx]


def render_class() -> None:
    instructor = current_instructor()
    section_intro(
        "Program AI",
        "강습·지도자 추천",
        "접근성 지원 필요 유형, 운동 목적, 선호 시간, 지도자 전문성을 함께 고려한 화면용 추천입니다.",
        ["생활체육 참여 참고자료", "최종 참여는 이용자와 운영기관 확인"],
    )

    st.markdown(
        f"""
        <div class="section-card">
            <p class="tiny-label">추천 지도자</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-size:30px;font-weight:900;">{esc(instructor["name"])} 지도자</h2>
            <p class="section-copy">{esc(instructor["summary"])}</p>
            <div class="chip-row">
                <span class="chip">{esc(instructor["time"])}</span>
                <span class="chip">{esc(instructor["group"])}</span>
                <span class="chip">김포 반다비체육센터</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    next_href = "?" + urlencode(main_resume_query(extra={"action": "class_next", "step": "class"}))
    confirm_href = "?" + urlencode(main_resume_query(extra={"action": "class_confirm", "step": "class"}))
    st.markdown(
        f"""
        <div class="step-action-links">
            <a class="step-action-link secondary" href="{esc(next_href)}" target="_self">다른 지도자</a>
            <a class="step-action-link primary" href="{esc(confirm_href)}" target="_self">확정하기</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def guardian_summary_text() -> str:
    result = st.session_state.get("route_result") or {}
    buddy = "버디 연결 요청 등록" if st.session_state.get("buddy_confirmed") else "버디 미연결"
    instructor = current_instructor()["name"] if st.session_state.get("class_confirmed") else "추천 검토 중"
    return (
        f"{st.session_state.get('user_name') or '이용자'}님은 {DEFAULT_DESTINATION} 생활체육 참여 흐름을 진행했습니다. "
        f"이동 계획은 {result.get('total_time', '확인 중')} 기준으로 준비되었고, 동행 상태는 {buddy}, "
        f"강습 지도자는 {instructor}입니다. 본 요약에는 진단명, 상세 건강정보, 상세 주소가 포함되지 않습니다. "
        "실제 외부 전송은 연결하지 않았습니다."
    )


def report_rag_source_label() -> str:
    cache = st.session_state.get("report_rag_cache")
    if not cache:
        cache = {"display_source": "bm25_local"}
        st.session_state.report_rag_cache = cache
    source = str(cache.get("display_source", "fallback"))
    return f"생활체육 RAG source: {source}"


def render_report() -> None:
    section_intro(
        "MAIN03",
        "AI 생활체육 리포트",
        "운동 후 변화와 다음 참여 가능성을 쉽게 확인하는 보호자 공유용 요약 화면입니다.",
        ["리포트 저장 +300BT", "개인정보 최소화", "참고용 지표"],
    )

    route_result = st.session_state.get("route_result") or {}
    total_time = route_result.get("total_time", "이동 계획 확인 완료")
    bus_number = route_result.get("bus_number") or "센터 이동 노선 확인"
    buddy_state = "버디 연결 요청 등록" if st.session_state.get("buddy_confirmed") else "버디 없이 참여 가능"
    instructor = current_instructor()["name"] if st.session_state.get("class_confirmed") else "추천 지도자 검토"
    source_label = report_rag_source_label()

    st.markdown(
        html_block(f"""
        <div class="report-native-grid">
            <article class="report-native-card">
                <p class="report-native-label">성취도 점수</p>
                <p class="report-native-value">82점</p>
                <p class="report-native-copy">{esc(source_label)} · 경로·동행·강습 추천 흐름을 완료했습니다.</p>
                <ul class="report-native-list">
                    <li>참여 준비 완료</li>
                    <li>이동 계획 확인</li>
                </ul>
            </article>
            <article class="report-native-card">
                <p class="report-native-label">지속참여 점수</p>
                <p class="report-native-value">76점</p>
                <p class="report-native-copy">다음 참여 가능성을 높이려면 같은 시간대 예약과 이동지원 여유 시간을 함께 잡는 구성이 좋습니다.</p>
                <ul class="report-native-list">
                    <li>다음 일정 추천</li>
                    <li>무리 없는 반복 참여</li>
                </ul>
            </article>
            <article class="report-native-card">
                <p class="report-native-label">오늘의 참여 요약</p>
                <p class="report-native-value">경로·동행·강습 흐름 완료</p>
                <p class="report-native-copy">예상 이동은 {esc(str(total_time))} 기준이며, {esc(str(bus_number))} 정보와 센터 접근성 확인 결과를 함께 참고했습니다.</p>
                <ul class="report-native-list">
                    <li>{esc(buddy_state)}</li>
                    <li>{esc(instructor)} 지도자</li>
                </ul>
            </article>
            <article class="report-native-card">
                <p class="report-native-label">다음 생활체육 가이드</p>
                <p class="report-native-value">도착 15분 여유</p>
                <p class="report-native-copy">강습 전후 컨디션을 확인하고, 이동지원 배차와 센터 진입 동선을 한 번 더 확인하는 참여 계획을 권장합니다.</p>
                <ul class="report-native-list">
                    <li>수분 섭취</li>
                    <li>쉬운 강도</li>
                    <li>보호자 공유 요약</li>
                </ul>
            </article>
            <article class="report-native-card wide">
                <p class="report-native-label">포인트 적립 안내</p>
                <p class="report-native-copy">리포트 저장 시 참여 인센티브 300BT가 적립됩니다. 반다비 포인트는 현금 환급·양도·재판매가 불가합니다.</p>
            </article>
        </div>
        """),
        unsafe_allow_html=True,
    )

    with st.container(key="report_action_row"):
        if st.button("리포트 저장 및 보호자 공유 요약 보기", key="report_save", type="primary"):
            add_points(300, "report_points_awarded")
            st.session_state.report_saved = True
            st.session_state.guardian_summary = guardian_summary_text()
            st.session_state.main_step = "guardian"
            sync_resume_query_params()
            st.rerun()


def render_guardian_summary() -> None:
    summary = st.session_state.get("guardian_summary") or guardian_summary_text()
    st.session_state.guardian_summary = summary
    section_intro(
        "Guardian Share",
        "보호자 공유 요약",
        "실제 외부 전송 없이 공유 문구만 생성합니다. 민감한 건강정보와 상세 주소는 포함하지 않습니다.",
        ["외부 전송 없음", "개인정보 최소화", "복사 가능한 요약"],
    )
    st.text_area("보호자 공유용 문구", value=summary, height=180)
    if st.button("처음 입력 화면으로 돌아가기", key="guardian_back"):
        reset_user_flow()
        st.rerun()


def render_main_page() -> None:
    st.markdown('<div class="journey-shell">', unsafe_allow_html=True)
    render_flow_steps()
    pending = st.session_state.get("pending_confirm")
    if pending:
        render_pending_confirm()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    step = st.session_state.get("main_step", "start")
    if step not in {"start", "route", "care", "class", "report", "guardian"}:
        st.session_state.main_step = "start"
        step = "start"

    if step == "start":
        render_start()
    elif step == "route":
        render_route()
    elif step == "care":
        render_buddy()
    elif step == "class":
        render_class()
    elif step == "report":
        render_report()
    else:
        render_guardian_summary()

    st.markdown("</div>", unsafe_allow_html=True)


def schedule_next_js_weekday(target_day: int) -> datetime:
    today = datetime.now()
    today_js = (today.weekday() + 1) % 7
    diff = target_day - today_js
    if diff <= 0:
        diff += 7
    return today + timedelta(days=diff)


def format_schedule_date_label(dt: datetime) -> str:
    js_days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    js_day = (dt.weekday() + 1) % 7
    return f"{dt.year} / {dt.strftime('%m')} / {dt.strftime('%d')} / {js_days[js_day]}"


def schedule_resume_query(*, extra: dict[str, str] | None = None) -> dict[str, str]:
    query = {
        "resume": "1",
        "page": "schedule",
        "step": st.session_state.get("main_step", "start"),
        "role": st.session_state.get("role", USER_ROLE),
        "user": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
    }
    if extra:
        query.update(extra)
    return query


def make_schedule_recommendations(days: list[str], time_range: str) -> list[dict[str, str]]:
    if not days:
        days = ["화", "목"]
    weekday_to_js = {"일": 0, "월": 1, "화": 2, "수": 3, "목": 4, "금": 5, "토": 6}
    weekday_label = {"일": "일요일", "월": "월요일", "화": "화요일", "수": "수요일", "목": "목요일", "금": "금요일", "토": "토요일"}
    time_sets = {
        "오전 10시 전후": ["10:00", "11:00", "14:00"],
        "오후 2시 전후": ["14:00", "15:00", "16:00"],
        "오후 4시 전후": ["16:00", "17:00", "14:00"],
    }
    times = time_sets.get(time_range, time_sets["오전 10시 전후"])
    primary_day = days[0]
    second_day = days[1] if len(days) > 1 else days[0]
    fallback_day = "금" if primary_day != "금" else "목"
    first = format_schedule_date_label(schedule_next_js_weekday(weekday_to_js.get(primary_day, 2)))
    second = format_schedule_date_label(schedule_next_js_weekday(weekday_to_js.get(second_day, 4)))
    third = format_schedule_date_label(schedule_next_js_weekday(weekday_to_js.get(fallback_day, 5)))
    first_label = f"{first} {times[0]}"
    second_label = f"{second} {times[1]}"
    third_label = f"{third} {times[2]}"
    return [
        {
            "rank_label": "1순위 추천",
            "rank_tone": "purple",
            "headline": f"{weekday_label.get(primary_day, '화요일')} {times[0]}",
            "date_label": first,
            "reason": "지도자 가능 · 이동지원 가능성 높음 · 버디 후보 있음",
            "badge": "추천",
            "badge_tone": "good",
            "full_label": first_label,
            "primary": True,
        },
        {
            "rank_label": "2순위 후보",
            "rank_tone": "blue",
            "headline": f"{weekday_label.get(second_day, '목요일')} {times[1]}",
            "date_label": second,
            "reason": "지도자 가능 · 이동지원 혼잡 가능성 있음",
            "badge": "보통",
            "badge_tone": "normal",
            "full_label": second_label,
            "primary": False,
        },
        {
            "rank_label": "대체 후보",
            "rank_tone": "amber",
            "headline": f"{weekday_label.get(fallback_day, '금요일')} {times[2]}",
            "date_label": third,
            "reason": "퇴근 시간대 혼잡 · 버디 후보 없음 · 이동지원 사전 확인 권장",
            "badge": "주의",
            "badge_tone": "warn",
            "full_label": third_label,
            "primary": False,
        },
    ]


def schedule_slot_card_html(item: dict[str, str]) -> str:
    selected = st.session_state.get("schedule_selected_time") == item.get("full_label")
    classes = ["schedule-slot-card"]
    if item.get("primary"):
        classes.append("primary")
    if selected:
        classes.append("selected")
    card_class = " ".join(classes)
    select_href = "?" + urlencode(
        schedule_resume_query(extra={"action": "schedule_select", "schedule_time": item["full_label"]})
    )
    return f"""
    <a class="{card_class}" href="{esc(select_href)}" target="_self">
        <div class="schedule-slot-head">
            <div>
                <p class="schedule-slot-rank {esc(item.get('rank_tone', 'purple'))}">{esc(item.get('rank_label', ''))}</p>
                <h4 class="schedule-slot-title">
                    {esc(item.get('headline', ''))}
                    <span class="schedule-slot-date">{esc(item.get('date_label', ''))}</span>
                </h4>
                <p class="schedule-slot-reason">{esc(item.get('reason', ''))}</p>
            </div>
            <span class="schedule-slot-badge {esc(item.get('badge_tone', 'good'))}">{esc(item.get('badge', ''))}</span>
        </div>
    </a>
    """


def build_schedule_results_html() -> str:
    recommendations = list(st.session_state.get("schedule_recommendations") or [])
    if not recommendations:
        calendar_plus_icon = """
            <svg class="schedule-empty-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="4" y="5.5" width="16" height="15" rx="3" fill="currentColor"/>
                <path d="M8 3.5v4M16 3.5v4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>
                <path d="M8 12.5h8M12 8.5v8" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
            </svg>
        """
        return (
            "<div class='schedule-empty'>"
            f"<div>{calendar_plus_icon}"
            "<div class='big'>가능한 시간 찾기를 누르면 추천 시간이 표시됩니다</div>"
            "<div class='small'>강습·이동지원·버디 후보를 함께 계산합니다.</div></div>"
            "</div>"
        )

    cards = "".join(schedule_slot_card_html(item) for item in recommendations[:3])
    selected = st.session_state.get("schedule_selected_time") or ""
    confirm_html = ""
    toast_html = ""
    if selected:
        continue_href = "?" + urlencode(schedule_resume_query(extra={"action": "schedule_continue"}))
        confirm_html = f"""
        <div class="schedule-confirm-box">
            <div>
                <p class="schedule-confirm-title">{esc(selected)} 일정이 선택됐어요</p>
                <p class="schedule-confirm-copy">이 시간으로 예약 흐름을 이어가면 경로·버디·강습 추천과 연결됩니다.</p>
            </div>
            <a class="schedule-confirm-link" href="{esc(continue_href)}" target="_self">이 시간으로 예약 이어가기</a>
        </div>
        """
        toast_html = f"<div class='schedule-toast'>{esc(selected)} 일정이 선택되었습니다.</div>"
    top_pick = st.session_state.get("schedule_top_pick") or recommendations[0]["full_label"]
    optimize_html = (
        f"<div class='schedule-optimize-result'>"
        f"가장 추천하는 시간은 <b>{esc(top_pick)}</b>입니다. "
        "이동지원 연계 가능성이 높고, 같은 센터를 이용하는 버디 후보가 있습니다."
        "</div>"
    )
    return f"<div class='schedule-result-stack'>{cards}{confirm_html}</div>{optimize_html}{toast_html}"


def render_schedule_page() -> None:
    schedule_find_query = schedule_resume_query(extra={"action": "schedule_find"})
    schedule_hidden_inputs = "".join(
        f'<input type="hidden" name="{esc(key)}" value="{esc(value)}" />'
        for key, value in schedule_find_query.items()
    )
    day_values = ["화·목 중심", "월·수 중심", "주말 가능"]
    time_values = ["오전 10시 전후", "오후 2시 전후", "오후 4시 전후"]
    current_day = st.session_state.get("schedule_day_label", "화·목 중심")
    current_time = st.session_state.get("schedule_time_label", "오전 10시 전후")
    day_options = "".join(
        f'<option value="{esc(value)}"{" selected" if value == current_day else ""}>{esc(value)}</option>'
        for value in day_values
    )
    time_options = "".join(
        f'<option value="{esc(value)}"{" selected" if value == current_time else ""}>{esc(value)}</option>'
        for value in time_values
    )
    sliders_icon = """
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M4 7h4M14 7h6M4 12h10M18 12h2M4 17h2M12 17h8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>
            <circle cx="11" cy="7" r="2.25" fill="currentColor"/>
            <circle cx="16" cy="12" r="2.25" fill="currentColor"/>
            <circle cx="9" cy="17" r="2.25" fill="currentColor"/>
        </svg>
    """
    calendar_check_icon = """
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M7 2.75a1.25 1.25 0 0 1 1.25 1.25v1h7.5V4a1.25 1.25 0 1 1 2.5 0v1H19a3 3 0 0 1 3 3v10.5a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3h.75V4A1.25 1.25 0 0 1 7 2.75Z" fill="currentColor"/>
            <path d="M2 9.5h20" stroke="#fff" stroke-width="2.2"/>
            <path d="M8.4 15.4 11 18l5-5.3" stroke="#fff" stroke-width="2.45" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    """
    info_icon = """
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="10" fill="currentColor"/>
            <path d="M12 10.5v6M12 7.4h.01" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
        </svg>
    """
    generated = bool(st.session_state.get("schedule_generated") and st.session_state.get("schedule_recommendations"))
    status_label = "추천 3건" if generated else "분석 대기"
    status_class = "schedule-status-chip ready" if generated else "schedule-status-chip"
    panel_class = "schedule-result-panel has-results" if generated else "schedule-result-panel"
    result_html = build_schedule_results_html()

    st.markdown(
        html_block(f"""
        <section class="st-key-schedule_shell">
            <div class="schedule-native-head">
                <div>
                    <p class="schedule-kicker">Personal Schedule AI</p>
                    <h2 class="schedule-title">내 운동 일정 추천</h2>
                    <p class="schedule-sub">강습 가능 시간, 이동지원 연계 가능성, 버디 후보 여부를 함께 계산해 실제로 참여하기 쉬운 시간대를 추천합니다.</p>
                </div>
                <form id="schedule-preference-form" class="schedule-find-form" method="get">
                    {schedule_hidden_inputs}
                    <button class="schedule-find-link" type="submit">
                    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M10.9 3.6a7.25 7.25 0 0 0-2.7 13.98c.42.16.87-.06 1.02-.49.15-.42-.06-.88-.48-1.04A5.63 5.63 0 1 1 16.05 8.8c.16.42.62.64 1.04.49.43-.15.65-.61.5-1.04A7.25 7.25 0 0 0 10.9 3.6Z" fill="currentColor"/>
                        <path d="M10.9 7.2c-1.65 0-3 1.34-3 3 0 2.25 3 5.65 3 5.65s3-3.4 3-5.65c0-1.66-1.35-3-3-3Zm0 4.05a1.05 1.05 0 1 1 0-2.1 1.05 1.05 0 0 1 0 2.1ZM15.4 15.4l4.95 4.95" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                    가능한 시간 찾기
                    </button>
                </form>
            </div>
            <div class="schedule-native-grid">
                <div class="schedule-left-stack">
                    <div class="schedule-soft">
                        <h3 class="schedule-soft-title">{sliders_icon}선호 조건</h3>
                        <label class="schedule-field-label">선호 요일</label>
                        <select class="schedule-control" aria-label="선호 요일" name="schedule_day_label" form="schedule-preference-form">
                            {day_options}
                        </select>
                        <label class="schedule-field-label">선호 시간대</label>
                        <select class="schedule-control" aria-label="선호 시간대" name="schedule_time_label" form="schedule-preference-form">
                            {time_options}
                        </select>
                        <div class="schedule-check-grid">
                            <div class="schedule-check"><span>✓</span>이동지원 우선</div>
                            <div class="schedule-check"><span>✓</span>버디 후보 우선</div>
                        </div>
                    </div>
                    <div class="schedule-soft">
                        <h3 class="schedule-soft-title">{info_icon}추천 기준</h3>
                        <p class="schedule-rule-list">
                            <b>1</b>지도자 가능 시간과 프로그램 정원<br>
                            <b>2</b>이동지원 연계 가능성과 시간대 혼잡도<br>
                            <b>3</b>같은 센터·시간대 버디 후보 여부
                        </p>
                    </div>
                </div>
                <div>
                    <div class="schedule-result-top">
                        <h3 class="schedule-soft-title" style="margin:0">{calendar_check_icon}참여 가능 시간 후보</h3>
                        <span class="{status_class}">{esc(status_label)}</span>
                    </div>
                    <div class="{panel_class}">{result_html}</div>
                </div>
            </div>
        </section>
        """),
        unsafe_allow_html=True,
    )


ACCESS_FACILITY_TYPES = [
    "출입구",
    "경사로",
    "접근 가능한 화장실",
    "승강기",
    "점자블록",
    "락커룸",
    "샤워실",
    "접근성 주차구역",
    "이동 동선",
]

ACCESS_ISSUE_OPTIONS = [
    "미끄럼·기울기 우려",
    "단차·문턱",
    "회전 공간 부족",
    "점자블록 단절·장애물",
    "안내 표지 복잡",
    "소음·청각 안내 부족",
    "혼잡·대기 공간 부족",
    "주차·진입 동선 혼란",
]

ACCESS_DISABILITY_FOCUS = [
    "휠체어 이용 또는 보행 보조 필요",
    "시각 정보 접근 지원 필요",
    "청각 안내 지원 필요",
    "천천히 단계별 안내 필요",
    "고령자·보행 속도 배려 필요",
]

ACCESS_GRADE_CLASSES = {
    "양호": "access-grade-good",
    "주의": "access-grade-caution",
    "점검 필요": "access-grade-check",
    "관리자 확인 필요": "access-grade-admin",
}


def access_braille_preview_svg() -> str:
    return """
    <svg viewBox="0 0 500 250" class="w-full h-auto" aria-hidden="true">
        <rect width="500" height="250" fill="#0f172a"/>
        <rect x="55" y="110" width="58" height="58" rx="5" fill="#eab308"/>
        <rect x="130" y="110" width="58" height="58" rx="5" fill="#eab308"/>
        <rect x="205" y="110" width="58" height="58" rx="5" fill="none" stroke="#ef4444" stroke-width="4" stroke-dasharray="8 6"/>
        <rect x="330" y="110" width="58" height="58" rx="5" fill="#eab308"/>
        <rect x="405" y="110" width="58" height="58" rx="5" fill="#eab308"/>
        <text x="250" y="205" text-anchor="middle" fill="#94a3b8" font-size="15">김포 반다비 1층 로비 점자블록</text>
    </svg>
    """


def access_preview_caption(facility_type: str) -> str:
    location_map = {
        "점자블록": "김포 반다비 1층 로비 점자블록",
        "경사로": "김포 반다비체육센터 북측 경사로",
        "접근 가능한 화장실": "김포 반다비체육센터 2층 접근 가능한 화장실",
    }
    return location_map.get(facility_type, f"{DEFAULT_DESTINATION} {facility_type}")


def access_grade_from_score(score: int) -> str:
    if score >= 82:
        return "관리자 확인 필요"
    if score >= 64:
        return "점검 필요"
    if score >= 42:
        return "주의"
    return "양호"


def access_disability_impacts(facility_type: str, issues: list[str]) -> dict[str, str]:
    issue_text = " · ".join(issues[:2]) if issues else "선택된 불편 요소"
    return {
        "휠체어 이용 또는 보행 보조 필요": (
            f"{facility_type} 구간에서 회전 공간, 단차, 출입문 폭, 경사로 기울기 확인이 필요할 수 있습니다. "
            f"({issue_text})"
        ),
        "시각 정보 접근 지원 필요": (
            f"{facility_type} 구간에서 점자블록 연속성, 음성 안내, 유도 표지 확인이 필요할 수 있습니다. "
            f"({issue_text})"
        ),
        "청각 안내 지원 필요": (
            f"{facility_type} 구간에서 시각 안내, 진동/문자 알림, 소음 환경 확인이 필요할 수 있습니다. "
            f"({issue_text})"
        ),
        "천천히 단계별 안내 필요": (
            f"{facility_type} 구간에서 안내 표지의 명확성, 혼잡도, 안정적 대기 공간 확인이 필요할 수 있습니다. "
            f"({issue_text})"
        ),
        "고령자·보행 속도 배려 필요": (
            f"{facility_type} 구간에서 미끄럼, 난간, 휴식 공간, 동선 길이 확인이 필요할 수 있습니다. "
            f"({issue_text})"
        ),
    }


def access_action_plan(facility_type: str, grade: str) -> dict[str, list[str]]:
    short = [
        "임시 안내문 게시 및 직원 안내 강화",
        "혼잡 시간대 동선 분리 안내",
        "위험 구간 임시 표식·스티커 부착",
    ]
    medium = [
        "미끄럼 방지 패드·손잡이 보완 검토",
        "유도선·점자블록 연속성 보완",
        "안내 표지 단순화 및 위치 재배치",
    ]
    long = [
        "출입문 폭·회전 공간 구조 개선 검토",
        "경사로 재시공·경사각 조정 검토",
        "화장실·샤워실 구조 개선 검토",
    ]
    if facility_type in {"점자블록", "이동 동선"}:
        medium.insert(0, "점자블록 단절 구간 연결·정비 검토")
    if facility_type in {"경사로", "출입구"}:
        short.insert(0, "경사로·문턱 현장 확인 및 임시 안전 조치")
    if grade in {"관리자 확인 필요", "점검 필요"}:
        short.insert(0, "관리자 현장 확인 일정 등록")
    return {"short": short[:3], "medium": medium[:3], "long": long[:3]}


def analyze_accessibility_demo(
    facility_type: str,
    disability_focus: str,
    issues: list[str],
    has_photo: bool,
) -> dict[str, Any]:
    score_parts = {
        "이용자 안전 영향도": 28,
        "이동 동선 영향도": 24,
        "반복 제보 가능성": 18,
        "지원 필요 유형 관련성": 22,
        "즉시 개선 필요도": 20,
    }
    facility_weights = {
        "경사로": 18,
        "출입구": 14,
        "접근 가능한 화장실": 16,
        "승강기": 12,
        "점자블록": 15,
        "락커룸": 10,
        "샤워실": 11,
        "접근성 주차구역": 13,
        "이동 동선": 14,
    }
    issue_weights = {
        "미끄럼·기울기 우려": 12,
        "단차·문턱": 11,
        "회전 공간 부족": 13,
        "점자블록 단절·장애물": 14,
        "안내 표지 복잡": 8,
        "소음·청각 안내 부족": 9,
        "혼잡·대기 공간 부족": 8,
        "주차·진입 동선 혼란": 10,
    }
    disability_weights = {
        "휠체어 이용 또는 보행 보조 필요": 10,
        "시각 정보 접근 지원 필요": 9,
        "청각 안내 지원 필요": 7,
        "천천히 단계별 안내 필요": 8,
        "고령자·보행 속도 배려 필요": 6,
    }

    total = sum(score_parts.values())
    total += facility_weights.get(facility_type, 10)
    total += disability_weights.get(disability_focus, 6)
    total += sum(issue_weights.get(issue, 6) for issue in issues)
    if not has_photo:
        total = int(total * 0.88)

    priority_score = max(18, min(96, total // 2))
    grade = access_grade_from_score(priority_score)
    admin_review = grade in {"점검 필요", "관리자 확인 필요"}

    expected_issue_map = {
        "출입구": "출입문 폭과 문턱 높이가 휠체어 이용·보행 보조 동선에 영향을 줄 수 있습니다.",
        "경사로": "경사로 기울기와 미끄럼 방지 상태에 대한 현장 점검이 권장됩니다.",
        "접근 가능한 화장실": "회전 공간, 손잡이 위치, 출입문 개폐 동선 확인이 필요할 수 있습니다.",
        "승강기": "버튼 높이, 음성 안내, 혼잡 시간대 대기 동선 확인이 필요할 수 있습니다.",
        "점자블록": "점자블록 단절 가능성이 있어 시각 정보 접근 지원 보완이 필요할 수 있습니다.",
        "락커룸": "좁은 통로와 회전 공간 부족으로 이용자 불편 가능성이 있습니다.",
        "샤워실": "미끄럼과 온도 조절 안내, 좌석·손잡이 위치 확인이 필요할 수 있습니다.",
        "접근성 주차구역": "주차구역과 출입 동선 연결, 표지 가독성 확인이 필요할 수 있습니다.",
        "이동 동선": "주요 이동 동선에서 장애물·단차·혼잡 구간 확인이 필요할 수 있습니다.",
    }
    expected_issues = [expected_issue_map.get(facility_type, "선택 구간의 접근성 보완 여부 확인이 필요할 수 있습니다.")]
    if issues:
        expected_issues.append(f"제보 항목: {', '.join(issues[:3])}")

    user_impact = (
        f"{disability_focus} 관점에서 {facility_type} 이용 시 이동·안내·대기 과정에서 "
        "불편 가능성이 있어 현장 확인이 권장됩니다."
    )
    improvement_need = (
        "높음 · 관리자 확인 권장"
        if admin_review
        else "보통 · 참고용 점검"
        if grade == "주의"
        else "낮음 · 참고용 모니터링"
    )

    summary_parts = [
        expected_issues[0],
        "AI 보조 분석 결과이며, 공식 인증·법적 적합 판정·행정 확정을 대체하지 않습니다.",
    ]
    if not has_photo:
        summary_parts.insert(0, "사진이 없어 분석 신뢰도는 낮게 표시됩니다. 현장 확인을 권장합니다.")

    return {
        "source": "rule_engine_demo",
        "facility_type": facility_type,
        "disability_focus": disability_focus,
        "issues": issues,
        "has_photo": has_photo,
        "grade": grade,
        "priority_score": priority_score,
        "confidence": "보통" if has_photo else "낮음",
        "score_parts": score_parts,
        "expected_issues": expected_issues,
        "user_impact": user_impact,
        "improvement_need": improvement_need,
        "admin_review_recommended": admin_review,
        "disability_impacts": access_disability_impacts(facility_type, issues),
        "actions": access_action_plan(facility_type, grade),
        "summary": " ".join(summary_parts),
        "notices": [
            "AI가 점검을 보조합니다. AI 판정 완료·법적 위반·불합격 표현을 사용하지 않습니다.",
            "제출 전 얼굴, 전화번호, 차량번호 등 개인정보는 마스킹해 주세요.",
        ],
        "report_type": facility_type,
        "risk": grade,
        "status": "검토 필요" if admin_review else "참고 모니터링",
    }


def mock_accessibility_result(report_type: str) -> dict[str, Any]:
    mapped = report_type if report_type in ACCESS_FACILITY_TYPES else "점자블록"
    issues = ["점자블록 단절·장애물"] if "점자" in report_type else []
    focus = "시각 정보 접근 지원 필요" if "점자" in report_type else "휠체어 이용 또는 보행 보조 필요"
    return analyze_accessibility_demo(mapped, focus, issues, has_photo=False)


def build_official_draft(report: dict[str, Any]) -> tuple[str, str]:
    prepared = engine_bridge.prepare_access_email_draft(report, default_destination=DEFAULT_DESTINATION)
    return prepared["subject"], prepared["body"]


def access_map_item_html(item: dict[str, Any], *, tone: str) -> str:
    if tone == "warn":
        icon = """
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 4.5 3 20h18L12 4.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M12 10v4M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """
    else:
        icon = """
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
            <path d="M8 12.5 10.8 15.2 16 9.8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """
    return f"""
    <div class="access-map-item {tone}">
        <div class="access-map-icon">{icon}</div>
        <div>
            <p class="access-map-title">{esc(item.get('title', item.get('facility', '접근성 제보')))}</p>
            <p class="access-map-meta">{esc(item.get('meta', item.get('location', '')))}</p>
        </div>
    </div>
    """


def access_vision_result_html(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return (
            "스캔 실행 전입니다. AI 분석 결과는 접근성 점검 보조자료이며, "
            "법적 인증·행정처분·시설 적합 판정을 대체하지 않습니다."
        )
    facility = analysis.get("facility_type", "접근성 점검")
    score = int(analysis.get("priority_score", 0))
    if "점자" in facility or analysis.get("grade") in {"점검 필요", "관리자 확인 필요"}:
        detect_score = min(99, max(score, 78))
        return f"""
        <div class="access-vision-alert">
            <div class="access-vision-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M12 4.5 3 20h18L12 4.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                    <path d="M12 10v4M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <div>
                <p class="access-vision-alert-title">개선 필요 · AI 탐지 참고값 {detect_score:.1f}%</p>
                <p class="access-vision-alert-copy">
                    {esc(facility)} 관련 접근성 확인이 필요할 수 있습니다. 기관 확인 후 공문 초안 생성이 가능합니다.
                </p>
            </div>
        </div>
        """
    grade = analysis.get("grade", "점검 필요")
    return (
        f"<strong>{esc(grade)} · AI 보조 참고 점수 {score}점</strong><br>"
        f"{esc(analysis.get('summary', ''))}"
    )


def access_run_scan(
    facility_type: str,
    disability_focus: str,
    issue_choices: list[str],
    has_photo: bool,
) -> dict[str, Any]:
    uploaded = st.session_state.get("access_photo_upload")
    photo_bytes = uploaded.getvalue() if uploaded is not None else None
    vision_raw = None
    if has_photo and photo_bytes:
        vision_raw = engine_bridge.run_vision_analysis(
            facility_type, disability_focus, issue_choices, photo_bytes
        )
    analysis = analyze_accessibility_demo(
        facility_type,
        disability_focus,
        issue_choices,
        has_photo,
    )
    analysis = engine_bridge.merge_vision_into_analysis(
        analysis, vision_raw, has_photo=has_photo
    )
    st.session_state.access_analysis = analysis
    st.session_state.accessibility_report = analysis
    st.session_state.vision_result = analysis
    st.session_state.vision_last_report_type = facility_type
    return analysis


def register_accessibility_submission(analysis: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "id": f"RPT-{datetime.now().strftime('%m%d%H%M')}",
        "facility": analysis.get("facility_type", "접근성 점검"),
        "location": access_preview_caption(analysis.get("facility_type", "이동 동선")),
        "grade": analysis.get("grade", "점검 필요"),
        "score": analysis.get("priority_score", 0),
        "status": "접수 대기 · 검토 필요" if analysis.get("admin_review_recommended") else "참고 등록 · 모니터링",
        "title": analysis.get("facility_type", "접근성 제보"),
        "meta": access_preview_caption(analysis.get("facility_type", "이동 동선")),
    }
    recent = list(st.session_state.get("access_recent_reports") or [])
    recent.insert(0, entry)
    st.session_state.access_recent_reports = recent[:5]
    st.session_state.access_last_submission = entry
    return entry


def render_accessibility_page() -> None:
    facility_type = st.session_state.get("access_facility_type", "점자블록")
    disability_focus = st.session_state.get("access_disability_focus", "시각 정보 접근 지원 필요")
    issue_choices = st.session_state.get("access_issue_choices") or []
    analysis = st.session_state.get("access_analysis")

    def access_href(action: str) -> str:
        return "?" + urlencode(
            {
                "resume": "1",
                "page": "accessibility",
                "step": st.session_state.get("main_step", "start"),
                "role": st.session_state.get("role", USER_ROLE),
                "user": st.session_state.get("user_name", ""),
                "email": st.session_state.get("user_email", ""),
                "action": action,
            }
        )

    access_form_query = {
        "resume": "1",
        "page": "accessibility",
        "step": st.session_state.get("main_step", "start"),
        "role": st.session_state.get("role", USER_ROLE),
        "user": st.session_state.get("user_name", ""),
        "email": st.session_state.get("user_email", ""),
    }
    access_hidden_inputs = "".join(
        f'<input type="hidden" name="{esc(key)}" value="{esc(value)}" />'
        for key, value in access_form_query.items()
        if value != ""
    )
    facility_options = "".join(
        f'<option value="{esc(value)}"{" selected" if value == facility_type else ""}>{esc(value)}</option>'
        for value in ACCESS_FACILITY_TYPES
    )
    focus_options = "".join(
        f'<option value="{esc(value)}"{" selected" if value == disability_focus else ""}>{esc(value)}</option>'
        for value in ACCESS_DISABILITY_FOCUS
    )
    issue_selected = issue_choices[0] if issue_choices else ""
    issue_options = "<option value=''>선택 안 함</option>" + "".join(
        f'<option value="{esc(value)}"{" selected" if value == issue_selected else ""}>{esc(value)}</option>'
        for value in ACCESS_ISSUE_OPTIONS
    )

    st.markdown('<div class="access-native-shell">', unsafe_allow_html=True)
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        with st.container(key="access_left_native"):
            st.markdown(
                html_block(f"""
                <div class="access-native-head">
                    <div>
                        <p class="access-kicker">AI Vision</p>
                        <h2 class="access-native-heading">접근성 점검 보조</h2>
                        <p class="access-sub">사진 제보를 위험도 카드로 바꿔 보여줍니다.</p>
                    </div>
                    <a class="access-scan-link" href="{esc(access_href('access_scan'))}" target="_self">
                        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M5 8.5h3l1.5-2h5L16 8.5h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z" fill="currentColor"/>
                            <circle cx="12" cy="14" r="3.2" fill="#fff"/>
                        </svg>
                        스캔
                    </a>
                </div>
                <div class="access-upload-native">
                    <p class="access-upload-title">시설 사진 업로드</p>
                    <p class="access-upload-copy">
                        경사로, 점자블록, 출입문, 화장실, 승강기 등 접근성 확인이 필요한 사진을 올려주세요.<br>
                        JPG, PNG 파일을 지원합니다. 실제 제출 전 개인정보가 포함되지 않았는지 확인해 주세요.
                    </p>
                </div>
                """),
                unsafe_allow_html=True,
            )
            upload_btn_col, upload_name_col = st.columns([1.05, 1.6], gap="small")
            with upload_btn_col:
                st.file_uploader(
                    "시설 사진",
                    type=["jpg", "jpeg", "png", "webp"],
                    key="access_photo_upload",
                    label_visibility="collapsed",
                )
            uploaded = st.session_state.get("access_photo_upload")
            has_photo = uploaded is not None
            upload_file_label = uploaded.name if has_photo and getattr(uploaded, "name", None) else "선택된 파일 없음"
            with upload_name_col:
                st.markdown(
                    html_block(f'<p class="access-upload-file-name">{esc(upload_file_label)}</p>'),
                    unsafe_allow_html=True,
                )

            if has_photo:
                photo_bytes = uploaded.getvalue()
                mime = uploaded.type or "image/jpeg"
                preview_markup = (
                    f'<img src="data:{mime};base64,{base64.b64encode(photo_bytes).decode("ascii")}" '
                    'alt="업로드한 시설 사진" style="width:100%;border-radius:18px;display:block;" />'
                )
            else:
                preview_markup = access_braille_preview_svg()

            if analysis:
                detect_score = float(analysis.get("detection_score", 96.8))
                result_note = (
                    f"<b>개선 필요 · AI 탐지 참고값 {detect_score:.1f}%</b><br>"
                    f"{esc(analysis.get('facility_type', facility_type))} 관련 접근성 확인이 필요할 수 있습니다. "
                    "기관 확인 후 공문 초안 생성이 가능합니다."
                )
            else:
                result_note = (
                    "스캔 실행 전입니다. AI 분석 결과는 접근성 점검 보조자료이며, "
                    "법적 인증·행정처분·시설 적합 판정을 대체하지 않습니다."
                )

            st.markdown(
                html_block(f"""
                <div class="access-detail-native">
                    <form class="access-detail-form" method="get">
                        {access_hidden_inputs}
                        <div>
                            <label class="access-native-label">점검 시설 유형</label>
                            <select class="access-native-select" name="access_facility_type" aria-label="점검 시설 유형">
                                {facility_options}
                            </select>
                        </div>
                        <div>
                            <label class="access-native-label">중점 확인 관점</label>
                            <select class="access-native-select" name="access_focus" aria-label="중점 확인 관점">
                                {focus_options}
                            </select>
                        </div>
                        <div>
                            <label class="access-native-label">불편 요소 선택</label>
                            <select class="access-native-select" name="access_issue" aria-label="불편 요소 선택">
                                {issue_options}
                            </select>
                        </div>
                        <div class="access-detail-actions">
                            <button class="access-detail-button primary" type="submit" name="action" value="access_scan">
                                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M5 8.5h3l1.5-2h5L16 8.5h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z" fill="currentColor"/>
                                    <circle cx="12" cy="14" r="3.2" fill="#fff"/>
                                </svg>
                                선택값으로 AI 보조 점검 실행
                            </button>
                            <button class="access-detail-button secondary" type="submit" name="action" value="access_submit">
                                점검 리포트 생성 · 제보 등록
                            </button>
                        </div>
                    </form>
                </div>
                <div class="access-preview-native">
                    {preview_markup}
                    <p class="access-preview-caption">{esc(access_preview_caption(facility_type))}</p>
                </div>
                <div class="access-note-native">{result_note}</div>
                <div class="access-action-native-grid">
                    <a class="access-action-link reward" href="{esc(access_href('access_reward'))}" target="_self">
                        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <ellipse cx="12" cy="6.5" rx="7" ry="2.8" fill="currentColor"/>
                            <path d="M5 7v8c0 1.7 3.1 3 7 3s7-1.3 7-3V7" stroke="#fff" stroke-width="2"/>
                            <path d="M5 11c0 1.7 3.1 3 7 3s7-1.3 7-3" stroke="#fff" stroke-width="1.7"/>
                        </svg>
                        제보 참여 인센티브
                    </a>
                    <a class="access-action-link draft" href="{esc(access_href('access_draft'))}" target="_self">
                        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M6 3.5h8.2L19 8.3V20.5H6V3.5Z" fill="currentColor"/>
                            <path d="M14 3.5V8.5H19" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>
                            <path d="M9.2 16.7 10 14.2 15.2 9 17 10.8 11.8 16l-2.6.7Z" fill="#fff"/>
                        </svg>
                        공문 초안 생성
                    </a>
                </div>
                """),
                unsafe_allow_html=True,
            )

    recent = list(st.session_state.get("access_recent_reports") or [])
    first_meta = "1층 로비 · 개선 필요 가능성 높음 · 검토 요청 대기"
    if recent:
        first = recent[0]
        if first.get("grade") != "양호":
            first_meta = (
                f"{first.get('location', '1층 로비')} · "
                f"개선 필요 가능성 높음 · {first.get('status', '검토 요청 대기')}"
            )

    with right_col:
        with st.container(key="access_right_native"):
            st.markdown(
                html_block(f"""
                <p class="access-kicker">Accessibility Map</p>
                <h2 class="access-native-heading">접근성 제보 지도</h2>
                <div class="access-map-native-list">
                    <div class="access-map-native-item">
                        <div class="access-map-native-icon warn">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 3 22 20H2L12 3Z" fill="currentColor"/>
                                <path d="M12 9v5M12 17h.01" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <div>
                            <p class="access-map-native-title">점자블록 단절</p>
                            <p class="access-map-native-meta">{esc(first_meta)}</p>
                        </div>
                    </div>
                    <div class="access-map-native-item">
                        <div class="access-map-native-icon done">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <circle cx="12" cy="12" r="10" fill="currentColor"/>
                                <path d="m8 12 2.5 2.5L16.5 9" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <div>
                            <p class="access-map-native-title">접근 가능한 화장실 개선 완료</p>
                            <p class="access-map-native-meta">2층 · 조치 완료 · 운영기관 확인 완료</p>
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    if analysis:
        grade = analysis.get("grade", "점검 필요")
        grade_class = ACCESS_GRADE_CLASSES.get(grade, "access-grade-check")
        impacts = analysis.get("disability_impacts") or {}
        actions = analysis.get("actions") or {}
        impact_html = "".join(
            f"<li><b>{esc(name)}</b>: {esc(text)}</li>" for name, text in impacts.items()
        )
        short_actions = "".join(f"<li>{esc(x)}</li>" for x in actions.get("short", []))
        medium_actions = "".join(f"<li>{esc(x)}</li>" for x in actions.get("medium", []))
        long_actions = "".join(f"<li>{esc(x)}</li>" for x in actions.get("long", []))
        last_submission = st.session_state.get("access_last_submission")
        completion_html = ""
        if last_submission:
            completion_html = f"""
            <div class="access-complete-card">
                <p class="access-complete-title">점검 리포트가 생성되었습니다</p>
                <p class="access-complete-meta">
                    제보 번호 {esc(last_submission.get('id', ''))} ·
                    제보 시설 {esc(last_submission.get('facility', ''))} ·
                    접근성 점검 등급 {esc(last_submission.get('grade', ''))} ·
                    개선 우선순위 참고 점수 {esc(str(last_submission.get('score', '')))}점 ·
                    관리자 확인 상태 {esc(last_submission.get('status', '접수 대기'))}
                </p>
            </div>
            """
        st.markdown(
            html_block(f"""
            <section class="access-report-native" aria-label="AI 보조 점검 상세 리포트">
                <h3>AI 보조 점검 상세 리포트</h3>
                <div class="access-result-card">
                    <div class="access-grade-row">
                        <span class="access-grade-badge {grade_class}">접근성 점검 등급 · {esc(grade)}</span>
                        <span class="access-grade-badge access-grade-caution">분석 신뢰도 · {esc(analysis.get('confidence', '보통'))}</span>
                    </div>
                    <div class="access-score-ring">
                        <span class="access-score-value">{int(analysis.get('priority_score', 0))}</span>
                        <span class="access-score-label">개선 우선순위 참고 점수 (0~100)</span>
                    </div>
                    <div class="access-metric-grid">
                        <div class="access-metric">
                            <div class="access-metric-label">예상 불편 요소</div>
                            <div class="access-metric-value">{esc(' / '.join(analysis.get('expected_issues', [])[:2]))}</div>
                        </div>
                        <div class="access-metric">
                            <div class="access-metric-label">이용자 영향</div>
                            <div class="access-metric-value">{esc(analysis.get('user_impact', ''))}</div>
                        </div>
                        <div class="access-metric">
                            <div class="access-metric-label">개선 필요도</div>
                            <div class="access-metric-value">{esc(analysis.get('improvement_need', ''))}</div>
                        </div>
                        <div class="access-metric">
                            <div class="access-metric-label">관리자 확인 권장</div>
                            <div class="access-metric-value">{'권장' if analysis.get('admin_review_recommended') else '참고 모니터링'}</div>
                        </div>
                    </div>
                </div>
                <div class="access-report-native-grid">
                    <div class="access-soft">
                        <p class="access-soft-title">지원 필요 유형별 영향 안내</p>
                        <ul class="access-impact-list">{impact_html}</ul>
                    </div>
                    <div class="access-soft">
                        <p class="access-soft-title">기관용 조치 제안</p>
                        <div class="access-action-block"><b>단기 조치</b><ul class="access-action-list">{short_actions}</ul></div>
                        <div class="access-action-block"><b>중기 조치</b><ul class="access-action-list">{medium_actions}</ul></div>
                        <div class="access-action-block"><b>장기 조치</b><ul class="access-action-list">{long_actions}</ul></div>
                    </div>
                </div>
                {completion_html}
            </section>
            """),
            unsafe_allow_html=True,
        )

    if st.session_state.get("access_show_draft"):
        report = st.session_state.get("access_analysis") or mock_accessibility_result(
            st.session_state.get("access_facility_type", "점자블록")
        )
        facility = report.get("facility_type") or report.get("report_type", "점자블록")
        prepared = engine_bridge.prepare_access_email_draft(report, default_destination=DEFAULT_DESTINATION)
        subject = prepared["subject"]
        body = prepared["body"]
        to_email = prepared["to_email"]
        from_name = prepared["from_name"]
        from_email = prepared["from_email"]
        payload = prepared["payload"]
        payload_text = json.dumps(payload, ensure_ascii=False, indent=2)
        body_textarea = esc(body).replace("\n", "&#10;")
        st.markdown(
            html_block(f"""
            <div class="access-draft-overlay" role="dialog" aria-modal="true" aria-label="접근성 개선 검토용 공문 이메일 초안">
                <section class="access-draft-modal">
                    <div class="access-draft-head">
                        <div>
                            <p class="access-kicker">Official Notice Draft</p>
                            <h2 class="access-draft-title">접근성 개선 검토용 공문·이메일 초안</h2>
                            <p class="access-draft-copy">미리보기 내용을 수정한 뒤, 추후 SendGrid API와 연결할 수 있는 형태로 저장합니다.</p>
                        </div>
                        <a class="access-draft-close" href="{esc(access_href('access_close_draft'))}" target="_self" aria-label="공문 초안 닫기">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/>
                            </svg>
                        </a>
                    </div>
                    <div class="access-draft-form-grid">
                        <label>
                            <span class="access-draft-label">받는 이메일 주소</span>
                            <input class="access-draft-input" type="email" value="{esc(to_email)}" />
                        </label>
                        <label>
                            <span class="access-draft-label">보내는 이 이름</span>
                            <input class="access-draft-input" value="{esc(from_name)}" />
                        </label>
                        <label>
                            <span class="access-draft-label">보내는 이메일 주소</span>
                            <input class="access-draft-input" type="email" value="{esc(from_email)}" />
                        </label>
                        <label>
                            <span class="access-draft-label">메일 제목</span>
                            <input class="access-draft-input" value="{esc(subject)}" />
                        </label>
                    </div>
                    <div class="access-draft-section">
                        <div class="access-draft-section-head">
                            <p class="access-draft-section-title">
                                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>
                                    <path d="m14 8 2 2" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>
                                </svg>
                                공문/이메일 본문 미리보기
                            </p>
                            <a class="access-draft-mini-link" href="{esc(access_href('access_prepare_draft'))}" target="_self">Payload 갱신</a>
                        </div>
                        <textarea class="access-draft-textarea" spellcheck="false">{body_textarea}</textarea>
                    </div>
                    <div class="access-draft-section">
                        <p class="access-draft-section-title">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 4l-4 16" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            SendGrid 연동용 payload 미리보기
                        </p>
                        <pre class="access-draft-pre">{esc(payload_text)}</pre>
                    </div>
                    <p class="access-draft-warning">※ 관리자 검토용 초안입니다. ENABLE_SENDGRID_SEND=true 이고 Secrets가 설정되면 발송 준비 버튼으로 SendGrid 전송을 시도합니다. API Key는 표시하지 않습니다.</p>
                    <div class="access-draft-actions">
                        <a class="access-draft-action neutral" href="{esc(access_href('access_prepare_draft'))}" target="_self">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" stroke="currentColor" stroke-width="2.2"/>
                                <circle cx="12" cy="12" r="3" fill="currentColor"/>
                            </svg>
                            미리보기 갱신
                        </a>
                        <a class="access-draft-action ready" href="{esc(access_href('access_send_draft'))}" target="_self">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M4 6h16v12H4V6Z" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/>
                                <path d="m4 7 8 6 8-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="m16.5 15.5 1.5 1.5 3-3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            발송 준비
                        </a>
                        <a class="access-draft-action submit" href="{esc(access_href('access_submit_draft'))}" target="_self">
                            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M21 3 10 14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>
                                <path d="m21 3-7 18-4-7-7-4 18-7Z" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>
                            </svg>
                            검토 요청 등록
                        </a>
                    </div>
                </section>
            </div>
            """),
            unsafe_allow_html=True,
        )

def render_dashboard_page() -> None:
    if st.session_state.get("role") != ADMIN_ROLE:
        st.session_state.current_page = "main"
        st.warning("기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다.")
        render_main_page()
        return

    font_data_uri = pretendard_font_data_uri()
    dashboard_font_face = (
        f"""
        @font-face {{
            font-family: "Pretendard Local";
            src: url("{font_data_uri}") format("truetype");
            font-weight: 45 920;
            font-style: normal;
            font-display: swap;
        }}
        """
        if font_data_uri
        else ""
    )

    st.markdown(
        f"""
        <style>
        {dashboard_font_face}
        [data-testid="stMarkdownContainer"] .dashboard-board-shell,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell .dashboard-board-title,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell .dashboard-board-kicker,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell p,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell th,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell td,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell a,
        [data-testid="stMarkdownContainer"] .dashboard-board-shell b {{
            font-family: {PRETENDARD_STACK} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    dispatch_href = "?" + urlencode(
        {
            "resume": "1",
            "page": "dashboard",
            "role": ADMIN_ROLE,
            "user": st.session_state.get("user_name", ""),
            "email": st.session_state.get("user_email", ""),
            "action": "dashboard_dispatch",
        }
    )
    log_lines = list(st.session_state.get("dashboard_log_lines") or [])
    log_html = "".join(f"<p>{esc(line)}</p>" for line in log_lines)
    api_items = engine_bridge.dashboard_api_status_items(
        cache=st.session_state.get("dashboard_api_cache")
    )
    st.session_state.dashboard_api_cache = api_items
    api_html = "".join(
        f'<div class="dashboard-api-item{" wide" if label == "SendGrid" else ""}"><b>{esc(label)}</b><br>{esc(status)}</div>'
        for label, status in api_items
    )
    chart_font_face = (
        f"""
          @font-face {{
            font-family: "Pretendard Local";
            src: url("{font_data_uri}") format("truetype");
            font-weight: 45 920;
            font-style: normal;
            font-display: swap;
          }}
        """
        if font_data_uri
        else ""
    )

    st.markdown(
        html_block(f"""
        <section class="dashboard-native-shell dashboard-kpi-shell">
            <div class="dashboard-kpi-grid">
                <div class="dashboard-kpi-card">
                    <svg class="dashboard-kpi-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M9 12.5 11 14.5 15.5 10" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2.2"/>
                        <path d="M6 20c.8-3.2 3.2-5 6-5s5.2 1.8 6 5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                    <p class="dashboard-kpi-label">예약 대비 출석률</p>
                    <p class="dashboard-kpi-value">94.2%</p>
                </div>
                <div class="dashboard-kpi-card">
                    <svg class="dashboard-kpi-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <rect x="3" y="8" width="12" height="8" rx="2" stroke="currentColor" stroke-width="2"/>
                        <path d="M15 11h3l2 2v3h-5v-5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                        <circle cx="7" cy="18" r="1.6" fill="currentColor"/>
                        <circle cx="17" cy="18" r="1.6" fill="currentColor"/>
                    </svg>
                    <p class="dashboard-kpi-label">이동지원 연계 성공</p>
                    <p class="dashboard-kpi-value purple">88.7%</p>
                </div>
                <div class="dashboard-kpi-card">
                    <svg class="dashboard-kpi-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M7 12h4l2-2 4 4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M4 18c2-2 4-3 8-3s6 1 8 3" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                    <p class="dashboard-kpi-label">피어 매칭 성공</p>
                    <p class="dashboard-kpi-value amber">76.4%</p>
                </div>
                <div class="dashboard-kpi-card">
                    <svg class="dashboard-kpi-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M8 6h8M8 10h8M8 14h5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                        <rect x="5" y="4" width="14" height="16" rx="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <p class="dashboard-kpi-label">지도자 부족률</p>
                    <p class="dashboard-kpi-value blue">24%</p>
                </div>
            </div>
        </section>
        """),
        unsafe_allow_html=True,
    )

    st.components.v1.html(
        f"""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
        <style>
          {chart_font_face}
          body {{
            margin: 0;
            padding: 0;
            font-family: "Pretendard Local", "Pretendard Variable", Pretendard, sans-serif;
            background: transparent;
          }}
          .wrap {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 0;
          }}
          .panel {{
            background: #ffffff;
            border: 1px solid rgba(184,172,216,.28);
            border-radius: 32px;
            padding: 20px 20px 16px;
            box-shadow: 0 2px 20px rgba(109,40,217,.07);
            box-sizing: border-box;
          }}
          h3 {{
            margin: 0;
            color: #2d2040;
            font-size: 18px;
            font-weight: 900;
            font-family: "Pretendard Local", "Pretendard Variable", Pretendard, sans-serif;
          }}
          .chart-box {{
            height: 288px;
            margin-top: 16px;
            position: relative;
          }}
          @media (max-width: 980px) {{
            .wrap {{ grid-template-columns: 1fr; }}
          }}
        </style>
        <div class="wrap">
          <div class="panel">
            <h3>접근성 지원 필요 유형별 이용률</h3>
            <div class="chart-box"><canvas id="bandabi-disability-chart"></canvas></div>
          </div>
          <div class="panel">
            <h3>시간대별 혼잡·이동지원 지연</h3>
            <div class="chart-box"><canvas id="bandabi-traffic-chart"></canvas></div>
          </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        const chartFont = '"Pretendard Local", "Pretendard Variable", Pretendard, sans-serif';
        Chart.defaults.font.family = chartFont;
        new Chart(document.getElementById('bandabi-disability-chart'), {{
          type: 'doughnut',
          data: {{
            labels: ['보행 보조', '음성 안내', '단계별 안내', '기타'],
            datasets: [{{ data: [48, 18, 22, 12], backgroundColor: ['#8b5cf6', '#a78bfa', '#6d28d9', '#4c1d95'], borderWidth: 0 }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#7868a0', font: {{ family: chartFont, size: 12 }} }} }} }}
          }}
        }});
        new Chart(document.getElementById('bandabi-traffic-chart'), {{
          type: 'bar',
          data: {{
            labels: ['09시', '11시', '13시', '15시', '17시', '19시'],
            datasets: [
              {{ label: '예약', data: [35, 68, 42, 95, 50, 20], backgroundColor: '#6366f1', borderRadius: 8 }},
              {{ label: '이동지원 지연', data: [5, 18, 8, 28, 12, 2], type: 'line', borderColor: '#ef4444', borderWidth: 2, fill: false, tension: 0.25 }}
            ]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
              x: {{ ticks: {{ color: '#7868a0', font: {{ family: chartFont, size: 11 }} }}, grid: {{ display: false }} }},
              y: {{ ticks: {{ color: '#7868a0', font: {{ family: chartFont, size: 11 }} }}, grid: {{ color: 'rgba(184,172,216,.24)' }} }}
            }},
            plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#7868a0', font: {{ family: chartFont, size: 12 }} }} }} }}
          }}
        }});
        </script>
        """,
        height=392,
    )

    st.markdown(
        html_block(f"""
        <section class="dashboard-native-shell dashboard-board-shell">
            <div class="dashboard-panel">
                <div class="dashboard-board-head">
                    <div>
                        <p class="dashboard-board-kicker">B2G Operating Board</p>
                        <p class="dashboard-board-title" role="heading" aria-level="2">기관 운영 액션 보드</p>
                    </div>
                    <a class="dashboard-dispatch-link" href="{esc(dispatch_href)}" target="_self">대체 매칭 알림</a>
                </div>
                <div class="dashboard-table-wrap">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>구분</th>
                                <th>내용</th>
                                <th>AI 추천</th>
                                <th style="text-align:right;">상태</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>노쇼 공백</td>
                                <td>수중 생활체육 10:00 슬롯</td>
                                <td>대기자 2명 삽입 가능</td>
                                <td class="status-warn">알림 대기</td>
                            </tr>
                            <tr>
                                <td>접근성</td>
                                <td>점자블록 단절</td>
                                <td>개선 필요 가능성 높음</td>
                                <td class="status-danger">검토 요청 필요</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="dashboard-api-section">
                    <p class="dashboard-panel-title">공공데이터 연동 상태</p>
                    <div class="dashboard-api-grid">{api_html}</div>
                </div>
                <div class="dashboard-log-feed">{log_html}</div>
            </div>
        </section>
        """),
        unsafe_allow_html=True,
    )


def render_app() -> None:
    init_state()
    inject_css()

    if not st.session_state.get("logged_in"):
        render_auth()
        return

    if st.session_state.get("role") == USER_ROLE:
        handle_user_chrome_query()
        sync_resume_query_params()
        render_user_topbar()
    else:
        handle_user_chrome_query()
        sync_resume_query_params()
        render_admin_topbar()

    render_notice()

    page = st.session_state.get("current_page", "main")
    if page == "main":
        render_main_page()
    elif page == "schedule":
        st.markdown('<div class="journey-shell">', unsafe_allow_html=True)
        render_schedule_page()
        st.markdown("</div>", unsafe_allow_html=True)
    elif page == "accessibility":
        st.markdown('<div class="journey-shell">', unsafe_allow_html=True)
        render_accessibility_page()
        st.markdown("</div>", unsafe_allow_html=True)
    elif page == "dashboard":
        render_dashboard_page()
    else:
        st.session_state.current_page = "dashboard" if st.session_state.get("role") == ADMIN_ROLE else "main"
        if st.session_state.get("role") == ADMIN_ROLE:
            render_dashboard_page()
        else:
            render_main_page()


render_app()
