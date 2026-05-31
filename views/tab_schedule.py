"""Tab 2 — personal schedule recommendation (UI mock)."""

from __future__ import annotations

import streamlit as st

from modules.safety import get_disclaimer, sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


MOCK_SLOTS = [
    {
        "title": s("화요일 10:00"),
        "meta": s("수중 생활체육 · 이동지원 연계 가능성 높음"),
        "tags": [s("버디 후보 2명"), s("4명 소그룹")],
        "score": 92,
    },
    {
        "title": s("목요일 10:30"),
        "meta": s("저강도 GX · 같은 센터 이용자 다수"),
        "tags": [s("버디 후보 1명"), s("6명 소그룹")],
        "score": 86,
    },
    {
        "title": s("수요일 14:00"),
        "meta": s("오후 시간대 · 이동지원 대기 가능(참고)"),
        "tags": [s("이동지원 우선"), s("지도자 여유")],
        "score": 79,
    },
]


def _run_schedule_optimize() -> None:
    st.session_state.schedule_slots = MOCK_SLOTS
    st.session_state.toast_message = s(
        "가장 추천하는 시간은 화요일 10:00입니다. 이동지원 연계 가능성이 높고, 같은 센터 버디 후보가 있습니다."
    )


def render_tab_schedule() -> None:
    st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
    head_l, head_r = st.columns([2.2, 1])
    with head_l:
        st.markdown(f'<p class="bandabi-tiny">{s("Personal Schedule AI")}</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="bandabi-hero-title" style="font-size:1.75rem;">{s("내 운동 일정 추천")}</div>')
        st.markdown(
            f'<p class="bandabi-mid" style="font-size:13px;margin-top:8px;">{s(get_disclaimer("sports"))}</p>',
            unsafe_allow_html=True,
        )
    with head_r:
        if st.button(s("⚡ 가능한 시간 찾기"), type="primary", use_container_width=True, key="btn_schedule_find"):
            _run_schedule_optimize()
            st.rerun()

    pref_col, result_col = st.columns([1, 1.4])
    with pref_col:
        st.markdown('<div class="bandabi-soft" style="margin-top:8px;">', unsafe_allow_html=True)
        st.markdown(f"**{s('선호 조건')}**")
        st.selectbox(s("선호 요일"), [s("화·목 중심"), s("월·수 중심"), s("주말 가능")], key="schedule_day")
        st.selectbox(
            s("선호 시간대"),
            [s("오전 10시 전후"), s("오후 2시 전후"), s("오후 4시 전후")],
            key="schedule_time",
        )
        st.session_state.schedule_mobility_first = st.checkbox(
            s("이동지원 우선"), value=bool(st.session_state.get("schedule_mobility_first", True))
        )
        st.session_state.schedule_buddy_first = st.checkbox(
            s("버디 후보 우선"), value=bool(st.session_state.get("schedule_buddy_first", True))
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f'<div class="bandabi-soft" style="margin-top:10px;font-size:12px;line-height:1.7;">'
            f'<b>{s("추천 기준")}</b><br/>'
            f'1. {s("지도자 가능 시간과 프로그램 정원")}<br/>'
            f'2. {s("이동지원 연계 가능성과 시간대 혼잡도")}<br/>'
            f'3. {s("같은 센터·시간대 버디 후보 여부")}'
            f"</div>",
            unsafe_allow_html=True,
        )

    with result_col:
        slots = st.session_state.get("schedule_slots") or []
        if not slots:
            st.markdown(
                f'<div class="bandabi-soft" style="text-align:center;padding:36px 16px;margin-top:8px;">'
                f'<i class="fa-solid fa-calendar-plus" style="font-size:2rem;color:var(--mid);" aria-hidden="true"></i>'
                f'<p style="font-weight:800;margin-top:12px;">{s("가능한 시간 찾기를 누르면 추천 시간이 표시됩니다")}</p>'
                f'<p class="bandabi-mid" style="font-size:12px;margin-top:6px;">{s("강습·이동지원·버디 후보를 함께 계산합니다.")}</p>'
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            for idx, slot in enumerate(slots):
                tags = "".join(f'<span class="bandabi-badge">{t}</span> ' for t in slot["tags"])
                st.markdown(
                    f"""
                    <div class="bandabi-toss-card">
                      <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
                        <div>
                          <p class="bandabi-tiny">{s("추천 시간")} #{idx + 1}</p>
                          <p style="font-size:1.35rem;font-weight:900;margin:8px 0 4px;">{slot["title"]}</p>
                          <p class="bandabi-mid" style="font-size:12px;">{slot["meta"]}</p>
                          <div style="margin-top:10px;">{tags}</div>
                        </div>
                        <span class="bandabi-badge accent">{slot["score"]}{s("점")}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="bandabi-soft" style="margin-top:10px;">'
                f'{s("가장 추천하는 시간은")} <b>{s("화요일 10:00")}</b>{s("입니다. 이동지원 연계 가능성이 높고, 같은 센터를 이용하는 버디 후보가 있습니다.")}'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown('<div class="bandabi-btn-confirm">', unsafe_allow_html=True)
            if st.button(s("이 시간으로 예약 이어가기"), type="primary", use_container_width=True, key="btn_schedule_book"):
                st.session_state.toast_message = s(
                    "예약 이어가기 요청이 등록되었습니다. 운영기관 검토 후 확정됩니다(데모)."
                )
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
