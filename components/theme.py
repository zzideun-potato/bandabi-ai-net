"""Purple design tokens from bandabi_purple HTML — does not modify modules/."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def inject_purple_theme(*, high_contrast: bool = False) -> None:
    """Inject HTML-aligned purple tokens, Pretendard, cards, Streamlit chrome hiding."""
    hc = "1" if high_contrast else "0"
    st.markdown(
        f"""
        <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
        <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.0/css/all.min.css" />
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
            --confirm: #a8e6c4;
            --confirm-ink: #1a5c38;
        }}
        #MainMenu {{ visibility: hidden; height: 0; }}
        header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0 !important;
            min-height: 0 !important;
        }}
        footer, footer[data-testid="stFooter"] {{
            visibility: hidden;
            height: 0 !important;
        }}
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {{ display: none !important; }}
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton {{ display: none !important; }}
        .stApp {{
            background: var(--base) !important;
            color: var(--ink) !important;
            font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        }}
        .block-container {{
            padding-top: 0.75rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: var(--ink) !important;
            font-weight: 900 !important;
            letter-spacing: -.03em;
        }}
        p, li, label, span, .stMarkdown, .stCaption {{ font-family: inherit; color: var(--ink); }}
        .stCaption, [data-testid="stCaptionContainer"] {{ color: var(--mid) !important; }}
        .vandabi-box, .vandabi-box.muted, .vandabi-footer {{
            background: var(--surface) !important;
            border: 1px solid var(--lav-line) !important;
            border-radius: 12px !important;
            color: var(--ink) !important;
            padding: 12px 14px !important;
            margin-bottom: 10px;
            box-shadow: 0 1px 4px rgba(109,40,217,.05) !important;
        }}
        .bandabi-glass, .bandabi-toss-card {{
            background: var(--white) !important;
            border: 1px solid var(--lav-line) !important;
            border-radius: 18px !important;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 2px 6px rgba(109,40,217,.06), 0 8px 24px rgba(109,40,217,.09);
            margin-bottom: 1rem;
        }}
        .bandabi-soft {{
            background: var(--surface) !important;
            border: 1px solid var(--lav-line) !important;
            border-radius: 12px !important;
            padding: 0.85rem 1rem;
        }}
        .bandabi-tiny {{
            font-size: 10px;
            font-weight: 600;
            letter-spacing: .12em;
            color: var(--accent-2);
            text-transform: uppercase;
            margin: 0 0 6px 0;
        }}
        .bandabi-mid {{ color: var(--mid) !important; }}
        .bandabi-hero-title {{
            font-size: clamp(1.6rem, 4vw, 2.25rem);
            font-weight: 900;
            line-height: 1.15;
            margin: 8px 0;
        }}
        .bandabi-risk-grade {{
            font-size: 1.75rem;
            font-weight: 900;
            color: var(--accent);
            margin: 6px 0;
        }}
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
        .bandabi-badge.accent {{ background: rgba(74,45,122,.12); color: var(--accent); }}
        .bandabi-badge.warn {{ background: rgba(120,104,160,.15); color: var(--accent); }}
        .bandabi-badge.ok {{ background: rgba(74,45,122,.18); color: var(--accent); }}
        .bandabi-badge.no-data {{ background: var(--surface); color: var(--mid); border-style: dashed; }}
        .bandabi-app-header {{
            background: rgba(232,226,244,.92);
            border: 1px solid var(--lav-line);
            border-radius: 16px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }}
        .bandabi-header-row {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}
        .bandabi-brand {{ display: flex; align-items: center; gap: 12px; }}
        .bandabi-brand-logo {{
            flex-shrink: 0;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(109,40,217,.18);
        }}
        .bandabi-brand-title {{ font-size: 1.1rem; font-weight: 900; color: var(--ink); }}
        .bandabi-brand-sub {{ font-size: .85rem; color: var(--mid); font-weight: 700; }}
        .bandabi-tab-shell {{
            background: var(--surface);
            border: 1px solid var(--lav-line);
            border-radius: 14px;
            padding: 4px;
            margin-bottom: 14px;
        }}
        .bandabi-tab-shell div.stButton > button {{
            border-radius: 10px !important;
            min-height: 2.65rem !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            background: transparent !important;
            color: var(--mid) !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
        }}
        .bandabi-tab-shell div.stButton > button[kind="primary"],
        .bandabi-tab-shell div.stButton > button[data-testid="baseButton-primary"] {{
            background: var(--accent) !important;
            color: #fff !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(109,40,217,.22) !important;
        }}
        .bandabi-toolbar div.stButton > button {{
            border-radius: 12px !important;
            min-height: 2.5rem !important;
            font-weight: 700 !important;
            background: var(--surface) !important;
            color: var(--ink) !important;
            border: 1px solid var(--lav-line) !important;
            box-shadow: none !important;
        }}
        .bandabi-flow-wrap {{ padding: 12px !important; margin-bottom: 14px; }}
        .bandabi-flow-step {{
            border-radius: 12px;
            border: 1px solid var(--lav-line);
            background: var(--surface);
            color: var(--mid);
            font-weight: 700;
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
            border-radius: 12px !important;
            min-height: 2.75rem !important;
            font-weight: 700 !important;
            font-family: inherit !important;
            border: 1px solid var(--lav-line) !important;
            background: var(--white) !important;
            color: var(--ink) !important;
        }}
        div.stButton > button[kind="primary"],
        div.stButton > button[data-testid="baseButton-primary"] {{
            background: var(--accent) !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(109,40,217,.24) !important;
        }}
        .bandabi-btn-confirm div.stButton > button[kind="primary"],
        .bandabi-btn-confirm div.stButton > button[data-testid="baseButton-primary"] {{
            background: var(--confirm) !important;
            color: var(--confirm-ink) !important;
            border: 1px solid rgba(80,180,120,.25) !important;
        }}
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{
            border-radius: 12px !important;
            border-color: var(--lav-line) !important;
            background: var(--white) !important;
            color: var(--ink) !important;
            font-family: inherit !important;
        }}
        label, .stSelectbox label, .stTextInput label, .stTextArea label {{
            font-size: 12px !important;
            font-weight: 700 !important;
            color: var(--mid) !important;
        }}
        [data-testid="stFileUploader"] section {{
            border: 1px dashed var(--lav-line) !important;
            border-radius: 14px !important;
            background: var(--surface) !important;
        }}
        div[data-testid="stExpander"], div[data-testid="stAlert"] {{
            border: 1px solid var(--lav-line) !important;
            border-radius: 14px !important;
            background: var(--white) !important;
            color: var(--ink) !important;
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
        .bandabi-reward-modal {{
            background: var(--white);
            border: 1px solid var(--lav-line);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 24px 64px rgba(109,40,217,.14);
            margin-bottom: 12px;
        }}
        .bandabi-reward-icon {{
            width: 52px; height: 52px; border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            background: var(--lav-dim); border: 1px solid var(--lav-line);
            color: var(--accent); font-size: 22px;
        }}
        .bandabi-toast {{
            position: sticky; top: 8px; z-index: 50;
            text-align: center; font-weight: 700; font-size: 13px;
            padding: 13px 18px; border-radius: 14px;
            background: var(--white); border: 1px solid var(--lav-line);
            box-shadow: 0 8px 32px rgba(109,40,217,.12);
            margin-bottom: 12px;
        }}
        .bandabi-route-map {{
            border-radius: 18px; overflow: hidden;
            border: 1px solid var(--lav-line);
            background: var(--surface); padding: 8px;
        }}
        .bandabi-route-line {{ stroke-dasharray: 14 10; animation: bandabiDash 1.3s linear infinite; }}
        @keyframes bandabiDash {{ to {{ stroke-dashoffset: -48; }} }}
        .bandabi-icon-chip {{
            width: 44px; height: 44px; border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0; font-size: 18px;
        }}
        .bandabi-icon-chip.warn {{ background: rgba(120,104,160,.15); color: var(--accent); }}
        .bandabi-icon-chip.ok {{ background: rgba(74,45,122,.12); color: var(--accent); }}
        .bandabi-start-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 8px;
        }}
        div[data-testid="stDialog"] > div {{
            border-radius: 20px !important;
            border: 1px solid var(--lav-line) !important;
            background: var(--white) !important;
        }}
        body.high-contrast-active .stApp {{ background: #000 !important; }}
        body.high-contrast-active .bandabi-glass,
        body.high-contrast-active .bandabi-soft,
        body.high-contrast-active .bandabi-toss-card,
        body.high-contrast-active .bandabi-app-header,
        body.high-contrast-active .bandabi-tab-shell,
        body.high-contrast-active .vandabi-box,
        body.high-contrast-active .bandabi-reward-modal,
        body.high-contrast-active .bandabi-toast {{
            background: #000 !important;
            color: #ffff00 !important;
            border-color: #ffff00 !important;
            box-shadow: none !important;
        }}
        body.high-contrast-active .bandabi-mid,
        body.high-contrast-active .bandabi-tiny,
        body.high-contrast-active .stCaption,
        body.high-contrast-active label,
        body.high-contrast-active h1,
        body.high-contrast-active h2,
        body.high-contrast-active h3,
        body.high-contrast-active p,
        body.high-contrast-active span {{ color: #ffff00 !important; }}
        body.high-contrast-active div.stButton > button[kind="primary"],
        body.high-contrast-active .bandabi-flow-step.active,
        body.high-contrast-active .bandabi-tab-shell div.stButton > button[kind="primary"] {{
            background: #ffff00 !important;
            color: #000 !important;
        }}
        body.high-contrast-active div.stButton > button {{
            background: #000 !important;
            color: #ffff00 !important;
            border-color: #ffff00 !important;
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
