"""Central session_state initialization for the single-page app."""

from __future__ import annotations

import streamlit as st


TAB_MAIN = "main"
TAB_SCHEDULE = "schedule"
TAB_VISION = "vision"
TAB_DASHBOARD = "dashboard"

ROLE_B2C = "B2C"
ROLE_B2G = "B2G"


def default_active_tab_for_role(role: str | None) -> str:
    """B2G defaults to dashboard; extend here when dashboard tab is built out."""
    if role == ROLE_B2G:
        return TAB_DASHBOARD
    return TAB_MAIN


def init_session_state() -> None:
    defaults: dict = {
        "authenticated": False,
        "auth_step": "entry",
        "auth_mode": "login",
        "user_name": "",
        "user_email": "",
        "role": None,
        "bt_balance": 3500,
        "active_tab": TAB_MAIN,
        "main_step": "start",
        "high_contrast": False,
        "route_analysis_result": None,
        "route_analyzing": False,
        "journey": {},
        "instructor_index": 0,
        "pending_confirm": None,
        "toast_message": "",
        "buddy_skipped": False,
        "report_saved": False,
        "vision_result": None,
        "vision_scanning": False,
        "vision_last_report_type": "",
        "toggle_guardian": True,
        "toggle_buddy": True,
        "toggle_class": True,
        "toggle_report": True,
        "schedule_slots": [],
        "gov_to_email": "facility@gimpo.go.kr",
        "gov_from_name": "김포 반다비 AI 운영팀",
        "gov_from_email": "no-reply@bandabi-ai.kr",
        "gov_subject": "김포 반다비체육센터 접근성 위험 요소 개선 검토 요청",
        "gov_body": (
            "수신: 김포시 시설관리 담당부서\n\n"
            "제목: 김포 반다비체육센터 접근성 위험 요소 개선 검토 요청\n\n"
            "김포 반다비체육센터 1층 로비 구간에서 점자블록 단절 및 휠체어 회전 공간 부족이 의심되는 제보가 접수되었습니다.\n\n"
            "본 내용은 AI 기반 접근성 점검 보조 결과와 이용자 제보를 바탕으로 생성된 관리자 검토용 초안입니다. "
            "실제 시설 적합 여부와 개선 필요성은 담당자 현장 확인 후 판단해 주시기 바랍니다."
        ),
        "sendgrid_payload_preview": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_auth() -> None:
    st.session_state.authenticated = False
    st.session_state.auth_step = "entry"
    st.session_state.auth_mode = "login"
    st.session_state.role = None
    st.session_state.active_tab = TAB_MAIN
    st.session_state.main_step = "start"
    st.session_state.route_analysis_result = None
    st.session_state.route_analyzing = False
    st.session_state.journey = {}
    st.session_state.pending_confirm = None


def complete_role_login(role: str, user_name: str) -> None:
    st.session_state.authenticated = True
    st.session_state.role = role
    st.session_state.user_name = user_name or "000"
    st.session_state.auth_step = "done"
    st.session_state.active_tab = default_active_tab_for_role(role)
    st.session_state.main_step = "start"
