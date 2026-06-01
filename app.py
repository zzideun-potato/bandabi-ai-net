"""Bandabi AI native Streamlit prototype.

This file intentionally keeps the current prototype self-contained:
Streamlit Cloud can run it with only ``python -m streamlit run app.py``.
External services and real authentication are not invoked in this UI-first build.
"""

from __future__ import annotations

import html
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any
from urllib.parse import quote

import streamlit as st

try:
    import pandas as pd
except Exception:  # pragma: no cover - Streamlit can still render without charts.
    pd = None


st.set_page_config(page_title="반다비 AI", page_icon="🐻", layout="wide", initial_sidebar_state="collapsed")


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
        "summary": "수중 생활체육 · 보행 보조 및 휠체어 이용자 지도 경험",
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
        "origin": "김포 구래역 1번 출구",
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
        "pending_confirm": None,
        "center_warning": False,
        "notice": "",
        "high_contrast": False,
        "vision_last_report_type": "점자블록 단절",
        "auth_name": "",
        "auth_email": "",
        "auth_password": "",
        "auth_password_confirm": "",
        "signup_role_choice": "이용자 (User)",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

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

    st.markdown(
        f"""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css');
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
            font-family: "Pretendard Variable", "Pretendard", "Apple SD Gothic Neo",
                "Malgun Gothic", system-ui, sans-serif;
            font-optical-sizing: auto;
            -webkit-font-smoothing: antialiased;
            text-rendering: geometricPrecision;
            overflow-x: hidden;
        }}
        .block-container {{
            max-width: 1120px;
            padding-top: .85rem;
            padding-bottom: 5rem;
        }}
        h1, h2, h3, p, label, span, div {{
            letter-spacing: 0;
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
            min-height: calc(100vh - 28px);
            display: flex;
            align-items: center;
            justify-content: center;
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
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
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
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
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
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
        }}
        .auth-form-page {{
            min-height: calc(100vh - 28px);
            display: flex;
            align-items: center;
            justify-content: center;
            transform: translateY(-14px);
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
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
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
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
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
        .auth-form-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        .auth-form-action {{
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 1 1 0;
            height: 55px;
            border-radius: 12px;
            text-decoration: none !important;
            font-family: "Pretendard Variable", "Pretendard", sans-serif;
            font-size: 16px;
            font-weight: 900;
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
        .signup-panel-stream {{
            box-sizing: border-box;
            width: 100%;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.34);
            border-radius: 16px;
            padding: 24px 20px 22px;
        }}
        .signup-panel-stream [data-testid="stTextInput"],
        .signup-panel-stream [data-testid="stRadio"] {{
            margin-bottom: 14px;
        }}
        .signup-panel-stream [data-testid="stTextInput"] label,
        .signup-panel-stream [data-testid="stRadio"] > label {{
            display: none;
        }}
        .signup-panel-stream [data-testid="stTextInput"] input {{
            min-height: 54px;
            border-radius: 12px;
            border: 0;
            background: #ffffff;
            color: #4a2d7a;
            font-size: 16px;
            font-weight: 300;
            padding: 0 20px;
            box-shadow: none;
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
            max-width: 860px;
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
        .route-line {{
            stroke-dasharray: 14 10;
            animation: routeDash 1.3s linear infinite;
        }}
        @keyframes routeDash {{
            to {{ stroke-dashoffset: -48; }}
        }}
        .confirm-action .stButton > button,
        .confirm-action .stButton > button[kind="primary"] {{
            background: #a8e6c4 !important;
            color: #1a5c38 !important;
            border: 1px solid rgba(80,180,120,.25) !important;
            box-shadow: none !important;
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
            font-weight: 700;
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
            font-weight: 700;
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
            font-weight: 700;
            line-height: 1.2;
            text-decoration: none !important;
            white-space: nowrap;
            transition: background .15s ease, color .15s ease, box-shadow .15s ease;
        }}
        .app-tab svg {{
            flex: 0 0 18px;
            width: 18px;
            height: 18px;
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
            padding: 28px 28px 24px;
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
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin: 0;
        }}
        .start-greeting {{
            color: #4a2d7a;
            font-size: clamp(28px, 3vw, 36px);
            font-weight: 900;
            line-height: 1.12;
            margin: 10px 0 0;
        }}
        .start-lead {{
            color: #7868a0;
            font-size: 18px;
            line-height: 1.45;
            font-weight: 300;
            margin: 14px 0 0;
        }}
        .start-copy {{
            color: #b8acd8;
            font-size: 12px;
            line-height: 1.65;
            font-weight: 300;
            margin: 8px 0 0;
        }}
        .start-grid-shell {{
            margin-top: 28px;
        }}
        .start-label {{
            display: block;
            color: #7868a0;
            font-size: 12px;
            font-weight: 800;
            margin: 0 0 8px;
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
            min-height: 48px;
            border-radius: 16px;
            border-color: rgba(119, 96, 160, .22);
            background: #fff;
            color: #4a2d7a;
            font-size: 14px;
            font-weight: 500;
        }}
        .start-tile-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }}
        .start-tile {{
            min-height: 58px;
            border-radius: 16px;
            background: #f0ecf8;
            border: 1px solid rgba(184,172,216,.22);
            color: #4a2d7a;
            font-size: 14px;
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
        .st-key-btn_ai_start > button {{
            min-height: 58px;
            border-radius: 24px;
            font-size: 18px;
            font-weight: 900;
            box-shadow: 0 12px 24px rgba(74,45,122,.28);
        }}
        .start-footnote {{
            color: #b8acd8;
            font-size: 11px;
            line-height: 1.65;
            font-weight: 300;
            margin: 28px 0 0;
        }}
        @media (max-width: 760px) {{
            .block-container {{ padding: 1rem 1rem 4rem; }}
            .section-card, .auth-card {{ padding: 20px; border-radius: 18px; }}
            .brand-title {{ font-size: 17px; }}
            .section-title {{ font-size: 25px; }}
            .metric-value {{ font-size: 24px; }}
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




def render_auth() -> None:
    query_auth = st.query_params.get("auth")
    if query_auth == "entry":
        st.session_state.auth_stage = "entry"
        st.session_state.auth_mode = "로그인"
        try:
            del st.query_params["auth"]
        except Exception:
            pass
    if query_auth == "signup_done":
        resolved_name = (
            (st.session_state.get("auth_name") or "").strip()
            or (st.session_state.get("login_name") or "").strip()
            or (st.session_state.get("user_name") or "").strip()
            or "안소연"
        )
        resolved_email = (
            (st.session_state.get("auth_email") or "").strip()
            or (st.session_state.get("login_email") or "").strip()
            or (st.session_state.get("user_email") or "").strip()
        )
        st.session_state.logged_in = True
        st.session_state.authenticated = True
        st.session_state.auth_mode = "회원가입"
        st.session_state.user_name = resolved_name
        st.session_state.user_email = resolved_email
        st.session_state.role = signup_role_from_choice()
        st.session_state.current_page = "dashboard" if st.session_state.role == ADMIN_ROLE else "main"
        st.session_state.main_step = "start"
        st.session_state.bt_points = int(st.session_state.get("bt_points", 3500))
        st.session_state.bt_balance = st.session_state.bt_points
        try:
            del st.query_params["auth"]
        except Exception:
            pass
        st.rerun()
    if query_auth == "login_done":
        resolved_name = (
            (st.session_state.get("auth_name") or "").strip()
            or (st.session_state.get("login_name") or "").strip()
            or (st.session_state.get("user_name") or "").strip()
            or "안소연"
        )
        resolved_email = (
            (st.session_state.get("auth_email") or "").strip()
            or (st.session_state.get("login_email") or "").strip()
            or (st.session_state.get("user_email") or "").strip()
        )
        st.session_state.logged_in = True
        st.session_state.authenticated = True
        st.session_state.auth_mode = "로그인"
        st.session_state.user_name = resolved_name
        st.session_state.user_email = resolved_email
        st.session_state.role = USER_ROLE
        st.session_state.current_page = "main"
        st.session_state.main_step = "start"
        st.session_state.bt_points = int(st.session_state.get("bt_points", 3500))
        st.session_state.bt_balance = st.session_state.bt_points
        try:
            del st.query_params["auth"]
        except Exception:
            pass
        st.rerun()
    if query_auth in {"login", "signup"}:
        st.session_state.auth_stage = "form"
        st.session_state.auth_mode = "로그인" if query_auth == "login" else "회원가입"
        if query_auth == "signup":
            role_qp = st.query_params.get("role")
            if role_qp == "admin":
                st.session_state.signup_role_choice = "기관 관리자 (Admin)"
            elif role_qp == "user":
                st.session_state.signup_role_choice = "이용자 (User)"
        try:
            del st.query_params["auth"]
            if "role" in st.query_params:
                del st.query_params["role"]
        except Exception:
            pass

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
                    <div class="signup-panel">
                        <div class="signup-panel-title">회원가입</div>
                        <p class="signup-panel-copy">프로토타입에서는 기본 정보만 입력하고 역할 선택으로 이동합니다.</p>

                        <label class="signup-field">
                            <span class="signup-label">이름</span>
                            <input class="signup-input" type="text" placeholder="예: 000" autocomplete="name">
                        </label>
                        <label class="signup-field">
                            <span class="signup-label">이메일</span>
                            <input class="signup-input" type="email" placeholder="user@example.com" autocomplete="email">
                        </label>
                        <label class="signup-field">
                            <span class="signup-label">비밀번호</span>
                            <input class="signup-input" type="password" placeholder="비밀번호" autocomplete="new-password">
                        </label>
                        <label class="signup-field">
                            <span class="signup-label">비밀번호 확인</span>
                            <input class="signup-input" type="password" placeholder="비밀번호 확인" autocomplete="new-password">
                        </label>
                        <div class="signup-field">
                            <span class="signup-label">회원 유형</span>
                            <div class="signup-role-links">
                                <a class="signup-role-link{user_role_active}" href="?auth=signup&amp;role=user" target="_self">이용자 (User)</a>
                                <a class="signup-role-link{admin_role_active}" href="?auth=signup&amp;role=admin" target="_self">기관 관리자 (Admin)</a>
                            </div>
                        </div>
                    </div>

                    <div class="auth-form-buttons">
                        <a class="auth-form-action back" href="?auth=entry" target="_self">이전</a>
                        <a class="auth-form-action next" href="?auth=signup_done" target="_self">계속</a>
                    </div>

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
                <div class="signup-panel">
                    <div class="signup-panel-title">로그인</div>
                    <p class="signup-panel-copy">프로토타입에서는 실제 인증 없이 다음 단계로 이동합니다.</p>

                    <label class="signup-field">
                        <span class="signup-label">이름</span>
                        <input class="signup-input" type="text" placeholder="예: 000" autocomplete="name">
                    </label>
                    <label class="signup-field">
                        <span class="signup-label">이메일</span>
                        <input class="signup-input" type="email" placeholder="user@example.com" autocomplete="email">
                    </label>
                    <label class="signup-field">
                        <span class="signup-label">비밀번호</span>
                        <input class="signup-input" type="password" placeholder="비밀번호" autocomplete="current-password">
                    </label>
                </div>

                <div class="auth-form-buttons">
                    <a class="auth-form-action back" href="?auth=entry" target="_self">이전</a>
                    <a class="auth-form-action next" href="?auth=login_done" target="_self">계속</a>
                </div>

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


def tab_icon_svg(kind: str) -> str:
    icons = {
        "brain": """
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M8.5 5.5a2.5 2.5 0 0 0-2.5 2.5V9a2 2 0 0 0-1.5 1.93V11a3.5 3.5 0 0 0 3.5 3.5V16a1.5 1.5 0 0 0 3 0v-1.5a3.5 3.5 0 0 0 3.5-3.5 2 2 0 0 0-1.5-1.93V8a2.5 2.5 0 0 0-2.5-2.5 1.75 1.75 0 0 0-3.5 0Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                <path d="M9 11.5c.5 1 1.5 1.5 3 1.5s2.5-.5 3-1.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
        """,
        "calendar_check": """
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="4" y="6" width="16" height="14" rx="3" stroke="currentColor" stroke-width="2"/>
                <path d="M8 4v4M16 4v4M4 10h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M9 15l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        """,
        "eye": """
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M2.5 12C4.6 7.8 8 5.5 12 5.5s7.4 2.3 9.5 6.5c-2.1 4.2-5.5 6.5-9.5 6.5S4.6 16.2 2.5 12Z" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="2.8" stroke="currentColor" stroke-width="2"/>
            </svg>
        """,
    }
    return icons.get(kind, "")


def handle_user_chrome_query() -> None:
    changed = False
    nav_tab = st.query_params.get("nav_tab")
    if nav_tab in {"main", "schedule", "accessibility"}:
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
    elif action == "logout":
        st.session_state.logged_in = False
        st.session_state.authenticated = False
        st.session_state.current_page = "main"
        st.session_state.main_step = "start"
        st.session_state.pending_confirm = None
        st.session_state.auth_name = ""
        st.session_state.auth_email = ""
        changed = True
    for key in ("nav_tab", "action"):
        if key in st.query_params:
            try:
                del st.query_params[key]
            except Exception:
                pass
    if changed:
        st.rerun()


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
    for page, label, icon_kind in USER_TABS:
        active = " active" if current_page == page else ""
        tab_links.append(
            f'<a class="app-tab{active}" href="?nav_tab={page}" target="_self">'
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
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                        <ellipse cx="12" cy="14" rx="7" ry="3" fill="currentColor" opacity=".35"/>
                                        <circle cx="12" cy="10" r="6" stroke="currentColor" stroke-width="2"/>
                                        <path d="M8.5 9.5h7M10 7.5h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
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
    normalized = origin.replace(" ", "")
    long_distance = any(token in normalized for token in ["성남", "신흥역", "분당", "수원", "서울역"])
    near_gimpo = any(token in normalized for token in ["김포", "구래", "장기", "운양", "마산"])

    if long_distance:
        total, walk, transfers = 86, 16, 2
        alternative = "장거리 · 이동지원 연계 검토"
        risk = "중간 이상"
        opinion = (
            "출발지가 성남권 또는 신흥역 권역으로 보입니다. 김포 반다비체육센터까지는 "
            "장거리 이동에 해당하므로 환승 여유와 이동지원센터 연계 검토가 필요합니다."
        )
        route = "성남권 출발지 → 수도권 전철 환승 → 김포골드라인 → 김포 반다비체육센터"
    elif near_gimpo:
        total, walk, transfers = 28, 8, 1
        alternative = "저상버스·센터 주변 보행 연계 가능"
        risk = "낮음"
        opinion = (
            "김포 관내 출발지로 확인되어 이동 부담이 비교적 낮습니다. "
            "센터 주변 마지막 보행 구간만 천천히 확인하면 무리가 적은 계획입니다."
        )
        route = "김포 관내 출발지 → 김포골드라인 또는 저상버스 → 센터 주변 보행"
    else:
        total, walk, transfers = 72, 13, 2
        alternative = "대체 이동수단 사전 문의 권장"
        risk = "중간"
        opinion = (
            "출발지와 센터 사이 이동 거리가 있는 편입니다. 대중교통과 이동지원 차량을 "
            "함께 검토하면 참여 가능성이 높아집니다."
        )
        route = "출발지 → 광역/도시철도 환승 → 김포 반다비체육센터"

    return {
        "origin": origin,
        "destination": DEFAULT_DESTINATION,
        "support": support,
        "recommended_route": route,
        "opinion": opinion,
        "total_time": f"약 {total}분",
        "walk_time": f"도보 약 {walk}분",
        "transfers": f"{transfers}회",
        "alternative": alternative,
        "walk_risk": risk,
        "weather_adjustment": "비 예보 시 도보 구간 6분 여유 권장",
        "facility_access": "센터 주출입구, 승강기, 접근 가능한 화장실 확인 필요",
        "bus_arrival": "저상버스 또는 이동지원 차량 시간 사전 확인",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def route_map_svg(result: dict[str, Any]) -> str:
    """Small native SVG that echoes the original HTML route-card visual."""
    route_note = "장거리 · 이동지원 검토" if "장거리" in result.get("alternative", "") else "센터 진입 180m"
    time_note = result.get("total_time", "예상 시간")
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
        <text x="340" y="131" text-anchor="middle" fill="#0e7490" font-size="13" font-weight="900">환승</text>
        <text x="625" y="186" text-anchor="middle" fill="#6d28d9" font-size="13" font-weight="900">하차</text>
        <text x="790" y="111" text-anchor="middle" fill="#92400e" font-size="13" font-weight="900">센터</text>
        <text x="250" y="96" fill="#7868a0" font-size="14">{esc(time_note)}</text>
        <text x="560" y="224" fill="#7868a0" font-size="14">{esc(route_note)}</text>
        <text x="410" y="164" fill="#6b4fa0" font-size="13" font-weight="800">주의 지점 확인</text>
      </svg>
    </div>
    """


def start_analysis() -> None:
    if st.session_state.get("destination_choice") == UNAVAILABLE_DESTINATION:
        block_unavailable_destination()
        return
    st.session_state.destination = DEFAULT_DESTINATION
    result = build_route_analysis()
    st.session_state.route_result = result
    st.session_state.route_analysis_result = result
    st.session_state.main_step = "route"
    st.session_state.current_page = "main"
    st.session_state.pending_confirm = None
    st.rerun()


def open_confirm(title: str, subtitle: str, message: str, next_step: str, **extra: Any) -> None:
    st.session_state.pending_confirm = {
        "title": title,
        "subtitle": subtitle,
        "message": message,
        "next_step": next_step,
        **extra,
    }


def apply_pending_confirm() -> None:
    pending = st.session_state.get("pending_confirm") or {}
    if pending.get("point_key"):
        add_points(int(pending.get("bt_delta", 0)), str(pending["point_key"]))
    if pending.get("confirm_buddy"):
        st.session_state.buddy_confirmed = True
    if pending.get("confirm_class"):
        st.session_state.class_confirmed = True
    st.session_state.main_step = pending.get("next_step", st.session_state.get("main_step", "start"))
    st.session_state.notice = pending.get("toast", "")
    st.session_state.pending_confirm = None
    st.rerun()


def render_pending_confirm() -> None:
    pending = st.session_state.get("pending_confirm")
    if not pending:
        return
    st.markdown(
        f"""
        <div class="section-card">
            <p class="tiny-label">Confirm</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-weight:900;">{esc(pending.get("title", "확정 요청"))}</h2>
            <p class="section-copy">{esc(pending.get("subtitle", ""))}</p>
            <div class="notice-box" style="margin-top:16px;">{esc(pending.get("message", ""))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("확인", key="pending_confirm_ok", type="primary"):
            apply_pending_confirm()
    with cols[1]:
        if st.button("취소", key="pending_confirm_cancel"):
            st.session_state.pending_confirm = None
            st.rerun()


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
        col1, col2 = st.columns(2)
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
            if st.button("⚡ AI 추천 시작", key="btn_ai_start", type="primary", use_container_width=True):
                start_analysis()
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


def render_route() -> None:
    result = st.session_state.get("route_result") or build_route_analysis()
    st.session_state.route_result = result
    st.session_state.route_analysis_result = result

    section_intro(
        "MAIN01",
        "AI 기반 도착 가능성 / 경로분석",
        "실제 API가 아닌 화면 검증용 mock 결과입니다. 장거리 출발지는 비현실적인 짧은 시간으로 표시하지 않습니다.",
        [result["origin"], result["destination"], result["support"]],
    )

    st.markdown(
        f"""
        <div class="section-card">
            <p class="tiny-label">추천 경로</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-size:24px;font-weight:900;line-height:1.28;">{esc(result["recommended_route"])}</h2>
            <p class="section-copy">{esc(result["opinion"])}</p>
            {route_map_svg(result)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    with cols[0]:
        metric_card("총 시간", result["total_time"], "참고용 예상 시간")
    with cols[1]:
        metric_card("도보", result["walk_time"], "마지막 접근 구간 포함")
    with cols[2]:
        metric_card("환승", result["transfers"], "여유 시간 반영 권장")
    with cols[3]:
        metric_card("대체 이동수단", result["alternative"], "이동지원 검토")

    cols = st.columns(4)
    with cols[0]:
        metric_card("도보 위험도", result["walk_risk"], "보행 환경 확인")
    with cols[1]:
        metric_card("날씨 보정", "여유 필요", result["weather_adjustment"])
    with cols[2]:
        metric_card("시설 접근성", "확인 필요", result["facility_access"])
    with cols[3]:
        metric_card("버스 도착", "사전 확인", result["bus_arrival"])

    st.markdown(
        """
        <div class="notice-box">
        운영 확정 요청을 등록하면 참여 인센티브 500BT가 적립됩니다. 반다비 포인트는 현금 환급·양도·재판매가 불가합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("다시하기", key="route_retry"):
            st.session_state.main_step = "start"
            st.rerun()
    with cols[1]:
        st.markdown('<div class="confirm-action">', unsafe_allow_html=True)
        if st.button("확정하기", key="route_confirm", type="primary"):
            open_confirm(
                "운영 확정 요청이 등록되었습니다.",
                "예약·이동·동행 플랜이 다음 단계로 연결됩니다.",
                "참여 인센티브 500BT가 적립됩니다. 현금 환급·양도·재판매는 불가하며 생활체육 서비스 혜택으로만 사용할 수 있습니다.",
                "care",
                bt_delta=500,
                point_key="route_points_awarded",
                toast="경로가 확정되었습니다. 버디 추천 화면으로 이동합니다.",
            )
            st.rerun()
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

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("건너뛰기", key="care_skip"):
            st.session_state.buddy_confirmed = False
            st.session_state.main_step = "class"
            st.session_state.notice = "버디 매칭을 건너뛰고 강습·지도자 추천으로 이동합니다."
            st.rerun()
    with cols[1]:
        st.markdown('<div class="confirm-action">', unsafe_allow_html=True)
        if st.button("확정하기", key="care_confirm", type="primary"):
            open_confirm(
                "버디 매칭 확정 요청이 등록되었습니다.",
                "상호 동의와 관리자 확인 후 연결됩니다.",
                "첫 방문 버디 후보 연결 요청이 등록되었습니다. 실명·연락처는 확정 전 비공개로 유지됩니다.",
                "class",
                confirm_buddy=True,
                toast="버디 후보가 임시 확정되었습니다. 강습·지도자 추천으로 이동합니다.",
            )
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


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

    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("다른 지도자", key="class_next"):
            st.session_state.instructor_index = (int(st.session_state.get("instructor_index", 0)) + 1) % len(INSTRUCTORS)
            st.rerun()
    with cols[1]:
        st.markdown('<div class="confirm-action">', unsafe_allow_html=True)
        if st.button("확정하기", key="class_confirm", type="primary"):
            open_confirm(
                "강습·지도자 추천이 확정되었습니다.",
                "운동 참여 결과를 리포트 화면에서 확인합니다.",
                "추천 지도자와 강습 선택이 등록되었습니다. 본 내용은 생활체육 참여 지원을 위한 참고자료입니다.",
                "report",
                confirm_class=True,
                toast="강습 추천이 확정되었습니다. 생활체육 리포트로 이동합니다.",
            )
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


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


def render_report() -> None:
    section_intro(
        "MAIN03",
        "AI 생활체육 리포트",
        "운동 후 변화와 다음 참여 가능성을 쉽게 확인하는 보호자 공유용 요약 화면입니다.",
        ["리포트 저장 +300BT", "개인정보 최소화", "참고용 지표"],
    )

    cols = st.columns(2)
    with cols[0]:
        metric_card("성취도 점수", "82점", "오늘 참여 조건을 기준으로 한 mock 점수")
    with cols[1]:
        metric_card("지속참여 점수", "76점", "다음 참여 가능성을 높이는 일정 추천 필요")

    cols = st.columns(2)
    with cols[0]:
        soft_card(
            "오늘의 참여 요약",
            "경로·동행·강습 흐름 완료",
            "센터 이동 계획과 강습 추천이 준비되었습니다. 실제 운영 확정은 기관 확인 후 진행됩니다.",
            ["이동지원 연계 예정", "보호자 알림 준비"],
        )
    with cols[1]:
        soft_card(
            "다음 생활체육 가이드",
            "무리 없는 반복 참여",
            "다음 주 동일 시간대 소그룹 강습과 이동지원 여유 시간을 함께 잡는 구성을 추천합니다.",
            ["수분 섭취", "도착 15분 여유", "쉬운 강도"],
        )

    st.markdown(
        """
        <div class="notice-box">
        포인트 적립 안내: 리포트 저장 시 참여 인센티브 300BT가 적립됩니다.
        반다비 포인트는 현금 환급·양도·재판매가 불가합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("리포트 저장 및 보호자 공유 요약 보기", key="report_save", type="primary"):
        add_points(300, "report_points_awarded")
        st.session_state.report_saved = True
        st.session_state.guardian_summary = guardian_summary_text()
        st.session_state.main_step = "guardian"
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
    render_pending_confirm()

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


def make_schedule_recommendations(days: list[str], time_range: str) -> list[dict[str, str]]:
    if not days:
        days = ["화", "목"]
    base_day = days[0]
    today = datetime.now()
    return [
        {
            "title": f"{base_day}요일 10:00",
            "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "reason": f"{time_range} 선호와 이동지원 여유 시간이 맞는 슬롯",
        },
        {
            "title": f"{days[-1]}요일 14:00",
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "reason": "버디 후보가 같은 센터를 이용하는 시간대",
        },
        {
            "title": "금요일 16:00",
            "date": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
            "reason": "혼잡도가 낮고 보호자 알림 공유가 쉬운 시간대",
        },
    ]


def render_schedule_page() -> None:
    section_intro(
        "Schedule AI",
        "내 운동 일정 추천",
        "선호 요일과 시간대, 이동지원 및 버디 우선순위를 반영해 예약 후보 3개를 제안합니다.",
        ["추천 시간 3개", "예약 흐름 연결", "mock 일정"],
    )
    col1, col2 = st.columns(2)
    with col1:
        days = st.multiselect("선호 요일", ["월", "화", "수", "목", "금", "토"], default=["화", "목"])
        time_range = st.selectbox("선호 시간대", ["오전", "오후", "저녁"], index=0)
    with col2:
        mobility_first = st.checkbox("이동지원 우선", value=True)
        buddy_first = st.checkbox("버디 후보 우선", value=True)
        st.markdown(
            f"""
            <div class="notice-box">
            우선순위: 이동지원 {'우선' if mobility_first else '일반'} · 버디 후보 {'우선' if buddy_first else '일반'}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("추천 시간 보기", key="schedule_generate", type="primary"):
        st.session_state.schedule_recommendations = make_schedule_recommendations(days, time_range)
        st.rerun()

    if not st.session_state.get("schedule_recommendations"):
        st.session_state.schedule_recommendations = make_schedule_recommendations(days, time_range)

    cols = st.columns(3)
    for idx, item in enumerate(st.session_state.schedule_recommendations):
        with cols[idx]:
            soft_card("추천 시간", item["title"], f"{item['date']} · {item['reason']}", ["김포 반다비체육센터"])
            if st.button("이 시간으로 예약 이어가기", key=f"schedule_pick_{idx}", type="primary"):
                st.session_state.selected_schedule = f"{item['date']} {item['title']}"
                st.session_state.current_page = "main"
                st.session_state.main_step = "start"
                st.session_state.notice = f"선택한 시간({st.session_state.selected_schedule}) 기준으로 예약 흐름을 이어갑니다."
                st.rerun()


def mock_accessibility_result(report_type: str) -> dict[str, Any]:
    return {
        "source": "mock",
        "report_type": report_type,
        "status": "검토 요청 권장",
        "risk": "개선 필요 가능성 높음",
        "summary": (
            "사진 기준으로 보행 유도 동선의 끊김 또는 문턱 가능성이 보입니다. "
            "공식 판정이 아닌 접근성 점검 보조 결과이며, 현장 담당자의 확인이 필요합니다."
        ),
        "notices": [
            "공식 인증·법적 적합 판정을 대체하지 않습니다.",
            "제출 전 얼굴, 전화번호, 차량번호 등 개인정보는 마스킹해 주세요.",
        ],
    }


def build_official_draft(report: dict[str, Any]) -> tuple[str, str]:
    subject = f"[접근성 점검 요청] {DEFAULT_DESTINATION} {report.get('report_type', '시설 동선')} 확인 요청"
    body = (
        "안녕하세요.\n\n"
        f"{DEFAULT_DESTINATION} 이용 과정에서 접근성 확인이 필요한 지점이 있어 검토를 요청드립니다.\n\n"
        f"- 제보 유형: {report.get('report_type', '접근성 점검')}\n"
        f"- AI 점검 보조 요약: {report.get('summary', '')}\n"
        "- 요청 사항: 현장 확인 후 보행 동선, 안내 표식, 안전 조치 필요 여부를 검토해 주세요.\n\n"
        "본 내용은 이용자 제보와 AI 보조 요약을 바탕으로 작성된 초안이며, 최종 판단은 담당 기관의 현장 확인을 따릅니다."
    )
    return subject, body


def render_accessibility_page() -> None:
    section_intro(
        "AI Vision",
        "접근성 점검 보조",
        "사진 제보를 기반으로 접근성 확인이 필요한 지점을 카드와 공문 초안으로 정리합니다.",
        ["st.file_uploader", "미리보기", "SendGrid payload 미리보기만 제공"],
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        report_type = st.selectbox(
            "점검 유형",
            ["점자블록 단절", "경사로", "출입문 문턱", "화장실 접근성", "승강기 안내"],
            key="vision_report_type",
        )
        uploaded = st.file_uploader(
            "시설 사진 업로드",
            type=["jpg", "jpeg", "png", "webp"],
            help="개인정보가 포함된 사진은 제출 전 마스킹해 주세요.",
        )
        if uploaded is not None:
            st.image(uploaded, caption="업로드 사진 미리보기", use_column_width=True)
        else:
            st.markdown(
                """
                <div class="notice-box">
                아직 선택된 사진이 없습니다. 사진 없이도 예시 결과를 생성해 화면 흐름을 확인할 수 있습니다.
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button("AI 점검 보조 결과 생성", key="vision_demo_analyze", type="primary"):
            result = mock_accessibility_result(report_type)
            st.session_state.accessibility_report = result
            st.session_state.vision_result = result
            st.session_state.vision_last_report_type = report_type
            st.rerun()

    with col2:
        report = st.session_state.get("accessibility_report")
        if report:
            metric_card("AI 점검 보조 결과", report["risk"], report["status"])
            st.markdown(
                f"""
                <div class="section-card">
                    <p class="tiny-label">Result</p>
                    <p class="section-copy" style="margin-top:0;">{esc(report["summary"])}</p>
                    <div class="chip-row">
                        {''.join(f"<span class='chip'>{esc(item)}</span>" for item in report["notices"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("접근성 제보 저장", key="vision_save_report"):
                add_points(200, "accessibility_points_awarded")
                st.session_state.notice = "접근성 제보 참여 인센티브 200BT가 적립되었습니다. 현금 환급·양도·재판매는 불가합니다."
                st.rerun()
        else:
            metric_card("AI 점검 보조 결과", "대기", "사진 업로드 또는 예시 분석 실행 전입니다.")

    report = st.session_state.get("accessibility_report") or mock_accessibility_result(
        st.session_state.get("vision_report_type", "점자블록 단절")
    )
    default_subject, default_body = build_official_draft(report)

    section_intro(
        "Official Draft",
        "공문 초안 생성",
        "실제 발송 버튼은 제공하지 않습니다. 아래 payload는 SendGrid 연동 시 전달 형식을 미리 보여주는 mock입니다.",
        ["발송 없음", "API Key 미표시", "초안 수정 가능"],
    )

    col1, col2 = st.columns(2)
    with col1:
        to_email = st.text_input("수신자 이메일", value="accessibility@gimpo.example.kr")
        from_name = st.text_input("발신자 이름", value=st.session_state.get("user_name") or "반다비 이용자")
        from_email = st.text_input(
            "발신자 이메일",
            value=st.session_state.get("user_email") or "bandabi.user@example.com",
        )
        subject = st.text_input("공문 제목", value=default_subject)
    with col2:
        body = st.text_area("공문 본문", value=default_body, height=260)

    payload = {
        "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
        "from": {"email": from_email, "name": from_name},
        "content": [{"type": "text/plain", "value": body}],
        "send_disabled": True,
        "note": "실제 SendGrid 발송은 이 화면에서 실행하지 않습니다. API Key 값도 표시하지 않습니다.",
    }
    st.markdown("<div class='notice-box'>SendGrid payload 미리보기</div>", unsafe_allow_html=True)
    st.json(payload)


def render_dashboard_page() -> None:
    if st.session_state.get("role") != ADMIN_ROLE:
        st.session_state.current_page = "main"
        st.warning("기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다.")
        render_main_page()
        return

    section_intro(
        "B2G Dashboard",
        "기관용 대시보드",
        "예약, 이동지원, 피어 매칭, 접근성 제보 흐름을 한 화면에서 보는 mock 운영 보드입니다.",
        ["실제 key 값 미표시", "FastAPI 호출 없음", "CSV/RAG/API status mock"],
    )

    cols = st.columns(4)
    with cols[0]:
        metric_card("출석률", "94.2%", "예약 대비 참여")
    with cols[1]:
        metric_card("배차 성공률", "88.7%", "이동지원 연계")
    with cols[2]:
        metric_card("피어 매칭률", "76.4%", "버디 후보 연결")
    with cols[3]:
        metric_card("접근성 제보 수", "18건", "검토 대기 4건")

    st.markdown(
        """
        <div class="section-card">
            <p class="tiny-label">공공데이터 연결 상태</p>
            <h2 style="margin:0;color:var(--bandabi-ink);font-weight:900;">운영 데이터 상태 카드</h2>
            <p class="section-copy">아래 상태는 화면 검증용입니다. API Key나 secrets 값은 읽거나 표시하지 않습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    with cols[0]:
        metric_card("CSV", "준비됨", "data/ 배치 기준 mock")
    with cols[1]:
        metric_card("RAG", "대기", "docs/ 문서 연결 예정")
    with cols[2]:
        metric_card("공공 API", "키 미표시", "실제 호출 없음")
    with cols[3]:
        metric_card("SendGrid", "발송 비활성", "payload preview only")

    if pd is not None:
        st.markdown("<div class='notice-box'>접근성 지원 필요 유형별 이용 비율</div>", unsafe_allow_html=True)
        chart_df = pd.DataFrame(
            {
                "유형": ["보행 보조", "시각 안내", "청각 안내", "단계별 안내"],
                "이용률": [48, 18, 12, 22],
            }
        ).set_index("유형")
        st.bar_chart(chart_df, use_container_width=True)

        action_df = pd.DataFrame(
            [
                ["노쇼 공백", "수중 생활체육 10:00 슬롯", "대기자 2명 삽입 가능", "알림 대기"],
                ["접근성", "점자블록 단절 제보", "현장 확인 및 조치 검토", "검토 요청"],
                ["이동지원", "오후 배차 지연 가능성", "예약 15분 앞당김 권장", "운영 확인"],
            ],
            columns=["구분", "내용", "AI 추천", "상태"],
        )
        st.dataframe(action_df, use_container_width=True, hide_index=True)
    else:
        st.info("pandas를 사용할 수 없어 차트와 표는 생략되었습니다.")


def render_app() -> None:
    init_state()
    inject_css()

    if not st.session_state.get("logged_in"):
        render_auth()
        return

    if st.session_state.get("role") == USER_ROLE:
        handle_user_chrome_query()
        render_user_topbar()
    else:
        render_header()
        render_nav()

    render_notice()

    page = st.session_state.get("current_page", "main")
    if st.session_state.get("role") == ADMIN_ROLE:
        st.session_state.current_page = "dashboard"
        render_dashboard_page()
        return

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
        st.session_state.current_page = "main"
        render_main_page()


render_app()
