from __future__ import annotations

import streamlit as st

from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import (
    inject_global_styles,
    render_app_header,
    render_disclaimer_box,
    render_info_card,
    render_metric_card,
    render_page_footer_note,
    render_section_header,
    render_status_badge,
    render_warning_box,
)
from modules.vision import analyze_accessibility_image, mask_notice, vision_status


st.set_page_config(page_title="AI 비전검증", page_icon="♿", layout="wide")
inject_global_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


def display_analysis_source(source: object) -> str:
    value = str(source or "demo_fallback")
    if value == "vision_model":
        return "AI 모델 응답"
    if value in {"demo_fallback", "missing_key"}:
        return "시연용 대체 응답"
    return "AI 임시 검토"


REPORT_TYPES = ["경사로 불편", "보행 장애물", "안내표지 부족", "장애인 화장실 접근성", "기타"]
REQUIRED_NOTICE = "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아닙니다. 관리자 검증, 개인정보 마스킹, 담당 공무원 확인 후 공식 접수 절차로 전환될 수 있습니다."


render_app_header("AI 비전검증", "이미지 업로드, 임시 분석 결과, 관리자 확인 안내를 분리해 표시합니다.", "B2G")
render_disclaimer_box(get_disclaimer("vision"))
render_disclaimer_box(REQUIRED_NOTICE)

status = vision_status()
status_cols = st.columns(3)
with status_cols[0]:
    render_metric_card("Vision 설정", s(str(status["data_status"])), "optional", "purple")
with status_cols[1]:
    render_metric_card("관리자 확인", "필요", "review", "warning")
with status_cols[2]:
    render_metric_card("개인정보 마스킹", "필요 여부 점검", "privacy", "info")

render_section_header("UPLOAD", "이미지 업로드 영역", "이미지 파일은 분석 요청에만 사용하며 저장하지 않습니다.")
with st.form("vision_form"):
    report_type = st.selectbox(s("제보 유형"), [s(item) for item in REPORT_TYPES])
    location = st.text_input(s("위치"), placeholder=s("예: 김포반다비체육센터 출입구 인근"))
    description = st.text_area(s("설명"), placeholder=s("불편 사항과 확인이 필요한 지점을 입력"))
    uploaded = st.file_uploader(s("이미지 업로드"), type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button(s("AI 임시 검토 실행"))

if uploaded is not None:
    st.image(uploaded, caption=s("업로드 이미지 미리보기"), width="stretch")

if submitted:
    image_bytes = uploaded.getvalue() if uploaded is not None else None
    result = analyze_accessibility_image(image_bytes, report_type, f"{location}\n{description}")
    st.session_state["vision_result"] = result

saved = st.session_state.get("vision_result")
if saved:
    render_section_header("RESULT", "AI 임시 검토 결과", "공식 증거가 아닌 위험 요소 후보와 확인 항목입니다.")
    result_cols = st.columns(3)
    with result_cols[0]:
        render_metric_card("위험 요소 후보", s(str(saved.get("risk_level", "확인 필요"))), "temporary", "warning")
    with result_cols[1]:
        render_metric_card("관리자 검토", "필요" if saved.get("review_required") else "권장", "review", "purple")
    with result_cols[2]:
        render_metric_card("분석 소스", s(display_analysis_source(saved.get("source"))), "AI 임시 검토", "muted")

    for item in saved.get("detected_items", []):
        render_info_card("검출 후보", s(str(item)), status="info")

    render_warning_box(s(str(saved.get("recommended_next_step", "관리자 검증 후 담당 부서 확인 자료로 정리"))))
    render_warning_box(s(str(saved.get("mask_notice", mask_notice()))))
    render_disclaimer_box(REQUIRED_NOTICE)
    render_status_badge("AI 임시 검토 결과", "warning")
else:
    render_warning_box("이미지, 제보 유형, 위치 설명을 입력한 뒤 AI 임시 검토를 실행하세요.")

render_page_footer_note()
