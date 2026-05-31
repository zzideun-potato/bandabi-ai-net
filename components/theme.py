"""Purple design tokens from bandabi_purple HTML — does not modify modules/."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def inject_purple_theme(*, high_contrast: bool = False) -> None:
    """Inject HTML-aligned purple tokens, Pretendard, cards, and optional high-contrast mode."""
    hc = "1" if high_contrast else "0"
    st.markdown(
        f"""
        <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
        <style>
        :root {{
            --ink: #2d2040;
            --mid: #7868a0;
            --lav: #b8acd8;
            --lav-dim: rgba(184,172,216,.20);
            --lav-line: rgba(184,172,216,.28);
            --surface: #f0ecf8;
            --base: #e8e2f4;
            --white: #ffffff;
            --accent: #4a2d7a;
            --accent-2: #6b4fa0;
        }}
        .stApp {{
            background: var(--base) !important;
            color: var(--ink) !important;
            font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        }}
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        h1, h2, h3, h4, h5, h6, p, li, label, span, .stMarkdown {{
            font-family: inherit;
        }}
        h1, h2, h3, h4 {{ color: var(--ink) !important; font-weight: 900 !important; letter-spacing: -.03em; }}
        p, li, label {{ color: var(--ink); }}
        [data-testid="stSidebar"] {{ display: none; }}
        div[data-testid="stVerticalBlock"] > div:has(> div.bandabi-shell) {{
            gap: 0.5rem;
        }}
        .bandabi-glass {{
            background: var(--white);
            border: 1px solid var(--lav-line);
            border-radius: 18px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 2px 6px rgba(109,40,217,.06), 0 8px 24px rgba(109,40,217,.09);
            margin-bottom: 1rem;
        }}
        .bandabi-soft {{
            background: var(--surface);
            border: 1px solid var(--lav-line);
            border-radius: 12px;
            padding: 0.85rem 1rem;
        }}
        .bandabi-tiny {{
            font-size: 10px;
            font-weight: 600;
            letter-spacing: .12em;
            color: var(--accent-2);
            text-transform: uppercase;
        }}
        .bandabi-mid {{ color: var(--mid); }}
        .bandabi-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 800;
            border: 1px solid var(--lav-line);
            background: var(--surface);
            color: var(--ink);
            margin: 2px 4px 6px 0;
        }}
        .bandabi-badge.accent {{ background: rgba(74,45,122,.12); color: var(--accent); border-color: rgba(74,45,122,.25); }}
        .bandabi-badge.warn {{ background: rgba(120,104,160,.15); color: var(--accent); }}
        .bandabi-badge.ok {{ background: rgba(74,45,122,.18); color: var(--accent); }}
        .bandabi-badge.no-data {{ background: var(--surface); color: var(--mid); border-style: dashed; }}
        .bandabi-header {{
            background: rgba(232,226,244,.92);
            border: 1px solid var(--lav-line);
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(12px);
        }}
        .bandabi-tab-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            background: var(--surface);
            border: 1px solid var(--lav-line);
            border-radius: 14px;
            padding: 4px;
        }}
        .bandabi-flow-step {{
            border-radius: 12px;
            border: 1px solid var(--lav-line);
            background: var(--surface);
            color: var(--mid);
            font-weight: 600;
            font-size: 12px;
            padding: 10px 8px;
            text-align: center;
        }}
        .bandabi-flow-step.active {{
            background: var(--accent);
            color: #fff !important;
            border-color: rgba(109,40,217,.4);
            box-shadow: 0 4px 14px rgba(109,40,217,.22);
        }}
        .bandabi-flow-step.done {{
            background: rgba(184,172,216,.18);
            color: var(--accent);
        }}
        div.stButton > button {{
            border-radius: 12px;
            min-height: 2.75rem;
            font-weight: 700;
            font-family: inherit;
            border: 1px solid var(--lav-line);
        }}
        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {{
            background: var(--accent) !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(109,40,217,.24);
        }}
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
        .stTextArea textarea {{
            border-radius: 12px !important;
            border-color: var(--lav-line) !important;
            background: var(--white) !important;
            color: var(--ink) !important;
            font-family: inherit !important;
        }}
        .bandabi-modal-note {{
            font-size: 11px;
            color: var(--mid);
            line-height: 1.65;
            border-radius: 12px;
            background: var(--surface);
            border: 1px solid var(--lav-line);
            padding: 12px;
        }}
        body.high-contrast-active, body.high-contrast-active .stApp {{
            background: #000 !important;
            color: #ffff00 !important;
        }}
        body.high-contrast-active * {{
            border-color: #ffff00 !important;
            color: #ffff00 !important;
            box-shadow: none !important;
        }}
        body.high-contrast-active div.stButton > button[kind="primary"],
        body.high-contrast-active .bandabi-flow-step.active {{
            background: #ffff00 !important;
            color: #000 !important;
        }}
        </style>
        <div data-bandabi-hc="{hc}" aria-hidden="true" style="display:none"></div>
        """,
        unsafe_allow_html=True,
    )
    components.html(
        f"""
        <script>
        (function() {{
            var on = {json.dumps(bool(high_contrast))};
            document.body.classList.toggle('high-contrast-active', on);
        }})();
        </script>
        """,
        height=0,
    )
