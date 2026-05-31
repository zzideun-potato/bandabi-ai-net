from __future__ import annotations

import streamlit as st

from modules.emailer import build_official_draft, can_send_email, email_status, improve_draft_with_llm, send_email_with_sendgrid
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.ui_components import (
    inject_global_styles,
    render_app_header,
    render_disclaimer_box,
    render_info_card,
    render_metric_card,
    render_page_footer_note,
    render_section_header,
    render_warning_box,
)


st.set_page_config(page_title="공문 초안 이메일", page_icon="♿", layout="wide")
inject_global_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


render_app_header("관리자 검증용 공문 초안", "초안 생성 영역과 이메일 발송 안전장치를 분리합니다.", "B2G")
render_disclaimer_box(get_disclaimer("general"))
render_disclaimer_box("담당자 확인 후 공식 절차 전환 가능 여부를 검토합니다. 이 화면은 관리자 검증용 초안 작성 도구입니다.")

email_info = email_status()
cols = st.columns(3)
with cols[0]:
    render_metric_card("SendGrid 상태", s(str(email_info["data_status"])), "기본 비활성 안전장치", "warning" if not email_info["can_send"] else "success")
with cols[1]:
    render_metric_card("발송 활성화", "enabled" if email_info["enabled"] else "disabled", "ENABLE_SENDGRID_SEND", "info")
with cols[2]:
    render_metric_card("발신 이메일", "configured" if email_info["has_sender"] else "missing", "값 미표시", "muted")

render_section_header("DRAFT", "공문 초안 생성", "입력 내용을 바탕으로 관리자 검증용 초안을 생성합니다.")
with st.form("official_draft_form"):
    title = st.text_input(s("제보 제목"), placeholder=s("예: 접근성 확인 요청"))
    body = st.text_area(s("제보 내용"), placeholder=s("검토가 필요한 내용을 입력"))
    location = st.text_input(s("위치"), placeholder=s("예: 김포반다비체육센터 출입구 인근"))
    recipient = st.text_input(s("수신 부서/담당자"), placeholder=s("예: 담당 부서 확인 필요"))
    sender = st.text_input(s("발신자 이메일"), placeholder=s("발신자 이메일을 직접 입력"))
    to_email = st.text_input(s("수신 이메일"), placeholder=s("SendGrid 발송 조건 충족 시에만 필요"))
    submitted = st.form_submit_button(s("공문 초안 생성"))

if submitted:
    draft = build_official_draft(title, body, location, recipient, sender)
    improved = improve_draft_with_llm(draft)
    final_draft = s(str(improved.get("text", draft)))
    st.session_state["official_draft"] = {
        "text": final_draft,
        "title": s(title or "관리자 검증용 공문 초안"),
        "to_email": s(to_email),
        "source": s(str(improved.get("source", "template"))),
    }

saved = st.session_state.get("official_draft")
if saved:
    render_section_header("PREVIEW", "초안 전문 미리보기", "OpenRouter 실패 시 템플릿 초안을 유지합니다.")
    render_metric_card("초안 생성 소스", saved["source"], "OpenRouter optional", "purple")
    st.text_area(s("관리자 검증용 공문 초안"), saved["text"], height=420)

    render_section_header("SEND", "이메일 발송 안전장치", "모든 조건이 충족될 때만 버튼이 활성화됩니다.")
    confirmed = st.checkbox(s("초안 내용을 확인했으며, 관리자 검증용 자료로만 사용합니다."))
    send_status = can_send_email()
    send_allowed = bool(confirmed and send_status["can_send"])

    if not confirmed:
        render_warning_box("확인 체크박스를 선택해야 발송 버튼을 사용할 수 있습니다.")
    if not send_status["can_send"]:
        render_warning_box("ENABLE_SENDGRID_SEND, SENDGRID_API_KEY, EMAIL_ADDRESS 설정이 모두 충족되지 않아 실제 발송은 차단됩니다.")

    if st.button(s("SendGrid로 초안 발송"), disabled=not send_allowed):
        result = send_email_with_sendgrid(saved["to_email"], saved["title"], saved["text"])
        if result.ok:
            render_info_card("발송 결과", s(result.message), status="success")
        else:
            render_warning_box(s(result.message))
else:
    render_warning_box("입력값을 작성한 뒤 관리자 검증용 공문 초안을 생성하세요.")

render_page_footer_note()
