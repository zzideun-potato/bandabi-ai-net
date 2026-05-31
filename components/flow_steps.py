"""Flow step indicator for tab1 user journey."""

from __future__ import annotations

import streamlit as st

from modules.safety import sanitize_public_claims


FLOW_ORDER = ["route", "care", "class", "report"]


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def render_flow_steps(current_step: str) -> None:
    if current_step in {"start", "guardian", "route_loading"}:
        return

    labels = {
        "route": ("경로", "fa-route"),
        "care": ("동행", "fa-user-group"),
        "class": ("강습", "fa-person-chalkboard"),
        "report": ("리포트", "fa-chart-line"),
    }
    try:
        current_index = FLOW_ORDER.index(current_step)
    except ValueError:
        current_index = -1

    st.markdown('<div class="bandabi-glass bandabi-flow-wrap">', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, step_id in enumerate(FLOW_ORDER):
        if idx == current_index:
            css = "active"
        elif current_index >= 0 and idx < current_index:
            css = "done"
        else:
            css = ""
        label, icon = labels[step_id]
        with cols[idx]:
            st.markdown(
                f"""
                <div class="bandabi-flow-step {css}">
                  <i class="fa-solid {icon}" aria-hidden="true"></i><br/>
                  {s(label)}
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)
