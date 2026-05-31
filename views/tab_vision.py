"""Tab 3 — AI vision accessibility assist."""

from __future__ import annotations

import json

import streamlit as st

from components.mock_ui import build_sendgrid_payload_preview, mock_vision_result
from components.vision_ui import (
    DEMO_IMAGE_PNG,
    OFFICIAL_NOTICE,
    REPORT_TYPES,
    demo_scan_svg_markup,
    is_model_output,
    qualitative_grade,
    result_source_badge,
    risk_icon,
)
from modules.safety import VISION_DISCLAIMER, get_disclaimer, sanitize_public_claims
from modules.vision import analyze_accessibility_image, mask_notice, vision_status
from modules.ui_components import render_disclaimer_box


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def _run_analysis(*, image_bytes: bytes | None, report_type: str, description: str) -> None:
    if image_bytes is None and not description.strip():
        result = mock_vision_result(location="", description=description)
    else:
        try:
            result = analyze_accessibility_image(image_bytes, report_type, description)
        except Exception:
            result = mock_vision_result(location=description.split("\n")[0], description=description)
    st.session_state.vision_result = result
    st.session_state.vision_last_report_type = report_type
    st.session_state.vision_scanning = False


def _render_gov_draft_section() -> None:
    st.markdown('<div class="bandabi-glass" style="margin-top:16px;">', unsafe_allow_html=True)
    st.markdown(f'<p class="bandabi-tiny">{s("Official Notice Draft")}</p>', unsafe_allow_html=True)
    st.markdown(f"### {s('접근성 개선 검토용 공문·이메일 초안')}")
    st.caption(s("미리보기 내용을 수정한 뒤, 추후 SendGrid API와 연결할 수 있는 형태로 저장합니다. 실제 발송은 하지 않습니다."))

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.gov_to_email = st.text_input(
            s("수신자 이메일"), value=st.session_state.get("gov_to_email", "facility@gimpo.go.kr"), key="gov_to"
        )
        st.session_state.gov_from_name = st.text_input(
            s("발신자 이름"), value=st.session_state.get("gov_from_name", "김포 반다비 AI 운영팀"), key="gov_from_name"
        )
    with c2:
        st.session_state.gov_from_email = st.text_input(
            s("발신자 이메일"), value=st.session_state.get("gov_from_email", "no-reply@bandabi-ai.kr"), key="gov_from_email"
        )
        st.session_state.gov_subject = st.text_input(
            s("공문 제목"),
            value=st.session_state.get("gov_subject", "김포 반다비체육센터 접근성 위험 요소 개선 검토 요청"),
            key="gov_subject",
        )

    st.session_state.gov_body = st.text_area(
        s("공문/이메일 본문"),
        value=st.session_state.get("gov_body", ""),
        height=220,
        key="gov_body",
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button(s("Payload 미리보기 갱신"), use_container_width=True, key="gov_refresh_payload"):
            st.session_state.sendgrid_payload_preview = build_sendgrid_payload_preview(
                to_email=st.session_state.gov_to_email,
                from_email=st.session_state.gov_from_email,
                from_name=st.session_state.gov_from_name,
                subject=st.session_state.gov_subject,
                body=st.session_state.gov_body,
            )
            st.rerun()
    with b2:
        if st.button(s("발송 준비(미실행)"), type="primary", use_container_width=True, key="gov_prepare"):
            st.session_state.sendgrid_payload_preview = build_sendgrid_payload_preview(
                to_email=st.session_state.gov_to_email,
                from_email=st.session_state.gov_from_email,
                from_name=st.session_state.gov_from_name,
                subject=st.session_state.gov_subject,
                body=st.session_state.gov_body,
            )
            st.session_state.toast_message = s(
                "SendGrid 발송용 payload가 준비되었습니다. 실제 발송 API는 추후 연결하면 됩니다."
            )
            st.rerun()

    payload = st.session_state.get("sendgrid_payload_preview")
    if payload:
        st.markdown(f"**{s('SendGrid 연동용 payload 미리보기')}**")
        st.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json")
    st.caption(s("※ 본 문서는 관리자 검토용 초안이며, 실제 이메일 발송은 SendGrid API 키와 인증된 발신자 설정을 연결한 뒤 가능합니다."))
    st.markdown("</div>", unsafe_allow_html=True)


def _render_risk_card(result: dict) -> None:
    grade, badge_cls = qualitative_grade(result)
    source_badge = s(result_source_badge(result))
    icon = risk_icon(grade)

    st.markdown(
        f"""
        <div class="bandabi-toss-card">
          <div style="display:flex;gap:14px;align-items:flex-start;">
            <div class="bandabi-icon-chip {badge_cls}" aria-hidden="true">{icon}</div>
            <div style="flex:1;">
              <span class="bandabi-badge {badge_cls}">{s("등급")}: {s(grade)}</span>
              <span class="bandabi-badge warn">{source_badge}</span>
              <div style="font-size:1.15rem;font-weight:900;margin-top:8px;">{s(str(result.get("risk_level", "확인 필요")))}</div>
              <p class="bandabi-mid" style="font-size:13px;margin-top:8px;line-height:1.6;">
                {s("접근성 점검 보조자료입니다. 공식 판정·행정처분·시설 적합 확정이 아닙니다.")}
              </p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result_panel(result: dict) -> None:
    st.markdown(f"**{s('마스킹·개인정보 고지')}**")
    st.markdown(f'<div class="bandabi-soft">{s(mask_notice())}</div>', unsafe_allow_html=True)
    render_disclaimer_box(s(VISION_DISCLAIMER))
    render_disclaimer_box(s(OFFICIAL_NOTICE))

    _render_risk_card(result)

    st.markdown(f"**{s('검출 후보 · 확인 항목')}**")
    for item in result.get("detected_items", []) or [s("확인 항목 없음")]:
        st.markdown(
            f'<div class="bandabi-soft" style="margin-bottom:8px;">{s(str(item))}</div>',
            unsafe_allow_html=True,
        )

    if result.get("recommended_next_step"):
        st.markdown(
            f'<div class="bandabi-soft">{s(str(result["recommended_next_step"]))}</div>',
            unsafe_allow_html=True,
        )

    if result.get("review_required"):
        st.markdown(
            f'<span class="bandabi-badge warn">{s("운영기관 검토 필요")}</span>',
            unsafe_allow_html=True,
        )
    if result.get("privacy_masking_required"):
        st.markdown(
            f'<span class="bandabi-badge accent">{s("개인정보 마스킹 점검 필요")}</span>',
            unsafe_allow_html=True,
        )

    reason = str(result.get("reason", "") or "")
    source = str(result.get("source", "") or "")
    if reason or source:
        st.caption(s(f"데이터 상태: source={source or 'unknown'}, reason={reason or 'none'}"))

    if is_model_output(result):
        st.caption(s("AI 모델 출력은 관리자 확인 전 참고자료이며, 신뢰도 % 수치는 모델 응답에 포함된 경우에만 별도 표시합니다."))
    else:
        st.caption(s("데모·대체 응답입니다. 확정형 신뢰도 % 수치를 표시하지 않습니다."))


def render_tab_vision() -> None:
    render_disclaimer_box(s(get_disclaimer("vision")))

    status = vision_status()
    st.markdown(f'<p class="bandabi-tiny">{s("AI Vision")}</p>', unsafe_allow_html=True)
    st.markdown(f"## {s('접근성 점검 보조')}")
    st.caption(s("사진 제보를 위험도 카드로 바꿔 보여줍니다. 결과는 접근성 점검 보조자료이며 공식 판정이 아닙니다."))

    badge = s("실API") if status.get("configured") else s("대체 데이터")
    st.markdown(f'<span class="bandabi-badge warn">{badge}</span>', unsafe_allow_html=True)

    col_input, col_map = st.columns([1.05, 0.95])

    with col_input:
        st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
        report_type = st.selectbox(
            s("점검 유형"),
            options=[s(t) for t in REPORT_TYPES],
            key="vision_report_type",
        )
        location = st.text_input(
            s("위치"),
            value="김포 반다비체육센터 1층 로비",
            key="vision_location",
            placeholder=s("예: 김포반다비체육센터 출입구 인근"),
        )
        description = st.text_area(
            s("설명"),
            key="vision_description",
            placeholder=s("불편 사항과 확인이 필요한 지점을 입력"),
            height=88,
        )
        uploaded = st.file_uploader(
            s("이미지 업로드 (jpg/png)"),
            type=["png", "jpg", "jpeg"],
            key="vision_upload",
        )

        if uploaded is not None:
            st.image(uploaded, caption=s("업로드 이미지 미리보기"), use_container_width=True)

        desc_full = s(f"{location}\n{description}".strip())
        btn_cols = st.columns(2)
        with btn_cols[0]:
            if st.button(s("📷 AI 임시 검토"), type="primary", use_container_width=True, key="vision_analyze"):
                image_bytes = uploaded.getvalue() if uploaded is not None else None
                st.session_state.vision_scanning = True
                _run_analysis(image_bytes=image_bytes, report_type=report_type, description=desc_full)
                st.rerun()
        with btn_cols[1]:
            if st.button(s("데모 이미지로 분석"), use_container_width=True, key="vision_demo_analyze"):
                st.session_state.vision_scanning = True
                _run_analysis(image_bytes=DEMO_IMAGE_PNG, report_type=report_type, description=desc_full)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        result = st.session_state.get("vision_result")
        if result:
            _render_result_panel(result)
        else:
            st.markdown(
                f'<div class="bandabi-soft">{s("스캔 실행 전입니다. AI 분석 결과는 접근성 점검 보조자료이며, 법적 인증·행정처분·시설 적합 판정을 대체하지 않습니다.")}</div>',
                unsafe_allow_html=True,
            )

    with col_map:
        st.markdown('<div class="bandabi-glass">', unsafe_allow_html=True)
        st.markdown(f'<p class="bandabi-tiny">{s("Accessibility Map")}</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="bandabi-hero-title" style="font-size:1.5rem;">{s("접근성 제보 지도 (데모)")}</div>')

        scanning = bool(st.session_state.get("vision_scanning"))
        has_result = bool(st.session_state.get("vision_result"))
        st.markdown(
            demo_scan_svg_markup(scanning=scanning, show_demo_bbox=has_result),
            unsafe_allow_html=True,
        )
        st.caption(s("bbox·스캔라인은 HTML 시안 연출을 참고한 데모 표시이며, 실제 좌표·공식 판정이 아닙니다."))

        demo_cards = [
            (s("점자블록 단절"), s("1층 로비 · 개선 필요 가능성 · 검토 요청 대기"), "warn"),
            (s("접근 가능한 화장실 개선 완료"), s("2층 · 조치 완료 · 운영기관 확인"), "ok"),
        ]
        for title, sub, cls in demo_cards:
            icon = "fa-triangle-exclamation" if cls == "warn" else "fa-circle-check"
            st.markdown(
                f"""
                <div class="bandabi-toss-card" style="margin-bottom:10px;display:flex;gap:12px;align-items:flex-start;">
                  <div class="bandabi-icon-chip {cls}"><i class="fa-solid {icon}" aria-hidden="true"></i></div>
                  <div>
                    <div style="font-weight:800;">{title}</div>
                    <div class="bandabi-mid" style="font-size:12px;margin-top:4px;">{sub}</div>
                    <span class="bandabi-badge {cls}">{s("참고")}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<span class="bandabi-badge warn">{s("데모 카드 · 운영기관 확인 필요")}</span>',
            unsafe_allow_html=True,
        )

        if st.button(s("제보 참여 인센티브(데모)"), key="vision_reward_demo", use_container_width=True):
            st.session_state.toast_message = s(
                "접근성 제보 참여 인센티브 200BT가 적립되었습니다(비현금·데모). 운영기관 검토가 필요합니다."
            )
            st.session_state.bt_balance = int(st.session_state.get("bt_balance", 3500)) + 200
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    _render_gov_draft_section()
