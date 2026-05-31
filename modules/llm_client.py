"""OpenRouter LLM client with strict fallback behavior."""

from __future__ import annotations

from typing import Any

from modules.config import get_secret
from modules.safety import get_disclaimer, sanitize_public_claims


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LATEST_NOTICE = "최신 정보는 김포반다비체육센터 또는 김포시교통약자이동지원센터 확인이 필요합니다."

RAG_SYSTEM_PROMPT = (
    "등록된 docs 근거 안에서만 답한다. "
    "문서에 없는 내용은 '현재 등록된 문서에서 확인되지 않습니다.'라고 답한다. "
    "실제 배차 확정, 예약 확정, 의료 진단, 치료, 재활 처방 표현은 사용하지 않는다. "
    f"답변 끝에는 '{LATEST_NOTICE}'를 붙인다."
)


def _fallback_result(source: str, text: str, reason: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "source": source,
        "text": sanitize_public_claims(text),
        "reason": reason,
    }


def _classify_exception(exc: Exception) -> str:
    """Classify errors without returning raw exception text or request URLs."""
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if "timeout" in name or "timeout" in message:
        return "timeout"
    if "rate" in name or "rate" in message or "429" in message:
        return "rate_limit"
    if "unauthorized" in name or "authentication" in name or "401" in message or "403" in message:
        return "unauthorized"
    if "notfound" in name or "not_found" in message or "invalid model" in message or "model" in message:
        return "model_error"
    if "connection" in name or "network" in message or "dns" in message:
        return "network_error"
    return "request_error"


def _append_latest_notice(text: str) -> str:
    cleaned = (text or "").strip()
    if LATEST_NOTICE not in cleaned:
        cleaned = f"{cleaned}\n\n{LATEST_NOTICE}".strip()
    return cleaned


def generate_with_openrouter(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> dict[str, Any]:
    api_key = get_secret("OPENROUTER_API_KEY")
    model = get_secret("OPENROUTER_MODEL")

    if not api_key:
        return _fallback_result(
            "fallback_missing_key",
            "OpenRouter 키가 설정되지 않아 로컬 대체 답변을 사용합니다.",
            "missing_key",
        )

    if not model:
        return _fallback_result(
            "fallback_missing_model",
            "OpenRouter 모델 설정이 없어 로컬 대체 답변을 사용합니다.",
            "missing_model",
        )

    try:
        from openai import OpenAI
    except Exception:
        return _fallback_result(
            "fallback_sdk_import_error",
            "OpenAI SDK를 불러오지 못해 로컬 대체 답변을 사용합니다.",
            "sdk_import_error",
        )

    try:
        client = OpenAI(api_key=str(api_key), base_url=OPENROUTER_BASE_URL, timeout=20.0)
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=str(model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = completion.choices[0].message.content or ""
        if not text.strip():
            return _fallback_result(
                "fallback_empty_response",
                "OpenRouter 응답이 비어 있어 로컬 대체 답변을 사용합니다.",
                "empty_response",
            )
        return {
            "ok": True,
            "source": "openrouter",
            "text": sanitize_public_claims(text),
            "reason": "",
            "model_status": "configured",
        }
    except Exception as exc:
        reason = _classify_exception(exc)
        return _fallback_result(
            f"fallback_{reason}",
            "OpenRouter 호출이 실패해 로컬 대체 답변을 사용합니다.",
            reason,
        )


def _template_rag_answer(question: str, context: str) -> str:
    if not context or context == "검색된 문서 근거가 없습니다.":
        return sanitize_public_claims(
            "현재 등록된 문서에서 확인되지 않습니다.\n\n"
            f"{LATEST_NOTICE}"
        )

    return sanitize_public_claims(
        "현재 등록된 문서 근거 기준의 참고 답변입니다.\n\n"
        f"질문: {question}\n\n"
        f"{context[:1800]}\n\n"
        f"{LATEST_NOTICE}"
    )


def generate_rag_answer(question: str, context: str) -> dict[str, Any]:
    disclaimer = get_disclaimer("general")
    prompt = (
        f"{disclaimer}\n\n"
        f"질문:\n{question}\n\n"
        f"docs 근거:\n{context}\n\n"
        "근거에 없는 내용은 추정하지 말고 확인되지 않는다고 답한다."
    )

    result = generate_with_openrouter(
        prompt=prompt,
        system_prompt=RAG_SYSTEM_PROMPT,
        temperature=0.2,
        max_tokens=800,
    )

    if result.get("ok"):
        result["text"] = sanitize_public_claims(_append_latest_notice(str(result.get("text", ""))))
        return result

    return {
        "ok": False,
        "source": result.get("source", "fallback"),
        "text": _template_rag_answer(question, context),
        "reason": result.get("reason", ""),
    }


def test_openrouter_text_connection(prompt: str = "김포 반다비 파일럿을 한 문장으로 설명") -> dict[str, Any]:
    """User-triggered smoke test. It never returns key values."""
    result = generate_with_openrouter(
        prompt=prompt,
        system_prompt="공공서비스 파일럿 QA용 짧은 한국어 응답만 작성한다.",
        temperature=0.1,
        max_tokens=120,
    )
    return {
        "ok": bool(result.get("ok")),
        "status": "configured" if result.get("ok") else "fallback",
        "source": result.get("source", "fallback"),
        "reason": result.get("reason", ""),
        "text": sanitize_public_claims(str(result.get("text", ""))[:500]),
    }


def fallback_answer(question: str, context: str = "") -> str:
    return _template_rag_answer(question, context)


def fallback_rag_answer(question: str, context: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "source": "fallback_template",
        "text": _template_rag_answer(question, context),
        "reason": "local_fallback",
    }


def generate_openrouter_answer(question: str, context: str = "") -> tuple[str, dict[str, Any]]:
    """Backward-compatible wrapper from the earlier project skeleton."""
    result = generate_rag_answer(question, context)
    return result["text"], {"mode": result.get("source", "fallback"), "reason": result.get("reason", "")}
