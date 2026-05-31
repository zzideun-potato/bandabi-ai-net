"""Rule-based explainable scoring for viable path analysis."""

from __future__ import annotations

from typing import Any

from modules.safety import sanitize_public_claims


LIMITATION_TEXT = "접근성 점수는 공공데이터와 파일럿 기준의 참고 점수이며, 실제 현장 상태와 다를 수 있습니다."


def grade_score(score: int) -> str:
    if score >= 80:
        return "이동 가능"
    if score >= 60:
        return "주의"
    if score >= 40:
        return "지원 필요"
    return "확인 불가"


def calculate_viable_path_score(inputs: dict[str, Any]) -> dict[str, Any]:
    support_type = str(inputs.get("accessibility_support_type", "일반"))
    mobility_needed = bool(inputs.get("mobility_support_needed", False))
    companion_needed = bool(inputs.get("companion_needed", False))
    weather_enabled = bool(inputs.get("weather_enabled", False))
    public_transport_available = bool(inputs.get("public_transport_available", True))
    origin_status = str(inputs.get("origin_geocode_status", "mock_fallback"))
    destination_status = str(inputs.get("destination_geocode_status", "mock_fallback"))

    destination_accessibility = 30 if "반다비" in str(inputs.get("destination", "")) else 22
    if support_type != "일반":
        destination_accessibility = min(destination_accessibility, 26)
    if destination_status != "real_api":
        destination_accessibility = max(destination_accessibility - 3, 15)

    mobility_support = 25
    if mobility_needed:
        mobility_support = 20 if companion_needed else 16
    if support_type.startswith("휠체어"):
        mobility_support = min(mobility_support, 18)

    weather_safety = 20
    if weather_enabled:
        weather_safety = 15

    bus_alternative = 10 if public_transport_available else 3
    protected_zone_safety = 8
    walking_transfer_burden = 5
    if support_type != "일반" and not companion_needed:
        walking_transfer_burden = 2
    if not public_transport_available:
        walking_transfer_burden = min(walking_transfer_burden, 3)

    item_scores = {
        "destination_accessibility": destination_accessibility,
        "mobility_support": mobility_support,
        "weather_safety": weather_safety,
        "bus_alternative": bus_alternative,
        "protected_zone_safety": protected_zone_safety,
        "walking_transfer_burden": walking_transfer_burden,
    }
    score = int(max(0, min(100, sum(item_scores.values()))))

    risk_factors: list[str] = []
    recommended_actions: list[str] = []

    if origin_status != "real_api" or destination_status != "real_api":
        risk_factors.append("주소 좌표가 시연용 대체 좌표 기준일 수 있음")
        recommended_actions.append("출발지와 목적지 주소를 운영기관 검토 전에 재확인")
    if mobility_needed:
        risk_factors.append("이동지원 후보 검토 필요")
        recommended_actions.append("교통약자 이동지원센터 기준과 이용 가능 여부 확인")
    if support_type != "일반":
        risk_factors.append(f"접근성 지원 유형: {support_type}")
        recommended_actions.append("도착지의 승강기, 보행 동선, 안내 지원 가능 여부 확인")
    if weather_enabled:
        risk_factors.append("날씨 영향은 API 또는 안전 대체 응답 기준")
        recommended_actions.append("이용 당일 기상 상태와 노면 상태 확인")
    if not public_transport_available:
        risk_factors.append("대중교통 대안이 제한될 수 있음")
        recommended_actions.append("대체 이동수단 후보를 함께 검토")
    if companion_needed:
        recommended_actions.append("동행 지원 가능 시간과 역할을 사전에 확인")

    if not risk_factors:
        risk_factors.append("현재 입력 기준 주요 위험요소 낮음")
    if not recommended_actions:
        recommended_actions.append("이용 전 운영기관 안내와 현장 동선을 확인")

    result = {
        "ai_name": "Viable Path Scoring AI",
        "model_type": "rule_based_explainable_ai",
        "score": score,
        "item_scores": item_scores,
        "mobility_level": grade_score(score),
        "risk_factors": [sanitize_public_claims(item) for item in risk_factors],
        "recommended_actions": [sanitize_public_claims(item) for item in recommended_actions],
        "explanation": "",
        "data_sources": [
            "사용자 입력",
            f"VWorld geocode status: origin={origin_status}, destination={destination_status}",
            "공공데이터 및 안전 대체 응답",
        ],
        "limitations": [LIMITATION_TEXT],
    }
    result["explanation"] = explain_score(result)
    return result


def explain_score(result: dict[str, Any]) -> str:
    score = int(result.get("score", 0))
    level = str(result.get("mobility_level", grade_score(score)))
    risks = ", ".join(result.get("risk_factors", []))
    text = (
        f"{result.get('ai_name', 'Viable Path Scoring AI')}는 입력값과 공공데이터 또는 안전 대체 응답을 기준으로 "
        f"{score}점, '{level}' 등급을 산출했습니다. 주요 확인 항목은 {risks}입니다. "
        f"{LIMITATION_TEXT}"
    )
    return sanitize_public_claims(text)


def score_viable_path(distance_km: float = 0.0, transfers: int = 0, accessibility_notes: int = 0) -> dict[str, float | str]:
    """Backward-compatible wrapper for the 1단계 placeholder page."""
    score = int(max(0, min(100, 75 - min(distance_km, 10) * 4 - transfers * 8 + accessibility_notes * 6)))
    return {"score": round(score, 1), "label": grade_score(score)}
