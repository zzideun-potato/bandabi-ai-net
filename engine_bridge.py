"""Connect 최최종.zip-style modules to the native Streamlit app without changing UI layout."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from math import asin, cos, radians, sin, sqrt
from typing import Any

from modules.api_clients import (
    data_go_kr_status,
    fetch_bus_arrival,
    fetch_bus_route,
    fetch_weather_short_forecast,
    geocode_vworld,
    mock_coordinate,
    test_vworld_geocode_connection,
    vworld_status,
)
from modules.config import get_secret
from modules.data_loader import load_csv_inventory
from modules.emailer import (
    build_official_draft as email_build_official_draft,
    can_send_email,
    email_status,
    improve_draft_with_llm,
    send_email_with_sendgrid,
)
from modules.rag_bm25 import answer_with_rag, build_index
from modules.scoring import calculate_viable_path_score
from modules.vision import analyze_accessibility_image, demo_vision_fallback, vision_status

DEFAULT_DESTINATION = "김포 반다비체육센터"
# VWorld는 시설명 검색이 잘 안 되어 주소로 좌표를 조회합니다 (변수.md 기준).
BANDABI_DESTINATION_GEOCODE = "경기도 김포시 사우중로 1"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(max(0.0, min(1.0, a))))


def resolve_route_coordinate(address: str, fallback_kind: str) -> dict[str, Any]:
    query = (address or "").strip()
    meta: dict[str, Any] = {"data_status": "fallback", "source": "fallback", "reason_code": "mock_coordinate"}
    try:
        geocode, meta = geocode_vworld(query)
        if geocode:
            return {
                "lat": float(geocode["y"]),
                "lon": float(geocode["x"]),
                "label": query,
                "data_status": meta.get("data_status", "real_api"),
                "source": meta.get("source", ""),
                "reason_code": meta.get("reason_code", ""),
            }
    except Exception:
        meta = {"data_status": "fallback", "source": "fallback", "reason_code": "api_error"}

    mock = mock_coordinate(fallback_kind)
    status = str(meta.get("data_status", "fallback"))
    if status == "mock_fallback":
        status = "fallback"
    return {
        "lat": float(mock["lat"]),
        "lon": float(mock["lon"]),
        "label": query or str(mock.get("label", "")),
        "data_status": status,
        "source": str(meta.get("source", "fallback")),
        "reason_code": str(meta.get("reason_code", "mock_coordinate")),
    }


def _normalize_api_status(status: Any) -> str:
    text = str(status or "fallback").strip()
    if text == "mock_fallback":
        return "fallback"
    return text


_LONG_DISTANCE_TOKENS = (
    "성남",
    "신흥",
    "분당",
    "수원",
    "서울",
    "인천",
    "부천",
    "안양",
    "의정부",
    "노원",
    "강남",
    "판교",
    "광명",
    "부평",
    "일산",
    "고양",
)
_GIMPO_TOKENS = ("김포", "구래", "장기", "운양", "마산", "양촌", "통진", "사우")


def _estimate_route_timing(
    origin_text: str,
    origin_coord: dict[str, Any],
    destination_coord: dict[str, Any],
) -> tuple[int, int, int, str, str, str, str]:
    normalized = (origin_text or "").replace(" ", "")
    long_distance = any(token in normalized for token in _LONG_DISTANCE_TOKENS)
    near_gimpo = any(token in normalized for token in _GIMPO_TOKENS)
    distance_km = _haversine_km(
        float(origin_coord["lat"]),
        float(origin_coord["lon"]),
        float(destination_coord["lat"]),
        float(destination_coord["lon"]),
    )
    origin_fallback = _normalize_api_status(origin_coord.get("data_status")) != "real_api"
    dest_fallback = _normalize_api_status(destination_coord.get("data_status")) != "real_api"
    both_fallback = origin_fallback and dest_fallback

    if long_distance or distance_km >= 35:
        total = max(70, min(95, int(distance_km * 1.4 + 22)))
        walk, transfers = max(14, int(total * 0.18)), 2
        alternative = "장거리 · 이동지원 연계 검토"
        risk = "중간 이상"
        route = "성남권 출발지 → 수도권 전철 환승 → 김포골드라인 → 김포 반다비체육센터"
        opinion = (
            "출발지가 성남권 또는 신흥역 권역으로 보입니다. 김포 반다비체육센터까지는 "
            "장거리 이동에 해당하므로 환승 여유와 이동지원센터 연계 검토가 필요합니다."
        )
    elif both_fallback and not near_gimpo:
        total = max(70, min(90, 78))
        walk, transfers = 15, 2
        alternative = "장거리 · 좌표 재확인 및 이동지원 검토"
        risk = "중간 이상"
        route = "출발지(대체좌표) → 광역 환승 → 김포 반다비체육센터"
        opinion = (
            "출발지·목적지 좌표가 시연용 대체값일 수 있어 직선 거리만으로는 시간을 추정하기 어렵습니다. "
            "성남·수도권 권역에서 출발한다면 장거리 이동으로 보고 환승·이동지원 여유를 두는 것이 안전합니다."
        )
    elif (near_gimpo or distance_km < 18) and not both_fallback and not long_distance:
        total = max(10, min(30, int(distance_km * 2.0 + 12)))
        walk, transfers = max(6, int(total * 0.28)), 1
        alternative = "저상버스·센터 주변 보행 연계 가능"
        risk = "낮음"
        route = "김포 관내 출발지 → 김포골드라인 또는 저상버스 → 센터 주변 보행"
        opinion = (
            "김포 관내 출발지로 확인되어 이동 부담이 비교적 낮습니다. "
            "센터 주변 마지막 보행 구간만 천천히 확인하면 무리가 적은 계획입니다."
        )
    else:
        total = max(40, min(75, int(distance_km * 1.8 + 18)))
        walk, transfers = max(10, int(total * 0.2)), 2
        alternative = "대체 이동수단 사전 문의 권장"
        risk = "중간"
        route = "출발지 → 광역/도시철도 환승 → 김포 반다비체육센터"
        opinion = (
            "출발지와 센터 사이 이동 거리가 있는 편입니다. 대중교통과 이동지원 차량을 "
            "함께 검토하면 참여 가능성이 높아집니다."
        )
    return total, walk, transfers, alternative, risk, route, opinion


def _fetch_route_public_apis_parallel() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    def _weather() -> dict[str, Any]:
        try:
            return fetch_weather_short_forecast()
        except Exception:
            return {"status": "network_error", "summary": {"weather_summary": "기상 API 네트워크 오류 · fallback"}}

    def _bus_route() -> dict[str, Any]:
        try:
            return fetch_bus_route()
        except Exception:
            return {"status": "api_error"}

    def _bus_arrival() -> dict[str, Any]:
        try:
            return fetch_bus_arrival()
        except Exception:
            return {"status": "network_error"}

    with ThreadPoolExecutor(max_workers=3) as pool:
        weather_future = pool.submit(_weather)
        route_future = pool.submit(_bus_route)
        arrival_future = pool.submit(_bus_arrival)
        return weather_future.result(), route_future.result(), arrival_future.result()


def _load_route_public_api_bundle(force_refresh: bool = False) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        import streamlit as st

        cached = st.session_state.get("route_public_api_cache")
        if cached and not force_refresh:
            return (
                cached.get("weather", {"status": "fallback"}),
                cached.get("bus_route", {"status": "fallback"}),
                cached.get("bus_arrival", {"status": "fallback"}),
            )
    except Exception:
        pass

    weather_result, bus_route_result, bus_arrival_result = _fetch_route_public_apis_parallel()
    try:
        import streamlit as st

        st.session_state.route_public_api_cache = {
            "weather": weather_result,
            "bus_route": bus_route_result,
            "bus_arrival": bus_arrival_result,
        }
    except Exception:
        pass
    return weather_result, bus_route_result, bus_arrival_result


def run_route_analysis(
    origin: str,
    destination: str,
    support: str,
    *,
    buddy_matching: bool,
    generated_at: str,
    force_refresh_apis: bool = False,
) -> dict[str, Any]:
    origin_coord = resolve_route_coordinate(origin, "default_origin")
    destination_coord = resolve_route_coordinate(
        BANDABI_DESTINATION_GEOCODE if destination == DEFAULT_DESTINATION else destination,
        "default_destination",
    )

    weather_result, bus_route_result, bus_arrival_result = _load_route_public_api_bundle(force_refresh_apis)

    weather_status = _normalize_api_status(weather_result.get("status", weather_result.get("data_status")))
    bus_route_status = _normalize_api_status(bus_route_result.get("status"))
    bus_arrival_status = _normalize_api_status(bus_arrival_result.get("status"))

    score_inputs = {
        "origin": origin,
        "destination": destination,
        "accessibility_support_type": support,
        "mobility_support_needed": any(token in support for token in ("휠체어", "보행 보조")),
        "companion_needed": buddy_matching,
        "weather_enabled": True,
        "public_transport_available": True,
        "origin_geocode_status": origin_coord["data_status"],
        "destination_geocode_status": destination_coord["data_status"],
        "weather_api_status": weather_status,
    }
    try:
        score_result = calculate_viable_path_score(score_inputs)
        opinion = str(score_result.get("explanation") or "")
        walk_risk = str(score_result.get("mobility_level") or "주의")
    except Exception:
        score_result = {}
        opinion = ""
        walk_risk = "주의"

    total, walk, transfers, alternative, timing_risk, route, timing_opinion = _estimate_route_timing(
        origin, origin_coord, destination_coord
    )
    if not opinion:
        opinion = timing_opinion
    elif timing_opinion not in opinion:
        opinion = f"{timing_opinion} {opinion}"

    weather_summary = ""
    summary_block = weather_result.get("summary")
    if isinstance(summary_block, dict):
        weather_summary = str(summary_block.get("weather_summary", ""))
    if not weather_summary:
        weather_summary = str(weather_result.get("message", "기상 정보 확인 필요"))
    weather_adjustment = (
        f"{weather_summary} (status: {weather_status})"
        if weather_status in {"real_api", "real_api_no_data"}
        else f"기상 {weather_status} · 비 예보 시 도보 구간 6분 여유 권장"
    )

    if bus_arrival_status == "real_api_no_data":
        bus_arrival = "TAGO 정상 응답 · 도착 데이터 없음 (real_api_no_data)"
    elif bus_arrival_status == "real_api":
        bus_arrival = "TAGO 버스 도착 정보 확인됨 (real_api)"
    else:
        bus_arrival = f"버스 도착 status: {bus_arrival_status} · 사전 확인 권장"

    origin_geo_status = _normalize_api_status(origin_coord["data_status"])
    dest_geo_status = _normalize_api_status(destination_coord["data_status"])
    status_line = (
        f"VWorld 출발 {origin_geo_status} / 목적 {dest_geo_status} · "
        f"기상 {weather_status} · 버스노선 {bus_route_status} · "
        f"버스도착 {bus_arrival_status} · scoring rule_engine"
    )

    return {
        "origin": origin,
        "destination": destination,
        "support": support,
        "recommended_route": route,
        "opinion": opinion,
        "total_time": f"약 {total}분",
        "walk_time": f"도보 약 {walk}분",
        "transfers": f"{transfers}회",
        "alternative": alternative,
        "walk_risk": timing_risk if timing_risk else walk_risk,
        "weather_adjustment": weather_adjustment,
        "facility_access": "센터 주출입구, 승강기, 접근 가능한 화장실 확인 필요",
        "bus_arrival": bus_arrival,
        "generated_at": generated_at,
        "status_line": status_line,
        "distance_km": round(
            _haversine_km(
                float(origin_coord["lat"]),
                float(origin_coord["lon"]),
                float(destination_coord["lat"]),
                float(destination_coord["lon"]),
            ),
            1,
        ),
        "engine_sources": {
            "vworld_origin": origin_geo_status,
            "vworld_destination": dest_geo_status,
            "weather": weather_status,
            "bus_route": bus_route_status,
            "bus_arrival": bus_arrival_status,
            "scoring": "rule_engine",
        },
        "score_result": score_result,
    }


def map_vision_source(raw_source: str) -> str:
    if raw_source in {"vision_model", "llm_real_api"}:
        return "llm_real_api"
    if raw_source in {"missing_key", "missing_model"}:
        return "missing_key"
    return "fallback"


def merge_vision_into_analysis(
    base: dict[str, Any],
    vision_raw: dict[str, Any] | None,
    *,
    has_photo: bool,
) -> dict[str, Any]:
    if not vision_raw:
        base["vision_source"] = "fallback"
        return base

    source = map_vision_source(str(vision_raw.get("source", "fallback")))
    base["vision_source"] = source
    base["source"] = source if source != "missing_key" else "missing_key"

    risk = str(vision_raw.get("risk_level", ""))
    if risk in {"높음", "중간", "관리자 확인 필요"}:
        base["grade"] = "관리자 확인 필요"
        base["admin_review_recommended"] = True
        base["improvement_need"] = "높음 · 관리자 확인 권장"
    detect_score = 78 if risk == "중간" else 88 if risk == "높음" else 62
    base["detection_score"] = float(detect_score)
    detected = vision_raw.get("detected_items") or []
    if detected:
        extra = str(detected[0])[:240]
        base["summary"] = f"{base.get('summary', '')} Vision 참고: {extra}"
    if not has_photo:
        base["confidence"] = "낮음"
    return base


def run_vision_analysis(
    facility_type: str,
    disability_focus: str,
    issue_choices: list[str],
    photo_bytes: bytes | None,
) -> dict[str, Any]:
    description = ", ".join(issue_choices) if issue_choices else disability_focus
    try:
        if photo_bytes:
            return analyze_accessibility_image(photo_bytes, facility_type, description)
        return demo_vision_fallback(facility_type, description)
    except Exception:
        return demo_vision_fallback(facility_type, description)


def prepare_access_email_draft(report: dict[str, Any], *, default_destination: str) -> dict[str, Any]:
    facility = report.get("facility_type") or report.get("report_type", "접근성 점검")
    title = f"[접근성 점검 요청] {default_destination} {facility} 확인 요청"
    body = (
        f"{default_destination} 이용 과정에서 접근성 확인이 필요한 지점이 있어 검토를 요청드립니다.\n\n"
        f"- 제보 시설: {facility}\n"
        f"- AI 보조 점검 등급: {report.get('grade', report.get('risk', '점검 필요'))}\n"
        f"- 개선 우선순위 참고 점수: {report.get('priority_score', '—')}점\n"
        f"- AI 보조 요약: {report.get('summary', '')}\n"
        "- 요청 사항: 현장 확인 후 보행 동선, 안내 표식, 안전 조치 필요 여부를 검토해 주세요."
    )
    location = default_destination
    recipient = "김포시 시설관리 담당부서"
    draft = email_build_official_draft(title, body, location, recipient, sender="김포 반다비 AI 운영팀")
    improved = improve_draft_with_llm(draft)
    draft_text = str(improved.get("text") or draft)
    draft_source = str(improved.get("source", "fallback"))
    if improved.get("ok"):
        draft_source = "llm_real_api"
    elif draft_source not in {"llm_real_api", "bm25_local"}:
        draft_source = "fallback"

    subject = title
    to_email = "facility@gimpo.go.kr"
    from_name = "김포 반다비 AI 운영팀"
    send_state = can_send_email()
    configured_sender = get_secret("EMAIL_ADDRESS", "")
    from_email = str(configured_sender) if configured_sender not in (None, "") else "EMAIL_ADDRESS 미설정"
    payload = {
        "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
        "from": {"email": from_email, "name": from_name},
        "content": [{"type": "text/plain", "value": draft_text}],
        "send_disabled": not bool(send_state.get("can_send")),
        "note": (
            "ENABLE_SENDGRID_SEND=true 이고 키·발신 주소가 있으면 발송 준비 버튼으로 SendGrid 전송을 시도합니다."
            if send_state.get("can_send")
            else "SendGrid 발송 조건 미충족 · payload 미리보기만 제공합니다."
        ),
        "email_status": send_state.get("data_status", "disabled"),
    }
    return {
        "subject": subject,
        "body": draft_text,
        "payload": payload,
        "draft_source": draft_source,
        "to_email": to_email,
        "from_name": from_name,
        "from_email": from_email,
        "can_send": bool(send_state.get("can_send")),
    }


def send_access_official_email(report: dict[str, Any], *, default_destination: str) -> dict[str, Any]:
    """Send official draft via SendGrid when ENABLE_SENDGRID_SEND and credentials are set."""
    prepared = prepare_access_email_draft(report, default_destination=default_destination)
    send_state = can_send_email()
    if not send_state.get("can_send"):
        return {
            "ok": False,
            "message": "SendGrid 발송 조건이 충족되지 않아 전송하지 않았습니다.",
            "data_status": str(send_state.get("data_status", "disabled")),
            "prepared": prepared,
        }

    result = send_email_with_sendgrid(
        str(prepared["to_email"]),
        str(prepared["subject"]),
        str(prepared["body"]),
    )
    return {
        "ok": bool(result.ok),
        "message": str(result.message),
        "data_status": str(result.data_status),
        "prepared": prepared,
    }


def load_report_rag() -> dict[str, Any]:
    try:
        result = answer_with_rag("김포 반다비 생활체육 참여 리포트와 다음 참여 가이드", top_k=5)
        source = str(result.get("source", "bm25_local"))
        if result.get("ok"):
            source = "llm_real_api"
        elif source.startswith("fallback"):
            source = "fallback"
        else:
            source = "bm25_local"
        result["display_source"] = source
        return result
    except Exception:
        return {"display_source": "fallback", "ok": False, "answer": ""}


def dashboard_api_status_items(*, refresh: bool = False, cache: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
    if cache and not refresh:
        return cache

    items: list[tuple[str, str]] = []
    try:
        vmeta = vworld_status()
        if vmeta.get("configured"):
            probe = test_vworld_geocode_connection("운양역")
            vlabel = _normalize_api_status(probe.get("status", probe.get("data_status")))
        else:
            vlabel = "missing_key"
        items.append(("VWorld 주소검색", vlabel))
    except Exception:
        items.append(("VWorld 주소검색", "api_error"))

    try:
        dmeta = data_go_kr_status()
        if not dmeta.get("configured"):
            items.append(("data.go.kr", "missing_key"))
        else:
            weather = fetch_weather_short_forecast()
            items.append(("기상 단기예보", _normalize_api_status(weather.get("status"))))
            bus_route = fetch_bus_route()
            items.append(("버스 노선 정보", _normalize_api_status(bus_route.get("status"))))
            bus_arrival = fetch_bus_arrival()
            items.append(("버스 도착 정보", _normalize_api_status(bus_arrival.get("status"))))
    except Exception:
        items.extend(
            [
                ("data.go.kr", "network_error"),
                ("기상 단기예보", "fallback"),
                ("버스 노선 정보", "fallback"),
                ("버스 도착 정보", "fallback"),
            ]
        )

    try:
        rag_index = build_index()
        items.append(("RAG 문서검색", f"{rag_index.data_status} · chunks {len(rag_index.chunks)}"))
    except Exception:
        items.append(("RAG 문서검색", "fallback"))

    try:
        send_state = email_status()
        items.append(("SendGrid", str(send_state.get("data_status", "disabled"))))
    except Exception:
        items.append(("SendGrid", "disabled"))

    try:
        inventory = load_csv_inventory()
        items.append(("CSV 데이터", str(inventory.get("data_status", "fallback"))))
    except Exception:
        items.append(("CSV 데이터", "fallback"))

    try:
        vstat = vision_status()
        items.append(("Vision 모델", str(vstat.get("data_status", "missing_key"))))
    except Exception:
        items.append(("Vision 모델", "fallback"))

    items.append(("접근성 제보", "session_store"))
    return items
