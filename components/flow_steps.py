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
        "route": "경로",
        "care": "동행",
        "class": "강습",
        "report": "리포트",
    }
    try:
        current_index = FLOW_ORDER.index(current_step)
    except ValueError:
        current_index = -1

    cols = st.columns(4)
    for idx, step_id in enumerate(FLOW_ORDER):
        if idx == current_index:
            css = "active"
        elif current_index >= 0 and idx < current_index:
            css = "done"
        else:
            css = ""
        with cols[idx]:
            st.markdown(
                f'<div class="bandabi-flow-step {css}">{s(labels[step_id])}</div>',
                unsafe_allow_html=True,
            )
