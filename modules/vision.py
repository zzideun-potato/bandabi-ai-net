"""Optional accessibility image analysis with safe alternate behavior."""

from __future__ import annotations

import base64
from typing import Any

from modules.config import get_secret
from modules.llm_client import OPENROUTER_BASE_URL
from modules.safety import sanitize_public_claims


VISION_NOTICE = (
    "AI 검출 결과는 공식 민원 또는 행정처분 자료가 아닙니다. "
    "관리자 검증, 개인정보 마스킹, 담당 공무원 확인 후 공식 절차로 전환될 수 있습니다."
)


def _classify_vision_error(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if "timeout" in name or "timeout" in message:
        return "timeout"
    if "unauthorized" in name or "authentication" in name or "401" in message or "403" in message:
        return "unauthorized"
    if "rate" in name or "429" in message:
        return "rate_limit"
    if "image" in message or "vision" in message or "model" in message:
        return "unsupported_or_model_error"
    if "connection" in name or "network" in message or "dns" in message:
        return "network_error"
    return "request_error"


def mask_notice() -> str:
    return sanitize_public_claims(
        "얼굴, 차량번호, 연락처, 상세 주소 등 개인정보가 포함될 수 있어 관리자 확인 단계에서 마스킹 필요 여부를 점검해야 합니다."
    )


def vision_status() -> dict[str, str | bool]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("VISION_MODEL")
    if api_key and model:
        return {"configured": True, "data_status": "configured", "message": "Vision 모델 설정이 감지되었습니다."}
    if api_key and not model:
        return {"configured": False, "data_status": "missing_model", "message": "VISION_MODEL 설정이 없어 시연용 대체 응답을 사용합니다."}
    return {"configured": False, "data_status": "missing_key", "message": "OPENROUTER_API_KEY 설정이 없어 시연용 대체 응답을 사용합니다."}


def test_vision_model_available() -> dict[str, Any]:
    """User-triggered status check only. Image analysis is not run here."""
    status = vision_status()
    if status["data_status"] == "configured":
        qa_status = "configured"
        reason = ""
    elif status["data_status"] == "missing_model":
        qa_status = "fallback"
        reason = "missing_model"
    else:
        qa_status = "fallback"
        reason = "missing_key"
    return {
        "ok": bool(status["configured"]),
        "status": qa_status,
        "source": "vision_status",
        "reason": reason,
        "message": sanitize_public_claims(str(status["message"])),
    }


def demo_vision_fallback(report_type: str, description: str = "") -> dict[str, Any]:
    report = report_type or "기타"
    combined = f"{report} {description}"
    risk_level = "낮음"
    if any(term in combined for term in ("경사로", "장애물", "화장실")):
        risk_level = "중간"
    if any(term in combined for term in ("차단", "위험", "불편", "부족")):
        risk_level = "높음"

    detected_items = [sanitize_public_claims(report)]
    if description:
        detected_items.append(sanitize_public_claims("사용자 설명 기반 확인 후보 포함"))

    return {
        "ok": False,
        "risk_level": risk_level,
        "detected_items": detected_items,
        "review_required": True,
        "privacy_masking_required": True,
        "recommended_next_step": sanitize_public_claims("관리자 검증 후 담당 부서 확인 자료로 정리"),
        "notice": sanitize_public_claims(VISION_NOTICE),
        "mask_notice": mask_notice(),
        "source": "demo_fallback",
        "reason": "fallback",
    }


def analyze_accessibility_image(image_bytes: bytes | None, report_type: str, description: str = "") -> dict[str, Any]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("VISION_MODEL")

    if not image_bytes:
        result = demo_vision_fallback(report_type, description)
        result["reason"] = "missing_input"
        result["message"] = "이미지 입력이 없어 시연용 대체 응답을 표시합니다."
        return result

    if not api_key:
        result = demo_vision_fallback(report_type, description)
        result["source"] = "missing_key"
        result["reason"] = "missing_key"
        return result

    if not model:
        result = demo_vision_fallback(report_type, description)
        result["reason"] = "missing_model"
        return result

    try:
        from openai import OpenAI

        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        client = OpenAI(api_key=str(api_key), base_url=OPENROUTER_BASE_URL, timeout=20.0)
        completion = client.chat.completions.create(
            model=str(model),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "접근성 이미지 임시 검토를 수행한다. 공식 판단처럼 단정하지 않는다. "
                        "개인정보 마스킹 필요 여부와 관리자 확인 필요 여부를 포함한다."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"제보 유형: {report_type}\n설명: {description}\n"
                                "risk_level, detected_items, review_required, recommended_next_step를 한국어로 요약."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=500,
        )
        text = sanitize_public_claims(completion.choices[0].message.content or "")
        if not text.strip():
            result = demo_vision_fallback(report_type, description)
            result["reason"] = "empty_response"
            return result
        return {
            "ok": True,
            "risk_level": "관리자 확인 필요",
            "detected_items": [text],
            "review_required": True,
            "privacy_masking_required": True,
            "recommended_next_step": sanitize_public_claims("관리자 검증 후 담당 부서 확인 자료로 정리"),
            "notice": sanitize_public_claims(VISION_NOTICE),
            "mask_notice": mask_notice(),
            "source": "vision_model",
            "reason": "",
        }
    except Exception as exc:
        result = demo_vision_fallback(report_type, description)
        result["reason"] = _classify_vision_error(exc)
        return result


def summarize_image_upload(filename: str | None, size: int | None = None) -> dict[str, str | int | None]:
    return {
        "filename": sanitize_public_claims(filename or ""),
        "size": size,
        "status": "업로드 확인",
        "note": sanitize_public_claims("AI 비전검증은 optional 기능이며 실패 시 시연용 대체 응답을 사용합니다."),
    }
