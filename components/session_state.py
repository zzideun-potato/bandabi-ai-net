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
