"""Optional voice command helpers with text fallback."""

from __future__ import annotations

import html
import json

import streamlit as st
import streamlit.components.v1 as components

from modules.safety import sanitize_public_claims


INTENT_RULES = {
    "route": ("경로", "길", "위치", "분석"),
    "mobility": ("이동지원", "차량", "교통약자", "이동"),
    "sports_report": ("생활체육", "리포트", "프로그램", "운동"),
    "vision": ("사진", "이미지", "검증", "제보"),
    "official_draft": ("공문", "초안", "메일", "이메일"),
    "dashboard": ("대시보드", "운영", "현황", "통계"),
}


def classify_voice_command(text: str) -> str:
    normalized = (text or "").strip().lower()
    if not normalized:
        return "unknown"

    for intent, keywords in INTENT_RULES.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            return intent
    return "unknown"


def voice_status() -> dict[str, str | bool]:
    try:
        import streamlit_mic_recorder  # noqa: F401

        return {
            "available": True,
            "data_status": "optional_available",
            "message": sanitize_public_claims("음성 입력 컴포넌트를 사용할 수 있습니다. 음성 파일은 저장하지 않습니다."),
        }
    except Exception:
        return {
            "available": False,
            "data_status": "text_fallback",
            "message": sanitize_public_claims("음성 입력 컴포넌트가 없어 텍스트 대체 입력을 사용합니다."),
        }


def render_voice_command_box(key: str = "voice_command") -> dict[str, str]:
    status = voice_status()
    st.caption(str(status["message"]))

    command_text = ""
    if status["available"]:
        try:
            from streamlit_mic_recorder import mic_recorder

            mic_recorder(start_prompt="녹음 시작", stop_prompt="녹음 종료", key=f"{key}_mic")
            st.caption(sanitize_public_claims("STT는 현재 placeholder입니다. 필요한 명령은 아래 텍스트로 입력합니다."))
        except Exception:
            st.caption(sanitize_public_claims("음성 컴포넌트 호출 실패로 텍스트 대체 입력을 사용합니다."))

    command_text = st.text_input(
        "음성 명령 텍스트 대체 입력",
        placeholder="예: 경로 분석해줘, 공문 초안 만들어줘",
        key=f"{key}_text",
    )
    intent = classify_voice_command(command_text)
    return {"text": sanitize_public_claims(command_text), "intent": intent, "data_status": str(status["data_status"])}


def render_browser_tts_button(text: str) -> None:
    safe_text = sanitize_public_claims(text or "")
    escaped = html.escape(safe_text)
    js_text = json.dumps(safe_text, ensure_ascii=False)
    try:
        components.html(
            f"""
            <button onclick='speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance({js_text}));'>
              음성 응답 듣기
            </button>
            <span style="font-size:12px;color:#52606d;margin-left:8px;">{escaped[:80]}</span>
            """,
            height=42,
        )
    except Exception:
        st.caption(sanitize_public_claims("브라우저 TTS를 사용할 수 없습니다."))
