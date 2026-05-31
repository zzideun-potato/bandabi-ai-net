"""Shared Streamlit UI components for the Vandabi AI Net app."""

from __future__ import annotations

import html

import streamlit as st


STATUS_CLASS = {
    "default": "default",
    "info": "info",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "purple": "purple",
    "muted": "muted",
}


def _status(status: str) -> str:
    return STATUS_CLASS.get(status, "default")


def _esc(value: object) -> str:
    return html.escape(str(value))


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --vandabi-bg: #0f172a;
            --vandabi-panel: #111c33;
            --vandabi-panel-2: #16223a;
            --vandabi-border: rgba(148, 163, 184, 0.24);
            --vandabi-text: #e5edf7;
            --vandabi-muted: #aab8cf;
            --vandabi-blue: #38bdf8;
            --vandabi-purple: #a78bfa;
            --vandabi-emerald: #34d399;
            --vandabi-amber: #fbbf24;
            --vandabi-red: #f87171;
        }
        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(56, 189, 248, 0.12), transparent 30%),
                radial-gradient(circle at 92% 14%, rgba(167, 139, 250, 0.12), transparent 28%),
                var(--vandabi-bg);
            color: var(--vandabi-text);
        }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1180px; }
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown { color: var(--vandabi-text); }
        [data-testid="stSidebar"] {
            background: #0b1222;
            border-right: 1px solid var(--vandabi-border);
        }
        [data-testid="stSidebar"] * { color: var(--vandabi-text); }
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            border: 1px solid var(--vandabi-border);
            border-radius: 14px;
            background: rgba(17, 28, 51, 0.78);
        }
        div.stButton > button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 10px;
            border: 1px solid rgba(56, 189, 248, 0.35);
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            color: white;
            font-weight: 700;
            min-height: 2.65rem;
        }
        div.stButton > button:disabled {
            background: #334155;
            border-color: #475569;
            color: #cbd5e1;
        }
        .vandabi-hero {
            border: 1px solid var(--vandabi-border);
            border-radius: 18px;
            padding: clamp(22px, 4vw, 34px);
            margin: 0 0 18px;
            background:
                linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(167, 139, 250, 0.12)),
                rgba(17, 28, 51, 0.92);
            box-shadow: 0 18px 50px rgba(2, 6, 23, 0.26);
        }
        .vandabi-hero h1 {
            margin: 0 0 10px;
            font-size: clamp(2rem, 5vw, 3.4rem);
            line-height: 1.1;
            letter-spacing: 0;
        }
        .vandabi-hero p {
            max-width: 860px;
            color: var(--vandabi-muted);
            font-size: 1.05rem;
            line-height: 1.65;
            margin: 0;
        }
        .vandabi-section-kicker {
            color: var(--vandabi-blue);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0;
            margin-bottom: 6px;
        }
        .vandabi-section-title {
            font-size: clamp(1.35rem, 3vw, 2rem);
            font-weight: 800;
            margin-bottom: 6px;
        }
        .vandabi-section-desc {
            color: var(--vandabi-muted);
            line-height: 1.6;
            margin-bottom: 14px;
        }
        .vandabi-card, .vandabi-metric, .vandabi-box {
            border: 1px solid var(--vandabi-border);
            border-radius: 14px;
            background: rgba(17, 28, 51, 0.84);
            box-shadow: 0 12px 30px rgba(2, 6, 23, 0.18);
        }
        .vandabi-card {
            padding: 18px;
            min-height: 136px;
            margin-bottom: 12px;
        }
        .vandabi-card h3 {
            font-size: 1.04rem;
            margin: 0 0 8px;
            color: var(--vandabi-text);
        }
        .vandabi-card p {
            font-size: 0.94rem;
            line-height: 1.58;
            color: var(--vandabi-muted);
            margin: 0;
        }
        .vandabi-card.info { border-color: rgba(56, 189, 248, 0.42); }
        .vandabi-card.success { border-color: rgba(52, 211, 153, 0.42); }
        .vandabi-card.warning { border-color: rgba(251, 191, 36, 0.48); }
        .vandabi-card.danger { border-color: rgba(248, 113, 113, 0.48); }
        .vandabi-card.purple { border-color: rgba(167, 139, 250, 0.48); }
        .vandabi-card.muted { border-color: rgba(148, 163, 184, 0.22); background: rgba(15, 23, 42, 0.72); }
        .vandabi-metric {
            padding: 15px 16px;
            min-height: 112px;
            margin-bottom: 12px;
        }
        .vandabi-metric .label {
            color: var(--vandabi-muted);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .vandabi-metric .value {
            color: var(--vandabi-text);
            font-size: clamp(1.25rem, 3vw, 1.75rem);
            font-weight: 850;
            line-height: 1.2;
            word-break: break-word;
        }
        .vandabi-metric .helper {
            color: var(--vandabi-muted);
            font-size: 0.83rem;
            margin-top: 8px;
        }
        .vandabi-metric.info { border-color: rgba(56, 189, 248, 0.42); }
        .vandabi-metric.success { border-color: rgba(52, 211, 153, 0.42); }
        .vandabi-metric.warning { border-color: rgba(251, 191, 36, 0.48); }
        .vandabi-metric.danger { border-color: rgba(248, 113, 113, 0.48); }
        .vandabi-metric.purple { border-color: rgba(167, 139, 250, 0.48); }
        .vandabi-metric.muted { background: rgba(15, 23, 42, 0.72); }
        .vandabi-box {
            padding: 14px 16px;
            margin: 10px 0;
            color: var(--vandabi-text);
            line-height: 1.6;
        }
        .vandabi-box.info { border-color: rgba(56, 189, 248, 0.42); background: rgba(14, 116, 144, 0.16); }
        .vandabi-box.warning { border-color: rgba(251, 191, 36, 0.58); background: rgba(120, 83, 12, 0.22); }
        .vandabi-box.danger { border-color: rgba(248, 113, 113, 0.55); background: rgba(127, 29, 29, 0.20); }
        .vandabi-box.muted { border-color: rgba(148, 163, 184, 0.22); background: rgba(15, 23, 42, 0.72); }
        .vandabi-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.78rem;
            font-weight: 800;
            margin: 2px 4px 8px 0;
            border: 1px solid rgba(148, 163, 184, 0.30);
            color: var(--vandabi-text);
            background: rgba(30, 41, 59, 0.88);
        }
        .vandabi-badge.info { border-color: rgba(56, 189, 248, 0.48); color: #bae6fd; }
        .vandabi-badge.success { border-color: rgba(52, 211, 153, 0.48); color: #bbf7d0; }
        .vandabi-badge.warning { border-color: rgba(251, 191, 36, 0.58); color: #fde68a; }
        .vandabi-badge.danger { border-color: rgba(248, 113, 113, 0.58); color: #fecaca; }
        .vandabi-badge.purple { border-color: rgba(167, 139, 250, 0.58); color: #ddd6fe; }
        .vandabi-badge.muted { color: var(--vandabi-muted); }
        .vandabi-footer {
            color: var(--vandabi-muted);
            border-top: 1px solid var(--vandabi-border);
            padding-top: 14px;
            margin-top: 28px;
            font-size: 0.9rem;
        }
        @media (max-width: 760px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .vandabi-card, .vandabi-metric { min-height: auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(title: str, subtitle: str | None = None, mode_badge: str | None = None) -> None:
    badge = f'<span class="vandabi-badge purple">{_esc(mode_badge)}</span>' if mode_badge else ""
    st.markdown(
        f"""
        <div class="vandabi-hero">
            {badge}
            <h1>{_esc(title)}</h1>
            <p>{_esc(subtitle or "")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(label: str, title: str, description: str | None = None, icon: str | None = None) -> None:
    icon_text = f"{_esc(icon)} " if icon else ""
    st.markdown(
        f"""
        <div class="vandabi-section">
            <div class="vandabi-section-kicker">{_esc(label)}</div>
            <div class="vandabi-section-title">{icon_text}{_esc(title)}</div>
            <div class="vandabi-section-desc">{_esc(description or "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: object, helper: str | None = None, status: str = "default") -> None:
    st.markdown(
        f"""
        <div class="vandabi-metric {_status(status)}">
            <div class="label">{_esc(label)}</div>
            <div class="value">{_esc(value)}</div>
            <div class="helper">{_esc(helper or "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(text: str, status: str = "default") -> None:
    st.markdown(
        f'<span class="vandabi-badge {_status(status)}">{_esc(text)}</span>',
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str, icon: str | None = None, status: str = "default") -> None:
    icon_text = f"{_esc(icon)} " if icon else ""
    st.markdown(
        f"""
        <div class="vandabi-card {_status(status)}">
            <h3>{icon_text}{_esc(title)}</h3>
            <p>{_esc(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_warning_box(message: str) -> None:
    st.markdown(f'<div class="vandabi-box warning">{_esc(message)}</div>', unsafe_allow_html=True)


def render_disclaimer_box(message: str) -> None:
    st.markdown(f'<div class="vandabi-box muted">{_esc(message)}</div>', unsafe_allow_html=True)


def render_page_footer_note() -> None:
    st.markdown(
        '<div class="vandabi-footer">파일럿 참고 시스템입니다. 공식 판단, 실행, 접수 결과가 아니며 관리자 확인이 필요합니다.</div>',
        unsafe_allow_html=True,
    )


def inject_base_styles() -> None:
    inject_global_styles()


def section_header(title: str, description: str = "") -> None:
    render_section_header("SECTION", title, description)


def metric_card(label: str, value: object, help_text: str = "", status: str = "default") -> None:
    render_metric_card(label, value, help_text, status=status)


def info_box(message: str) -> None:
    st.markdown(f'<div class="vandabi-box info">{_esc(message)}</div>', unsafe_allow_html=True)


def warning_box(message: str) -> None:
    render_warning_box(message)


def status_badge(label: str, status: str = "default") -> None:
    render_status_badge(label, status=status)


def feature_card(title: str, body: str) -> None:
    render_info_card(title, body, status="default")
