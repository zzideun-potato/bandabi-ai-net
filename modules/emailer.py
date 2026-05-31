"""Official draft and SendGrid helpers with disabled-by-default sending."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.config import get_bool_secret, get_secret
from modules.llm_client import generate_with_openrouter
from modules.safety import sanitize_public_claims


@dataclass(frozen=True)
class EmailResult:
    ok: bool
    message: str
    data_status: str = "not_sent"


def build_official_draft(title: str, body: str, location: str, recipient: str, sender: str = "") -> str:
    draft = f"""
[관리자 검증용 공문 초안]

수신: {recipient or "담당 부서 확인 필요"}
발신: {sender or "발신자 확인 필요"}
제목: {title or "제보 검토 요청"}

1. 검토 요청 위치
{location or "위치 정보 미입력"}

2. 제보 내용
{body or "제보 내용 미입력"}

3. 요청 취지
본 문서는 관리자 검증용 초안입니다. 담당 부서 확인, 개인정보 마스킹, 현장 상태 확인 후 필요한 절차로 전환될 수 있습니다.

4. 유의 사항
AI 또는 시스템 생성 문구는 참고 자료이며 공식 절차 처리 결과가 아닙니다.
"""
    return sanitize_public_claims(draft.strip())


def improve_draft_with_llm(draft_text: str) -> dict[str, Any]:
    prompt = (
        "다음 공문 초안을 공공기관 검토용 문체로 정리한다. "
        "공식 절차 처리 결과로 오해될 표현은 쓰지 말고, 관리자 검증용 초안임을 유지한다.\n\n"
        f"{draft_text}"
    )
    result = generate_with_openrouter(prompt, system_prompt="관리자 검증용 공문 초안만 작성한다.", temperature=0.2, max_tokens=900)
    if result.get("ok"):
        result["text"] = sanitize_public_claims(str(result.get("text", "")))
        return result
    return {
        "ok": False,
        "source": result.get("source", "fallback"),
        "text": sanitize_public_claims(draft_text),
        "reason": result.get("reason", ""),
    }


def can_send_email() -> dict[str, Any]:
    enabled = get_bool_secret("ENABLE_SENDGRID_SEND", False)
    has_key = bool(get_secret("SENDGRID_API_KEY"))
    has_sender = bool(get_secret("EMAIL_ADDRESS"))
    can_send = bool(enabled and has_key and has_sender)

    if not enabled:
        data_status = "disabled"
    elif not has_key or not has_sender:
        data_status = "missing_config"
    else:
        data_status = "enabled_ready"

    return {
        "enabled": enabled,
        "has_key": has_key,
        "has_sender": has_sender,
        "can_send": can_send,
        "data_status": data_status,
    }


def email_status() -> dict[str, Any]:
    status = can_send_email()
    return {
        **status,
        "message": sanitize_public_claims(
            "SendGrid 전송은 ENABLE_SENDGRID_SEND가 true이고 API 키, 발신 이메일, 사용자 확인이 모두 있을 때만 시도됩니다."
        ),
    }


def _sendgrid_error_status(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if "unauthorized" in name or "forbidden" in name:
        return "auth_error"
    if "timeout" in name:
        return "timeout"
    if "connection" in name or "network" in name:
        return "network_error"
    return "send_error"


def send_email_with_sendgrid(to_email: str, subject: str, body: str) -> EmailResult:
    status = can_send_email()
    if not status["can_send"]:
        return EmailResult(
            ok=False,
            message=sanitize_public_claims("SendGrid 전송 조건이 충족되지 않아 전송하지 않았습니다."),
            data_status=status["data_status"],
        )

    if not to_email:
        return EmailResult(
            ok=False,
            message=sanitize_public_claims("수신 이메일이 없어 전송하지 않았습니다."),
            data_status="missing_recipient",
        )

    api_key = get_secret("SENDGRID_API_KEY")
    from_email = get_secret("EMAIL_ADDRESS")

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=str(from_email),
            to_emails=str(to_email),
            subject=sanitize_public_claims(subject),
            plain_text_content=sanitize_public_claims(body),
        )
        SendGridAPIClient(str(api_key)).send(message)
        return EmailResult(ok=True, message=sanitize_public_claims("SendGrid 전송 요청이 처리되었습니다."), data_status="sent")
    except Exception as exc:
        return EmailResult(
            ok=False,
            message=sanitize_public_claims(f"SendGrid 전송 실패 상태: {_sendgrid_error_status(exc)}"),
            data_status="send_error",
        )


def send_email_if_enabled(subject: str, body: str) -> EmailResult:
    """Backward-compatible wrapper. No recipient means the send is blocked."""
    return send_email_with_sendgrid("", subject, body)
