"""Route analysis orchestration — wraps modules/ without modifying them."""

from __future__ import annotations

import math
from typing import Any

from modules.api_clients import (
    fetch_bus_arrival,
    fetch_bus_route,
    fetch_weather_short_forecast,
    geocode_vworld,
    mock_coordinate,
)
from modules.scoring import calculate_viable_path_score, explain_score, grade_score
from modules.safety import sanitize_public_claims


GIMPO2_CENTER_KEY = "gimpo2"
GIMPO2_WARNING = (
    "김포 제2 반다비 교육거점은 아직 등록되지 않은 예정 시설입니다. "
    "현재는 김포 반다비체육센터 기준으로 이용해 주세요."
)

CENTER_OPTIONS = {
    "gimpo": "김포 반다비체육센터",
    GIMPO2_CENTER_KEY: "김포 제2 반다비 교육거점",
}

DISABILITY_MAP = {
    "physical": "휠체어 또는 보행 보조 필요",
    "visual": "음성 안내 또는 유도 동선 필요",
    "developmental": "단계별 안내 또는 보호자·동행 지원 필요",
    "senior": "일반",
}


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def resolve_coordinate(address: str, fallback_kind: str) -> dict[str, Any]:
    geocode, meta = geocode_vworld(address)
    if geocode:
        try:
            return {
                "lat": float(geocode["y"]),
                "lon": float(geocode["x"]),
                "label": address,
                "data_status": meta.get("data_status", "real_api"),
                "source": meta.get("source", ""),
                "display_message": meta.get("display_message", ""),
            }
        except Exception:
            pass

    mock = mock_coordinate(fallback_kind)
    return {
        "lat": float(mock["lat"]),
        "lon": float(mock["lon"]),
        "label": address or mock["label"],
        "data_status": meta.get("data_status", "mock_fallback"),
        "source": meta.get("source", "fallback"),
        "display_message": meta.get(
            "display_message",
            "VWorld 실응답을 확인하지 못해 시연용 대체 좌표를 사용했습니다.",
        ),
    }


def _first_item_value(items: list[Any], keys: tuple[str, ...]) -> str | None:
    for item in items:
        if not isinstance(item, dict):
            continue
        lower = {str(k).lower(): v for k, v in item.items()}
        for key in keys:
            value = lower.get(key.lower())
            if value not in (None, ""):
                return str(value)
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _qualitative_walk(support_type: str) -> str:
    if "휠체어" in support_type or "보행" in support_type:
        return "도보 부담 가능성 있음 · 현장 확인 필요"
    if "음성" in support_type:
        return "도보 동선 안내 확인 필요"
    return "도보 보통 · 현장 확인 권장"


def _qualitative_transfer(public_transport: bool) -> str:
    if public_transport:
        return "환승 있을 수 있음 · 확인 필요"
    return "환승 정보 없음 · 확인 필요"


def _qualitative_time() -> str:
    return "이동시간 확인 필요"


def build_travel_metrics(
    *,
    bus_route: dict[str, Any],
    bus_arrival: dict[str, Any],
    origin_coord: dict[str, Any],
    destination_coord: dict[str, Any],
    support_type: str,
    public_transport_available: bool,
) -> dict[str, Any]:
    """Return display metrics; precise numbers only when real_api fields exist."""
    route_real = bus_route.get("status") == "real_api"
    arrival_real = bus_arrival.get("status") == "real_api"
    precise = False

    total_time_text = _qualitative_time()
    walk_text = _qualitative_walk(support_type)
    transfer_text = _qualitative_transfer(public_transport_available)
    badge = "예상(참고용)"

    if route_real:
        items = bus_route.get("items") or []
        route_name = _first_item_value(items, ("routeno", "routeNo", "route_no"))
        route_time = _first_item_value(items, ("routetp", "routeTp"))
        if route_name:
            total_time_text = s(f"노선 {route_name} · 상세 시간은 정류소 기준 확인")
            if route_time:
                total_time_text = s(f"노선 {route_name} ({route_time}) · 도착 API와 함께 확인")
            badge = "실API(노선)"

    if arrival_real:
        items = bus_arrival.get("items") or []
        arr_sec = _first_item_value(items, ("arrprevstationcnt", "arrprevstationnum"))
        arr_time = _first_item_value(
            items,
            ("arrtime", "arrTime", "arrprevstationtime", "predicttime1", "predictTime1"),
        )
        if arr_time and arr_time.isdigit():
            minutes = max(1, int(int(arr_time) / 60)) if int(arr_time) > 120 else int(arr_time)
            total_time_text = s(f"버스 도착 약 {minutes}분 (실API)")
            precise = True
            badge = "실API(도착)"
        elif arr_sec:
            transfer_text = s(f"남은 정류소 {arr_sec}개 (실API)")
            precise = True

    if route_real and origin_coord.get("data_status") == "real_api" and destination_coord.get("data_status") == "real_api":
        km = _haversine_km(origin_coord["lat"], origin_coord["lon"], destination_coord["lat"], destination_coord["lon"])
        if km > 0:
            walk_m = int(min(km * 1000 * 0.15, 800))
            if walk_m >= 50:
                walk_text = s(f"도보 약 {walk_m}m (좌표 기준 참고)")
                precise = True

    if not precise:
        total_time_text = s(total_time_text)
        walk_text = s(walk_text)
        transfer_text = s(transfer_text)

    return {
        "total_time": total_time_text,
        "walk": walk_text,
        "transfer": transfer_text,
        "precise": precise,
        "badge": badge,
        "route_status": bus_route.get("status", "fallback"),
        "arrival_status": bus_arrival.get("status", "fallback"),
    }


def run_route_analysis(inputs: dict[str, Any]) -> dict[str, Any]:
    origin_coord = resolve_coordinate(inputs["origin"], "default_origin")
    destination_coord = resolve_coordinate(inputs["destination"], "default_destination")
    weather_result = fetch_weather_short_forecast()
    bus_route = fetch_bus_route()
    bus_arrival = fetch_bus_arrival()

    score_inputs = {
        **inputs,
        "origin_geocode_status": origin_coord["data_status"],
        "destination_geocode_status": destination_coord["data_status"],
        "weather_enabled": True,
        "weather_api_status": weather_result.get("status", "fallback"),
    }
    score_result = calculate_viable_path_score(score_inputs)
    travel_metrics = build_travel_metrics(
        bus_route=bus_route,
        bus_arrival=bus_arrival,
        origin_coord=origin_coord,
        destination_coord=destination_coord,
        support_type=inputs.get("accessibility_support_type", "일반"),
        public_transport_available=bool(inputs.get("public_transport_available", True)),
    )

    weather_summary = weather_result.get("summary", {})
    if isinstance(weather_summary, dict):
        weather_text = s(weather_summary.get("weather_summary", weather_result.get("message", "확인 필요")))
    else:
        weather_text = s(str(weather_summary or "확인 필요"))

    return {
        "inputs": inputs,
        "origin_coord": origin_coord,
        "destination_coord": destination_coord,
        "weather_result": weather_result,
        "bus_route": bus_route,
        "bus_arrival": bus_arrival,
        "score_result": score_result,
        "travel_metrics": travel_metrics,
        "weather_text": weather_text,
        "grade_label": s(score_result.get("mobility_level", grade_score(int(score_result.get("score", 0))))),
        "explanation": s(explain_score(score_result)),
    }


DISPLAY_GRADE_MAP = {
    "이동 가능": "원활",
    "주의": "주의",
    "지원 필요": "지원 권장",
    "확인 불가": "대체 경로 권장",
}


def _is_long_distance_cross_city(origin: str, destination: str) -> bool:
    cross_markers = ("성남", "신흥", "판교", "강남", "서울")
    dest_markers = ("김포", "반다비")
    return any(marker in origin for marker in cross_markers) and any(marker in destination for marker in dest_markers)


def _is_local_gimpo_route(origin: str, destination: str) -> bool:
    return any(marker in origin for marker in ("김포", "구래", "운양", "양씨")) and any(
        marker in destination for marker in ("김포", "반다비")
    )


def format_duration_for_ui(origin: str, destination: str, result: dict[str, Any], travel_metrics: dict[str, Any]) -> str:
    if travel_metrics.get("precise") and "실API" in str(travel_metrics.get("badge", "")):
        return s(travel_metrics["total_time"])
    if _is_long_distance_cross_city(origin, destination):
        return "90분+ · 장거리 · 이동지원 검토"
    if _is_local_gimpo_route(origin, destination):
        origin_coord = result["origin_coord"]
        destination_coord = result["destination_coord"]
        km = _haversine_km(origin_coord["lat"], origin_coord["lon"], destination_coord["lat"], destination_coord["lon"])
        minutes = max(10, min(30, int(round(km * 3.5 + 8))))
        return s(f"약 {minutes}분 · 참고")
    return s(travel_metrics.get("total_time", "이동시간 확인 필요"))


def analyze_route_for_api(origin: str, destination: str, disability: str = "physical") -> dict[str, Any]:
    """Return UI-safe route analysis payload for POST /api/route-analysis."""
    support = DISABILITY_MAP.get(disability, "일반")
    inputs = {
        "origin": origin.strip(),
        "destination": destination.strip(),
        "accessibility_support_type": support,
        "mobility_support_needed": disability in ("physical", "developmental", "senior"),
        "companion_needed": disability in ("visual", "developmental"),
        "public_transport_available": True,
    }
    result = run_route_analysis(inputs)
    score_result = result["score_result"]
    travel = result["travel_metrics"]
    mobility_level = str(score_result.get("mobility_level", grade_score(int(score_result.get("score", 0)))))
    display_grade = DISPLAY_GRADE_MAP.get(mobility_level, mobility_level)
    duration = format_duration_for_ui(origin, destination, result, travel)
    weather_result = result["weather_result"]
    weather_status = weather_result.get("status", "fallback")
    weather_text = result["weather_text"]
    arrival = result["bus_arrival"]
    arrival_status = arrival.get("status", "fallback")

    origin_status = str(result["origin_coord"].get("data_status", "mock_fallback"))
    vworld_label = "VWorld 실제 API" if origin_status == "real_api" else "VWorld fallback"
    weather_label = f"기상 {weather_status}"
    arrival_label = f"버스 도착 {arrival_status if arrival_status == 'real_api' else 'no_data'}"
    status_line = f"{vworld_label} · {weather_label} · {arrival_label} · scoring rule_engine"

    return {
        "ok": True,
        "origin_label": s(result["origin_coord"].get("label", origin)),
        "dest_label": s(result["destination_coord"].get("label", destination)),
        "score": int(score_result.get("score", 0)),
        "grade": display_grade,
        "action": result["explanation"],
        "status_line": status_line,
        "bus_route": {
            "routeId": "API-ROUTE",
            "duration": duration,
            "walk": s(travel.get("walk", "확인 필요")),
            "transfer": s(travel.get("transfer", "확인 필요")),
            "mode": s("저상버스 · 참고" if _is_local_gimpo_route(origin, destination) else "대중교통 · 참고"),
        },
        "weather": {
            "wind": "강풍 주의" if "강풍" in weather_text else "없음",
            "rain": "없음",
            "temp": "보통",
            "summary": weather_text,
            "data_status": weather_status,
        },
        "arrival": {
            "status": "no_data" if arrival_status not in {"real_api"} else "ok",
            "eta": None,
            "message": s(arrival.get("message", "실시간 도착 정보 없음")),
        },
        "source": "python_modules",
    }


def data_status_badge(status: str) -> tuple[str, str]:
    if status == "real_api":
        return ("실API", "ok")
    if status == "real_api_no_data":
        return ("no_data", "no-data")
    if status == "missing_key":
        return ("대체 데이터", "warn")
    return ("대체 데이터", "warn")
