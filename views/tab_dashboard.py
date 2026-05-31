"""Tab 4 — B2G dashboard (UI mock + safe module status)."""

from __future__ import annotations

import streamlit as st

from components.session_state import ROLE_B2G
from modules.api_clients import vworld_status
from modules.config import list_config_status
from modules.data_loader import load_csv_inventory
from modules.emailer import email_status
from modules.rag_bm25 import build_index
from modules.safety import get_disclaimer, sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def _status_badge(label: str, status: str) -> str:
    cls = "ok" if status in {"configured", "enabled", "real_csv", "real_docs", "ready", "enabled_ready"} else "warn"
    if status in {"missing", "missing_config", "disabled", "read_error"}:
        cls = "no-data"
    return f'<span class="bandabi-badge {cls}">{s(label)} · {s(status)}</span>'


def render_tab_dashboard() -> None:
    if st.session_state.get("role") != ROLE_B2G:
        st.warning(s("기관용 대시보드는 관리자 모드에서만 접근할 수 있습니다."))
        return

    st.markdown(f'<p class="bandabi-tiny">{s("B2G Dashboard")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('기관용 대시보드')}")
    st.caption(s(get_disclaimer("general")))

    kpis = [
        (s("예약 대비 출석률"), "94.2%", "fa-user-check", "ok"),
        (s("이동지원 연계 성공"), "88.7%", "fa-van-shuttle", "accent"),
        (s("피어 매칭 성공"), "76.4%", "fa-handshake-angle", "warn"),
        (s("지도자 부족률"), "24%", "fa-person-chalkboard", "warn"),
    ]
    kpi_cols = st.columns(4)
    for col, (label, value, icon, tone) in zip(kpi_cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="bandabi-toss-card">
                  <i class="fa-solid {icon}" style="color:var(--accent);" aria-hidden="true"></i>
                  <p class="bandabi-mid" style="font-size:11px;margin-top:12px;">{label}</p>
                  <p style="font-size:1.6rem;font-weight:900;margin:6px 0 0;">{value}</p>
                  <span class="bandabi-badge {tone}">{s("데모")}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    chart_l, chart_r = st.columns(2)
    with chart_l:
        st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
        st.markdown(f"**{s('접근성 지원 필요 유형별 이용률')}**")
        for label, pct in (
            (s("보행 보조"), "38%"),
            (s("시각·안내"), "22%"),
            (s("발달·동행"), "18%"),
            (s("고령·저강도"), "22%"),
        ):
            st.markdown(f"- {label}: **{pct}**")
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_r:
        st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
        st.markdown(f"**{s('시간대별 혼잡·이동지원 지연')}**")
        for label, note in (
            (s("09:00–11:00"), s("혼잡 · 이동지원 지연 12분(데모)")),
            (s("13:00–15:00"), s("보통 · 지연 5분(데모)")),
            (s("17:00–19:00"), s("피크 · 지연 18분(데모)")),
        ):
            st.markdown(f"- {label}: {note}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="bandabi-glass" style="margin-top:12px;">', unsafe_allow_html=True)
    st.markdown(f"**{s('기관 운영 액션 보드')}**")
    rows = [
        (s("노쇼 공백"), s("수중 생활체육 10:00 슬롯"), s("대기자 2명 삽입 가능"), s("알림 대기")),
        (s("접근성"), s("점자블록 단절"), s("개선 필요 가능성 높음"), s("검토 요청 필요")),
        (s("배차"), s("이동지원 14:00"), s("대체 차량 후보 1대"), s("검토 중")),
    ]
    for kind, content, ai, status in rows:
        st.markdown(
            f'<div class="bandabi-soft" style="margin-bottom:8px;display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between;">'
            f"<span><b>{kind}</b> · {content}</span>"
            f"<span class='bandabi-mid'>{ai}</span>"
            f"<span class='bandabi-badge warn'>{status}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"### {s('공공데이터 · CSV · RAG · API 상태')}")
    st.caption(s("키 값은 표시하지 않습니다. 연결 상태만 확인합니다."))

    vworld = vworld_status()
    email = email_status()
    rag_index = build_index("docs")
    csv_inventory = load_csv_inventory()
    if csv_inventory.empty:
        csv_status = "mock_fallback"
    elif csv_inventory["data_status"].eq("real_csv").any():
        csv_status = "real_csv"
    else:
        csv_status = "mock_fallback"

    status_cols = st.columns(2)
    with status_cols[0]:
        st.markdown('<div class="bandabi-soft">', unsafe_allow_html=True)
        st.markdown(f"**{s('공공데이터 연결')}**")
        st.markdown(_status_badge("VWorld", str(vworld.get("data_status", "missing"))), unsafe_allow_html=True)
        st.markdown(
            _status_badge("기상·공공데이터", str(list_config_status().get("DATA_GO_KR_SERVICE_KEY", "missing"))),
            unsafe_allow_html=True,
        )
        st.markdown(
            _status_badge("VWorld 지오코딩", str(list_config_status().get("VWORLD_API_KEY", "missing"))),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with status_cols[1]:
        st.markdown('<div class="bandabi-soft">', unsafe_allow_html=True)
        st.markdown(f"**{s('CSV / RAG / API')}**")
        st.markdown(_status_badge("CSV", csv_status), unsafe_allow_html=True)
        st.markdown(_status_badge("RAG", str(rag_index.data_status)), unsafe_allow_html=True)
        st.markdown(_status_badge("SendGrid", str(email.get("data_status", "disabled"))), unsafe_allow_html=True)
        st.markdown(
            _status_badge("OpenRouter", str(list_config_status().get("OPENROUTER_API_KEY", "missing"))),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="bandabi-soft" style="margin-top:10px;font-family:monospace;font-size:11px;line-height:1.7;">'
        f"[10:04:01] {s('김포 반다비 운영 데이터 수집 완료(데모)')}<br/>"
        f"[10:04:04] {s('지도자 유휴·이동지원 지연·접근성 제보 통합 분석 대기(데모)')}"
        f"</div>",
        unsafe_allow_html=True,
    )
