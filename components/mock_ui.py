"""UI-phase mock payloads — screen flow only, no external API calls."""

from __future__ import annotations

from typing import Any

from modules.safety import sanitize_public_claims


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def _is_long_distance(origin: str, destination: str) -> bool:
    cross_markers = ("성남", "신흥", "판교", "강남", "서울", "수원", "부천")
    dest_markers = ("김포", "반다비")
    return any(marker in origin for marker in cross_markers) and any(
        marker in destination for marker in dest_markers
    )


def _is_local_gimpo(origin: str, destination: str) -> bool:
    return any(marker in origin for marker in ("김포", "구래", "운양", "양씨")) and any(
        marker in destination for marker in ("김포", "반다비")
    )


def _route_profile(origin: str, destination: str, support_type: str) -> dict[str, Any]:
    if _is_long_distance(origin, destination):
        return {
            "total_time": s("90분+ · 장거리 · 이동지원 검토"),
            "walk": s("도보 구간 부담 가능 · 장거리"),
            "transfer": s("환승 1~2회 · 참고"),
            "alt_transport": s("이동지원·택시 연계 검토"),
            "bus_arrival": s("실시간 도착 정보 없음 · no_data"),
            "grade_label": s("지원 권장"),
            "score": 58,
            "explanation": s(
                "장거리 이동으로 도보·환승 부담이 클 수 있습니다. 이동지원 연계를 함께 검토해 주세요."
            ),
            "weather_text": s("맑음 · 바람 약함(데모)"),
            "badge": s("예상(참고용)"),
            "precise": False,
        }
    if _is_local_gimpo(origin, destination):
        return {
            "total_time": s("약 22분 · 참고"),
            "walk": s("도보 약 480m"),
            "transfer": s("환승 없음 · 참고"),
            "alt_transport": s("저상버스 가능성 높음"),
            "bus_arrival": s("버스 도착 약 8분(데모)"),
            "grade_label": s("원활"),
            "score": 84,
            "explanation": s("근거리 이동으로 대중교통·도보 병행이 가능해 보입니다. 현장 확인을 권장합니다."),
            "weather_text": s("맑음 · 바람 약함(데모)"),
            "badge": s("데모"),
            "precise": False,
        }
    return {
        "total_time": s("약 70분+ · 확인 필요"),
        "walk": s("도보 구간 확인 필요"),
        "transfer": s("환승 있을 수 있음 · 확인 필요"),
        "alt_transport": s("대중교통·이동지원 병행 검토"),
        "bus_arrival": s("실시간 도착 정보 없음 · no_data"),
        "grade_label": s("주의"),
        "score": 66,
        "explanation": s("이동 시간과 환승 부담을 함께 확인해 주세요. 필요 시 이동지원 연계를 검토합니다."),
        "weather_text": s("흐림 · 바람 보통(데모)"),
        "badge": s("예상(참고용)"),
        "precise": False,
    }


def mock_route_analysis(inputs: dict[str, Any]) -> dict[str, Any]:
    origin = str(inputs.get("origin") or "김포 구래역 1번 출구")
    destination = str(inputs.get("destination") or "김포 반다비체육센터")
    support = str(inputs.get("accessibility_support_type") or "일반")
    profile = _route_profile(origin, destination, support)

    return {
        "inputs": inputs,
        "origin_coord": {
            "lat": 37.645,
            "lon": 126.671,
            "label": origin,
            "data_status": "mock_fallback",
        },
        "destination_coord": {
            "lat": 37.615,
            "lon": 126.715,
            "label": destination,
            "data_status": "mock_fallback",
        },
        "weather_result": {"status": "mock_fallback", "summary": {"weather_summary": profile["weather_text"]}},
        "bus_route": {"status": "mock_fallback", "items": []},
        "bus_arrival": {"status": "mock_fallback", "message": profile["bus_arrival"]},
        "score_result": {
            "score": profile["score"],
            "mobility_level": profile["grade_label"],
            "recommended_actions": [profile["explanation"]],
        },
        "travel_metrics": {
            "total_time": profile["total_time"],
            "walk": profile["walk"],
            "transfer": profile["transfer"],
            "alt_transport": profile["alt_transport"],
            "precise": profile["precise"],
            "badge": profile["badge"],
            "route_status": "mock_fallback",
            "arrival_status": "mock_fallback",
        },
        "weather_text": profile["weather_text"],
        "grade_label": profile["grade_label"],
        "explanation": profile["explanation"],
    }


def mock_vision_result(*, location: str, description: str) -> dict[str, Any]:
    return {
        "risk_level": s("개선 필요 · 참고"),
        "detected_items": [
            s("점자블록 단절 의심 구간"),
            s("휠체어 회전 공간 부족 가능성"),
        ],
        "recommended_next_step": s(
            f"{location} 구간 현장 확인 후 접근성 개선 검토를 권장합니다. {description}".strip()
        ),
        "review_required": True,
        "source": "mock_ui",
        "reason": "ui_prototype",
    }


def build_sendgrid_payload_preview(
    *,
    to_email: str,
    from_email: str,
    from_name: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    return {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
        "mail_settings": {"sandbox_mode": {"enable": True}},
    }
