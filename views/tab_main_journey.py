"""Tab 1 — user journey: start → route → care → class → report → guardian."""

from __future__ import annotations

import streamlit as st

from components.confirm_dialog import open_confirm, process_pending_confirm
from components.flow_steps import render_flow_steps
from components.route_engine import (
    CENTER_OPTIONS,
    DISABILITY_MAP,
    data_status_badge,
    run_route_analysis,
    s,
)
from modules.rag_bm25 import answer_with_rag
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import render_disclaimer_box


INSTRUCTORS = [
    {
        "name": "박강훈",
        "meta": "수중 생활체육 · 휠체어 이용 또는 보행 보조 필요 이용자 지도 경험",
        "tags": ["수중 생활체육", "화·목 10시", "4명 소그룹"],
    },
    {
        "name": "이서연",
        "meta": "저강도 생활체육 · 음성 안내 동선 경험",
        "tags": ["GX", "월·수 14시", "6명 소그룹"],
    },
]


def _disclaimer_mobility() -> None:
    render_disclaimer_box(s(get_disclaimer("mobility")))


def _disclaimer_sports() -> None:
    render_disclaimer_box(
        s(
            "본 리포트는 의료 진단, 치료, 재활치료 또는 의학적 판단을 대체하지 않습니다. "
            "생활체육 참여를 돕기 위한 참고 정보이며, 운동 강도 변경은 지도자 확인 후 진행해야 합니다."
        )
    )
    render_disclaimer_box(s(get_disclaimer("sports")))


def _start_analysis(disability_key: str, origin: str, center_key: str) -> None:
    support = DISABILITY_MAP.get(disability_key, DISABILITY_MAP["physical"])
    destination = CENTER_OPTIONS.get(center_key, CENTER_OPTIONS["gimpo"])
    inputs = {
        "origin": origin,
        "destination": destination,
        "disability_key": disability_key,
        "accessibility_support_type": support,
        "mobility_support_needed": disability_key in {"physical", "developmental", "senior"},
        "companion_needed": disability_key == "developmental",
        "public_transport_available": True,
        "weather_enabled": True,
    }
    st.session_state.journey["origin"] = origin
    st.session_state.journey["destination"] = destination
    st.session_state.journey["support_type"] = support
    st.session_state.main_step = "route_loading"
    st.session_state.route_analyzing = True
    try:
        st.session_state.route_analysis_result = run_route_analysis(inputs)
    except Exception:
        st.session_state.route_analysis_result = run_route_analysis(
            {**inputs, "origin": origin or "김포 구래역 1번 출구", "destination": destination}
        )
    st.session_state.main_step = "route"
    st.session_state.route_analyzing = False


def render_start() -> None:
    _disclaimer_mobility()
    name = st.session_state.get("user_name") or "000"
    st.markdown(f'<p class="bandabi-tiny">{s("Start")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s(f'반갑습니다, {name}님 :)')}")
    st.markdown(f'<p class="bandabi-mid">{s("오늘 운동, 갈 수 있는 경로부터 확인해요.")}</p>', unsafe_allow_html=True)

    col_form, col_cards = st.columns([1.2, 1])
    with col_form:
        disability = st.selectbox(
            s("접근성 지원 필요 유형"),
            options=list(DISABILITY_MAP.keys()),
            format_func=lambda k: s(
                {
                    "physical": "휠체어 이용 또는 보행 보조 필요",
                    "visual": "음성 안내 또는 유도동선 필요",
                    "developmental": "보호자 동행 또는 단계별 안내 필요",
                    "senior": "일부 도움 필요 또는 저강도 안내 선호",
                }[k]
            ),
            key="start_disability",
        )
        origin = st.text_input(s("출발지"), value="김포 구래역 1번 출구", key="start_origin")
        center = st.selectbox(
            s("목적지"),
            options=list(CENTER_OPTIONS.keys()),
            format_func=lambda k: s(CENTER_OPTIONS[k]),
            key="start_center",
        )
    with col_cards:
        for label in (s("보호자 알림"), s("버디 매칭"), s("강습 추천"), s("리포트 수신")):
            st.markdown(f'<div class="bandabi-soft" style="text-align:center;font-weight:700;margin-bottom:8px;">{label}</div>', unsafe_allow_html=True)
        if st.button(s("⚡ AI 추천 시작"), type="primary", use_container_width=True, key="btn_ai_start"):
            _start_analysis(disability, origin, center)
            st.rerun()

    st.caption(
        s(
            "본 AI 결과는 이용자 편의를 위한 추천 정보이며, "
            "최종 이용 여부와 운영 확정은 이용자 및 운영기관이 결정합니다."
        )
    )


def render_route() -> None:
    _disclaimer_mobility()
    result = st.session_state.get("route_analysis_result")
    if not result:
        st.warning(s("경로 분석 결과가 없습니다. 시작 화면에서 다시 분석해 주세요."))
        if st.button(s("시작 화면으로"), key="route_back_empty"):
            st.session_state.main_step = "start"
            st.rerun()
        return

    if st.session_state.get("route_analyzing"):
        with st.spinner(s("이동 가능성을 계산하고 있어요")):
            pass

    st.markdown(f'<p class="bandabi-tiny">{s("MAIN 01")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('AI 기반 도착 가능성 — 경로분석')}")
    st.caption(s("공공데이터와 입력 정보를 기반으로 한 예측값이며, 실제 교통상황·시설 운영상황에 따라 달라질 수 있습니다."))

    inputs = result["inputs"]
    score = result["score_result"]
    metrics = result["travel_metrics"]
    origin = result["origin_coord"]
    dest = result["destination_coord"]

    st.markdown(
        f"**{s(f'{inputs['origin']} → {inputs['destination']}')}**"
    )

    for label, coord in ((s("출발지 좌표"), origin), (s("목적지 좌표"), dest)):
        badge_text, badge_cls = data_status_badge(coord.get("data_status", "fallback"))
        st.markdown(
            f'{label}: <span class="bandabi-badge {badge_cls}">{badge_text}</span>',
            unsafe_allow_html=True,
        )

    route_badge, route_cls = data_status_badge(metrics["route_status"])
    arrival_badge, arrival_cls = data_status_badge(metrics["arrival_status"])
    st.markdown(
        f'{s("버스 노선")}: <span class="bandabi-badge {route_cls}">{route_badge}</span> '
        f'{s("버스 도착")}: <span class="bandabi-badge {arrival_cls}">{arrival_badge}</span>',
        unsafe_allow_html=True,
    )
    if metrics["arrival_status"] == "real_api_no_data":
        st.markdown(
            f'<span class="bandabi-badge no-data">{s("no_data")}</span>',
            unsafe_allow_html=True,
        )

    weather_status = result["weather_result"].get("status", "fallback")
    w_badge, w_cls = data_status_badge(weather_status)
    st.markdown(
        f'{s("날씨 보정")}: <span class="bandabi-badge {w_cls}">{w_badge}</span> · {s(result["weather_text"])}',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    precise = metrics.get("precise", False)
    metric_badge = s(metrics.get("badge", "예상(참고용)"))
    with c1:
        st.markdown(f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{s("총 시간")}</div><div style="font-weight:800;">{s(metrics["total_time"])}</div><span class="bandabi-badge warn">{metric_badge}</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{s("도보")}</div><div style="font-weight:800;">{s(metrics["walk"])}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{s("환승")}</div><div style="font-weight:800;">{s(metrics["transfer"])}</div></div>', unsafe_allow_html=True)
    with c4:
        score_val = int(score.get("score", 0))
        st.markdown(
            f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{s("이동 가능성")}</div>'
            f'<div style="font-weight:800;">{score_val}% · {s(result["grade_label"])}</div></div>',
            unsafe_allow_html=True,
        )
    if not precise:
        st.caption(s("총시간·도보·환승은 실API 수치가 없어 정성 표현 또는 확인 필요로 표시합니다."))

    st.markdown(f"**{s('AI 종합 소견')}**: {s(result['grade_label'])}")
    st.write(s(result["explanation"]))
    if score.get("recommended_actions"):
        st.markdown(f"- {s(score['recommended_actions'][0])}")

    bus_route = result.get("bus_route", {})
    if bus_route.get("items"):
        with st.expander(s("버스 노선 상세(참고)")):
            st.json(bus_route.get("items")[:3])

    st.markdown(
        f'<div class="bandabi-glass"><b>{s("예약·이동·동행 플랜이 준비됐어요")}</b><br/>'
        f'<span class="bandabi-mid">{s("확정하면 버디 후보와 강습 추천으로 이어집니다. 실제 예약·배차는 운영기관 검토 후 진행됩니다.")}</span></div>',
        unsafe_allow_html=True,
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(s("다시하기"), key="route_restart"):
            st.session_state.main_step = "start"
            st.session_state.route_analysis_result = None
            st.rerun()
    with b2:
        if st.button(s("재계산"), key="route_recalc"):
            _start_analysis(inputs.get("disability_key", "physical"), inputs["origin"], "gimpo")
            st.session_state.toast_message = s("경로 참고 분석을 다시 실행했습니다.")
            st.rerun()
    with b3:
        if st.button(s("확정하기"), type="primary", key="route_confirm"):
            open_confirm(
                title=s("운영 확정 요청이 등록되었습니다."),
                subtitle=s("예약·이동·동행 플랜이 다음 단계로 연결됩니다."),
                message=s(
                    "운영 확정 요청이 등록되었습니다. 참여 인센티브 500BT가 적립됩니다. "
                    "실제 예약·배차·이동지원 실행은 운영기관 검토 후 진행됩니다."
                ),
                bt_delta=500,
                next_step="care",
                on_confirm_key="route",
            )
            st.rerun()


def render_care() -> None:
    _disclaimer_mobility()
    st.markdown(f'<p class="bandabi-tiny">{s("MAIN 02")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('인증 기반 — 버디 후보 추천')}")
    st.caption(s("혼자 이동하는 부담을 줄이고, 버디와 함께 체육 시설을 이용합니다."))

    cols = st.columns(3)
    cards = [
        (s("첫 방문 버디"), s("김지오 회원"), s("같은 시간대, 같은 센터 이용")),
        (s("센터 도우미"), s("500m 전"), s("대기(참고)")),
        (s("보호자 모드"), s("출석 알림 공유"), s("확정 전 연락처 비공개")),
    ]
    for col, (title, main, sub) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="bandabi-glass"><div class="bandabi-tiny">{title}</div>'
                f'<div style="font-size:1.4rem;font-weight:900;margin:12px 0;">{main}</div>'
                f'<div class="bandabi-mid" style="font-size:12px;">{sub}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="bandabi-soft">{s("버디 후보 추천은 기관 인증 이용자에 한해 제공되며, 상호 동의 및 관리자 확인 후 연결됩니다. 실명·연락처는 확정 전 비공개이며 신고/차단/긴급 연락 기능을 포함합니다.")}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button(s("건너뛰기"), key="care_skip"):
            st.session_state.buddy_skipped = True
            st.session_state.journey["buddy"] = s("버디 매칭 건너뜀")
            st.session_state.main_step = "class"
            st.rerun()
    with c2:
        if st.button(s("확정하기"), type="primary", key="care_confirm"):
            open_confirm(
                title=s("버디 매칭 확정 요청이 등록되었습니다."),
                subtitle=s("상호 동의와 관리자 확인 후 연결됩니다."),
                message=s(
                    "첫 방문 버디 후보 연결 요청이 등록되었습니다. "
                    "실명·연락처는 확정 전 비공개로 유지되며, 관리자 확인 후 다음 단계로 연결됩니다."
                ),
                bt_delta=0,
                next_step="class",
                on_confirm_key="buddy",
            )
            st.rerun()


def render_class() -> None:
    _disclaimer_mobility()
    idx = int(st.session_state.get("instructor_index", 0)) % len(INSTRUCTORS)
    data = INSTRUCTORS[idx]
    support = st.session_state.journey.get("support_type", DISABILITY_MAP["physical"])

    st.markdown(f'<p class="bandabi-tiny">{s("Program AI")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('인증 기반 — 강습·지도자 추천')}")
    st.caption(s("접근성 지원 필요 유형, 운동 목적, 시간, 지도자 전문성을 함께 고려합니다."))

    tags = "".join(f'<span class="bandabi-badge">{s(t)}</span>' for t in data["tags"])
    st.markdown(
        f'<div class="bandabi-glass" style="max-width:420px;margin:0 auto;">'
        f'<div class="bandabi-tiny">{s("추천 지도자")}</div>'
        f'<div style="font-size:2rem;font-weight:900;margin:16px 0;">{s(data["name"])} <span class="bandabi-mid" style="font-size:1rem;">{s("지도자")}</span></div>'
        f'<div class="bandabi-mid">{s(data["meta"])} · {s(support)}</div>'
        f'<div style="margin-top:16px;">{tags}</div></div>',
        unsafe_allow_html=True,
    )
    st.caption(s("본 추천은 생활체육 참여 지원을 위한 참고자료이며, 최종 참여 여부는 이용자와 운영기관이 결정합니다."))

    c1, c2 = st.columns(2)
    with c1:
        if st.button(s("다른 지도자"), key="class_switch"):
            st.session_state.instructor_index = idx + 1
            st.rerun()
    with c2:
        if st.button(s("확정하기"), type="primary", key="class_confirm"):
            st.session_state.journey["instructor"] = s(data["name"])
            open_confirm(
                title=s("강습·지도자 추천이 확정되었습니다."),
                subtitle=s("운동 참여 결과를 리포트 화면에서 확인합니다."),
                message=s(
                    "추천 지도자와 강습 선택이 등록되었습니다. "
                    "본 내용은 생활체육 참여 지원을 위한 참고자료이며, 최종 운영 확정은 이용자와 운영기관 확인 후 진행됩니다."
                ),
                bt_delta=0,
                next_step="report",
                on_confirm_key="class",
            )
            st.rerun()


def render_report() -> None:
    _disclaimer_sports()
    st.markdown(f'<p class="bandabi-tiny">{s("MAIN 03")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('AI 생활체육 리포트')}")
    st.caption(s("운동 후 변화와 다음 참여 가능성을 쉽게 확인해요."))

    demo_cols = st.columns(4)
    demo = [
        (s("오늘 출석"), s("출석 완료(데모)")),
        (s("운동 성취도"), s("84점(데모)")),
        (s("지속참여 점수"), s("91점(데모)")),
        (s("참여 인센티브"), s("+300 BT(데모)")),
    ]
    for col, (label, value) in zip(demo_cols, demo):
        with col:
            st.markdown(
                f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{label}</div>'
                f'<div style="font-weight:800;">{value}</div><span class="bandabi-badge warn">{s("데모")}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown(f"**{s('수행 범위 변화(데모)')}**: {s('78° → 82° · 지난 회차 대비 소폭 개선(참고)')}")

    support = st.session_state.journey.get("support_type", "")
    program = st.session_state.journey.get("instructor", "박강훈")
    rag_query = s(f"다음 생활체육 참여 가이드 — 프로그램 {program}, 접근성 지원 {support}")
    try:
        rag = answer_with_rag(rag_query, top_k=5, docs_dir="docs")
    except Exception:
        rag = {"answer": s("문서 기반 가이드를 불러오지 못했습니다. 운영기관 안내를 확인해 주세요."), "data_status": "fallback", "source": "fallback"}

    rag_badge = s(rag.get("data_status", "unknown"))
    st.markdown(f"**{s('다음 생활체육 가이드')}** · `{rag_badge}` · source={s(str(rag.get('source', 'fallback')))}")
    st.markdown(f'<div class="bandabi-soft">{s(rag.get("answer", ""))}</div>', unsafe_allow_html=True)

    st.caption(s("지속참여 루프: 다음 예약 · 이동지원 연계 · 버디 동행 · 보호자 알림(모두 운영기관 검토 필요)"))

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(s("다음 강습 추천 보기"), key="report_back_class"):
            st.session_state.main_step = "class"
            st.rerun()
    with c2:
        if st.button(s("리포트 저장 및 공유"), key="report_save"):
            st.session_state.report_saved = True
            st.session_state.main_step = "guardian"
            st.rerun()
    with c3:
        if st.button(s("참여 인센티브 확인"), type="primary", key="report_bt"):
            st.session_state.bt_balance = int(st.session_state.get("bt_balance", 0)) + 300
            st.session_state.toast_message = s("운동 완료 참여 인센티브 300BT가 적립되었습니다(비현금).")
            st.rerun()


def render_guardian() -> None:
    _disclaimer_sports()
    journey = st.session_state.journey
    st.markdown(f'<p class="bandabi-tiny">{s("Guardian Share")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('보호자 공유용 요약')}")
    st.caption(s("출석, 이동, 운동 참여 결과를 간단히 공유합니다. 민감한 진단명·상세 건강정보는 포함하지 않습니다."))

    rows = [
        (s("출석"), s("완료(데모)")),
        (s("이동"), journey.get("route_plan", s("이동지원 연계 요청 등록(검토 중)"))),
        (s("버디"), journey.get("buddy", s("미연결"))),
        (s("운동"), s(f"{journey.get('instructor', '지도자')} 프로그램 참여(데모)")),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, rows):
        with col:
            st.markdown(
                f'<div class="bandabi-soft"><div class="bandabi-mid" style="font-size:11px;">{label}</div>'
                f'<div style="font-weight:800;">{value}</div></div>',
                unsafe_allow_html=True,
            )

    dest = journey.get("destination", s("김포 반다비체육센터"))
    summary = s(
        f"오늘 {dest} 생활체육 프로그램 참여 흐름이 진행되었습니다. "
        f"이동지원 연계 요청과 센터 도착 확인은 운영기관 검토 중이며, "
        f"다음 참여를 위한 생활체육 가이드가 생성되었습니다."
    )
    st.markdown(f'<div class="bandabi-glass">{summary}</div>', unsafe_allow_html=True)
    st.caption(s("보호자 공유는 이용자 동의 범위 안에서만 제공됩니다. 실제 외부 전송은 연결하지 않았습니다."))

    c1, c2 = st.columns(2)
    with c1:
        if st.button(s("리포트 화면으로"), key="guardian_back"):
            st.session_state.main_step = "report"
            st.rerun()
    with c2:
        if st.button(s("보호자에게 공유"), type="primary", key="guardian_share"):
            open_confirm(
                title=s("보호자 공유 메시지 생성"),
                subtitle=s("실제 외부 전송은 하지 않습니다."),
                message=s("보호자 공유용 요약 메시지가 생성되었습니다. 운영기관 확인 후 실제 전송 채널을 연결할 수 있습니다."),
                bt_delta=0,
                next_step="guardian",
                on_confirm_key="guardian",
            )
            st.session_state.toast_message = s("보호자 공유 완료 메시지가 생성되었습니다. 실제 외부 전송은 연결하지 않았습니다.")
            st.rerun()


def render_tab_main() -> None:
    process_pending_confirm()

    step = st.session_state.get("main_step", "start")
    render_flow_steps(step if step != "route_loading" else "route")

    if step == "start":
        render_start()
    elif step in {"route_loading", "route"}:
        render_route()
    elif step == "care":
        render_care()
    elif step == "class":
        render_class()
    elif step == "report":
        render_report()
    elif step == "guardian":
        render_guardian()
    else:
        render_start()
