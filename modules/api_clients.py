"""External API clients with timeout, safe diagnostics, and fallback-first behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree as ET

import requests

from modules.config import get_secret
from modules.safety import sanitize_public_claims

SPORTS_FACILITY_URL = "https://apis.data.go.kr/B551014/SRVC_API_SFMS_FACI"
SPORTS_FACILITY_DETAIL_URL = "https://apis.data.go.kr/B551014/SRVC_SFMS_FACIL_INFO"
DISABLED_CONVENIENCE_URL = "https://apis.data.go.kr/B554287/DisabledPersonConvenientFacility"
MOBILITY_SUPPORT_URL = "https://apis.data.go.kr/B551982/tsdo_v2"
WEATHER_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
BUS_ARRIVAL_URL = "https://apis.data.go.kr/1613000/ArvlInfoInqireService"
BUS_ROUTE_URL = "https://apis.data.go.kr/1613000/BusRouteInfoInqireService"
VWORLD_SEARCH_URL = "https://api.vworld.kr/req/search"
VWORLD_ADDRESS_URL = "https://api.vworld.kr/req/address"

GIMPO_STDG_CD = "4157000000"
DEFAULT_TAGO_ROUTE_NO = "81"

MOCK_COORDINATES = {
    "default_origin": {"lat": 37.615, "lon": 126.715, "label": "김포시 mock 출발지"},
    "default_destination": {"lat": 37.638, "lon": 126.682, "label": "김포반다비체육센터 mock 목적지"},
}


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    data: Any = None
    data_status: str = "missing"
    error: str = ""
    reason: str = ""


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _is_success_code(code: Any) -> bool:
    normalized = str(code or "").strip().upper().replace(" ", "_")
    return normalized in {"00", "0", "K0", "INFO-000", "NORMAL_CODE"}


def _is_no_data_code(code: Any, message: Any = "") -> bool:
    normalized_code = str(code or "").strip().upper().replace(" ", "_")
    normalized_message = str(message or "").strip().upper().replace(" ", "_")
    return normalized_code in {"03", "K3", "NO_DATA", "NODATA_ERROR"} or "NO_DATA" in normalized_message or "NODATA" in normalized_message


def _redact_public_data_error(message: Any) -> str:
    text = str(message or "")
    for token in ("serviceKey", "ServiceKey", "SERVICEKEY", "apikey", "apiKey", "key="):
        text = text.replace(token, "redacted")
    if len(text) > 160:
        text = text[:160]
    return sanitize_public_claims(text)


def _join_endpoint(base: str, operation: str) -> str:
    return f"{base.rstrip('/')}/{operation.lstrip('/')}"


def _operation_name(endpoint: str) -> str:
    return endpoint.rstrip("/").rsplit("/", 1)[-1]


def _classify_request_error(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.ConnectionError):
        return "network_error"
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        return "unauthorized"
    if status_code == 429:
        return "rate_limit"
    if status_code:
        return f"http_{status_code}"
    if "json" in name or "parse" in name:
        return "parse_error"
    return "api_error"


def classify_public_data_error(error_or_response: Any) -> str:
    if isinstance(error_or_response, Exception):
        return _classify_request_error(error_or_response)
    if isinstance(error_or_response, requests.Response):
        status_code = error_or_response.status_code
        if status_code in (401, 403):
            return "unauthorized"
        if status_code == 429:
            return "rate_limit"
        if status_code in (500, 502, 503, 504):
            return f"http_{status_code}"
        if status_code >= 400:
            return f"http_{status_code}"
    return "api_error"


def _status_message(status: str) -> str:
    messages = {
        "real_api": "공공데이터 API 실응답을 사용했습니다.",
        "real_api_no_data": "공공데이터 API 정상 응답이나 검색 조건 기준 결과가 없습니다.",
        "missing_key": "DATA_GO_KR_SERVICE_KEY가 없어 대체 응답을 사용합니다.",
        "missing_params": "필수 파라미터가 부족해 대체 응답을 사용합니다.",
        "api_error": "API 응답 상태가 정상으로 확인되지 않아 대체 응답을 사용합니다.",
        "timeout": "API timeout으로 대체 응답을 사용합니다.",
        "network_error": "네트워크 오류로 대체 응답을 사용합니다.",
        "parse_error": "응답 파싱 실패로 대체 응답을 사용합니다.",
        "fallback": "대체 응답을 사용합니다.",
    }
    return messages.get(status, "대체 응답을 사용합니다.")


def _clean_item(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clean_item(v) for k, v in value.items() if str(k).lower() not in {"servicekey", "apikey", "key"}}
    if isinstance(value, list):
        return [_clean_item(item) for item in value]
    return sanitize_public_claims(str(value)) if isinstance(value, str) else value


def make_api_result(
    service_name: str,
    status: str,
    data: Any = None,
    items: list[Any] | None = None,
    message: str = "",
    source: str = "public_data",
    endpoint_name: str = "",
    real_count: int = 0,
    fallback_count: int = 0,
    reason_code: str = "",
    action_needed: str = "",
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cleaned_items = [_clean_item(item) for item in (items if items is not None else [])]
    if status == "real_api":
        real_count = len(cleaned_items) if real_count == 0 else real_count
        fallback_count = 0
    elif source == "fallback":
        real_count = 0
        fallback_count = len(cleaned_items) if fallback_count == 0 else fallback_count
    elif status == "real_api_no_data":
        real_count = 0
        fallback_count = 0

    return {
        "service_name": sanitize_public_claims(service_name),
        "status": status,
        "data_status": status,
        "real_count": real_count,
        "fallback_count": fallback_count,
        "count": real_count,
        "items": cleaned_items,
        "summary": _clean_item(summary or {}),
        "source": source,
        "reason_code": sanitize_public_claims(reason_code or status),
        "action_needed": sanitize_public_claims(action_needed or _default_action_needed(status)),
        "endpoint_name": sanitize_public_claims(endpoint_name),
        "message": sanitize_public_claims(message or _status_message(status)),
        "data": _clean_item(data) if data is not None else None,
    }


def _default_action_needed(status: str) -> str:
    if status in {"real_api", "real_api_no_data"}:
        return "없음"
    if status == "missing_key":
        return "Streamlit Secrets의 DATA_GO_KR_SERVICE_KEY 확인"
    if status == "missing_params":
        return "필수 요청 파라미터 입력"
    if status == "parse_error":
        return "응답 형식 또는 operation 확인"
    if status in {"timeout", "network_error"}:
        return "네트워크 상태 또는 API 운영 상태 재확인"
    return "요청 파라미터 또는 operation 확인"


def safe_get_json(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = 5,
) -> ApiResult:
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return ApiResult(ok=True, data=response.json(), data_status="real_api")
    except Exception as exc:
        return ApiResult(ok=False, data=None, data_status="mock_fallback", error="", reason=_classify_request_error(exc))


def vworld_status() -> dict[str, str | bool]:
    configured = get_secret("VWORLD_API_KEY") not in (None, "")
    return {
        "configured": configured,
        "data_status": "configured" if configured else "missing",
        "message": "VWorld API Key 설정 상태만 확인합니다.",
    }


def get_data_go_kr_key() -> str | None:
    key = get_secret("DATA_GO_KR_SERVICE_KEY")
    return str(key) if key not in (None, "") else None


def data_go_kr_status() -> dict[str, str | bool]:
    configured = get_data_go_kr_key() not in (None, "")
    return {
        "configured": configured,
        "data_status": "configured" if configured else "missing",
        "message": "DATA_GO_KR_SERVICE_KEY 설정 상태만 확인합니다.",
    }


def _vworld_display_message(source: str) -> str:
    messages = {
        "vworld_search": "VWorld 장소 검색 API로 좌표를 확인했습니다.",
        "vworld_address_road": "VWorld 도로명주소 변환으로 좌표를 확인했습니다.",
        "vworld_address_parcel": "VWorld 지번주소 변환으로 좌표를 확인했습니다.",
        "fallback": "VWorld 실응답을 확인하지 못해 시연용 대체 좌표를 사용했습니다.",
    }
    return messages.get(source, messages["fallback"])


def _vworld_action_needed(status: str, reason_code: str) -> str:
    if status == "real_api":
        return "없음"
    if status == "missing_key":
        return "VWORLD_API_KEY Secret 등록 필요"
    if reason_code in {"connection_error", "network_error", "timeout", "ssl_error"}:
        return "VWorld API 키의 도메인/IP 허용 설정, 로컬 네트워크, VWorld 서비스 접속 가능 여부를 확인하세요."
    if reason_code in {"invalid_key", "incorrect_key", "unavailable_key"}:
        return "VWorld API 키 상태 확인 필요"
    if reason_code == "no_result":
        return "검색어 또는 주소 표기 확인 필요"
    if reason_code == "missing_input":
        return "검색어 또는 주소 입력 필요"
    return "VWorld 설정, 검색어, 주소 표기 확인 필요"


def _vworld_meta(status: str, reason_code: str, source: str = "fallback", **extra: str) -> dict[str, str]:
    meta = {
        "data_status": status,
        "status": status,
        "source": source,
        "reason": reason_code,
        "reason_code": reason_code,
        "action_needed": _vworld_action_needed(status, reason_code),
        "display_message": _vworld_display_message(source),
    }
    meta.update({key: str(value) for key, value in extra.items() if value not in (None, "")})
    return meta


def _classify_vworld_request_error(exc: Exception) -> str:
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.exceptions.SSLError):
        return "ssl_error"
    if isinstance(exc, requests.ConnectionError):
        return "connection_error"
    return "network_error"


def _classify_vworld_status(response: dict[str, Any], default: str = "no_result") -> str:
    body = response.get("response", {}) if isinstance(response, dict) else {}
    status = str(body.get("status", "")).upper()
    if status == "NOT_FOUND":
        return "no_result"
    if status == "ERROR":
        error = body.get("error", {})
        code = str(error.get("code", "")).upper()
        return {
            "INVALID_KEY": "invalid_key",
            "INCORRECT_KEY": "incorrect_key",
            "UNAVAILABLE_KEY": "unavailable_key",
            "OVER_REQUEST_LIMIT": "over_request_limit",
            "PARAM_REQUIRED": "param_required",
        }.get(code, "api_error")
    return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _call_vworld_json(endpoint: str, params: dict[str, Any], timeout: int = 8) -> tuple[dict[str, Any] | None, str]:
    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json(), ""
    except ValueError:
        return None, "parse_error"
    except Exception as exc:
        return None, _classify_vworld_request_error(exc)


def _search_vworld_place(query: str, api_key: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    params = {
        "service": "search",
        "request": "search",
        "version": "2.0",
        "crs": "EPSG:4326",
        "query": query,
        "type": "PLACE",
        "format": "json",
        "errorFormat": "json",
        "size": 10,
        "page": 1,
        "key": api_key,
    }
    data, error = _call_vworld_json(VWORLD_SEARCH_URL, params=params, timeout=8)
    if error:
        return None, _vworld_meta("mock_fallback", error, search_type="PLACE")

    response = data.get("response", {}) if isinstance(data, dict) else {}
    status = str(response.get("status", "")).upper()
    if status != "OK":
        return None, _vworld_meta("mock_fallback", _classify_vworld_status(data or {}), search_type="PLACE")

    items_container = response.get("result", {}).get("items", {})
    items = items_container.get("item") if isinstance(items_container, dict) else items_container
    for item in _as_list(items):
        if not isinstance(item, dict):
            continue
        point = item.get("point") or {}
        x = point.get("x")
        y = point.get("y")
        if x not in (None, "") and y not in (None, ""):
            return (
                {
                    "x": x,
                    "y": y,
                    "title": item.get("title", ""),
                    "road_address": (item.get("address") or {}).get("road", ""),
                    "parcel_address": (item.get("address") or {}).get("parcel", ""),
                },
                _vworld_meta("real_api", "place_search_ok", "vworld_search", search_type="PLACE"),
            )
    return None, _vworld_meta("mock_fallback", "no_coordinate", search_type="PLACE")


def _address_vworld_getcoord(query: str, api_key: str, address_type: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    normalized_type = address_type.upper()
    params = {
        "service": "address",
        "request": "GetCoord",
        "version": "2.0",
        "crs": "EPSG:4326",
        "address": query,
        "format": "json",
        "errorFormat": "json",
        "type": normalized_type,
        "refine": "true",
        "simple": "false",
        "key": api_key,
    }
    data, error = _call_vworld_json(VWORLD_ADDRESS_URL, params=params, timeout=8)
    source = "vworld_address_road" if normalized_type == "ROAD" else "vworld_address_parcel"
    if error:
        return None, _vworld_meta("mock_fallback", error, address_type_tried=normalized_type)

    response = data.get("response", {}) if isinstance(data, dict) else {}
    status = str(response.get("status", "")).upper()
    if status != "OK":
        return None, _vworld_meta("mock_fallback", _classify_vworld_status(data or {}), address_type_tried=normalized_type)

    point = response.get("result", {}).get("point") or {}
    x = point.get("x")
    y = point.get("y")
    if x not in (None, "") and y not in (None, ""):
        return (
            {"x": x, "y": y},
            _vworld_meta("real_api", f"address_{normalized_type.lower()}_ok", source, address_type_tried=normalized_type),
        )
    return None, _vworld_meta("mock_fallback", "no_coordinate", address_type_tried=normalized_type)


def geocode_vworld(address: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    query = (address or "").strip()
    if not query:
        return None, _vworld_meta("missing_input", "missing_input")

    api_key = str(get_secret("VWORLD_API_KEY", "") or "").strip()
    if not api_key:
        return None, _vworld_meta("missing_key", "missing_key")

    place_result, place_meta = _search_vworld_place(query, api_key)
    if place_result:
        return place_result, place_meta

    road_result, road_meta = _address_vworld_getcoord(query, api_key, "ROAD")
    if road_result:
        return road_result, road_meta

    parcel_result, parcel_meta = _address_vworld_getcoord(query, api_key, "PARCEL")
    if parcel_result:
        return parcel_result, parcel_meta

    final_reason = parcel_meta.get("reason_code") or road_meta.get("reason_code") or place_meta.get("reason_code") or "no_result"
    tried = ",".join(filter(None, [place_meta.get("search_type"), road_meta.get("address_type_tried"), parcel_meta.get("address_type_tried")]))
    return None, _vworld_meta("mock_fallback", final_reason, tried=tried)


def test_vworld_geocode_connection(address: str = "운양역") -> dict[str, Any]:
    geocode, meta = geocode_vworld(address)
    return {
        "ok": geocode is not None,
        "status": meta.get("data_status", "mock_fallback"),
        "source": meta.get("source", "fallback"),
        "reason": meta.get("reason", ""),
        "reason_code": meta.get("reason_code", ""),
        "has_coordinate": geocode is not None,
        "search_type": meta.get("search_type", ""),
        "address_type_tried": meta.get("address_type_tried", ""),
        "action_needed": meta.get("action_needed", _vworld_action_needed(meta.get("data_status", "mock_fallback"), meta.get("reason_code", ""))),
        "display_message": meta.get("display_message", _vworld_display_message("fallback")),
    }


def mock_coordinate(kind: str = "default_origin") -> dict[str, Any]:
    return dict(MOCK_COORDINATES.get(kind, MOCK_COORDINATES["default_origin"]))


def build_public_data_params(params: dict[str, Any] | None = None, json: bool = True) -> dict[str, Any]:
    built: dict[str, Any] = {}
    if params:
        built.update({key: value for key, value in params.items() if value not in (None, "")})
    built.setdefault("pageNo", 1)
    built.setdefault("numOfRows", 10)
    if json and not any(key in built for key in ("_type", "type", "resultType", "dataType")):
        built["_type"] = "json"
    service_key = get_data_go_kr_key()
    if service_key:
        built["serviceKey"] = service_key
    return built


def _find_first_key(data: Any, keys: set[str]) -> Any:
    if isinstance(data, dict):
        for key, value in data.items():
            if str(key).lower() in keys:
                return value
        for value in data.values():
            found = _find_first_key(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first_key(item, keys)
            if found is not None:
                return found
    return None


def _collect_items(data: Any) -> list[Any]:
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in {"item", "servlist"}:
                return value if isinstance(value, list) else [value]
        for key, value in data.items():
            if str(key).lower() in {"items", "body", "response", "data", "facinfolist"}:
                collected = _collect_items(value)
                if collected:
                    return collected
        return []
    if isinstance(data, list):
        return data
    return []


def _xml_element_to_obj(element: ET.Element) -> Any:
    children = list(element)
    if not children:
        return element.text.strip() if element.text else ""
    result: dict[str, Any] = {}
    for child in children:
        child_obj = _xml_element_to_obj(child)
        key = child.tag.split("}")[-1]
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(child_obj)
        else:
            result[key] = child_obj
    return result


def _parse_xml_to_dict_or_items(text: bytes | str) -> dict[str, Any]:
    root = ET.fromstring(text)
    return {_strip_namespace(root.tag): _xml_element_to_obj(root)}


def _strip_namespace(tag: str) -> str:
    return tag.split("}")[-1]


def _response_kind(response: requests.Response) -> str:
    if not response.content:
        return "empty"
    content_type = response.headers.get("content-type", "").lower()
    sample = response.content[:120].lstrip().lower()
    if "json" in content_type or sample.startswith(b"{") or sample.startswith(b"["):
        return "json"
    if "xml" in content_type or sample.startswith(b"<"):
        if b"<html" in sample:
            return "html"
        return "xml"
    if b"<html" in sample:
        return "html"
    return "text"


def _extract_header_code(normalized: dict[str, Any]) -> str:
    return str(normalized.get("result_code", "") or "")


def _extract_total_count(normalized: dict[str, Any]) -> int:
    return _safe_int(normalized.get("total_count"), 0)


def normalize_public_data_response(raw: Any, service_name: str = "") -> dict[str, Any]:
    try:
        parsed = _xml_element_to_obj(raw) if isinstance(raw, ET.Element) else raw
        result_code = _find_first_key(parsed, {"resultcode", "code", "returncode"})
        result_msg = _find_first_key(parsed, {"resultmsg", "resultmessage", "message", "returnmsg", "errmsg"})
        total_count = _find_first_key(parsed, {"totalcount", "total_count", "count"})
        items = [_clean_item(item) for item in _collect_items(parsed)]
        return {
            "service_name": service_name,
            "result_code": str(result_code or "").strip(),
            "result_message": _redact_public_data_error(result_msg),
            "items": items,
            "total_count": _safe_int(total_count, 0),
            "raw_type": type(parsed).__name__,
        }
    except Exception:
        return {
            "service_name": service_name,
            "result_code": "parse_error",
            "result_message": "parse_error",
            "items": [],
            "total_count": 0,
            "raw_type": "parse_error",
        }


def extract_public_data_items(normalized: dict[str, Any]) -> list[Any]:
    items = normalized.get("items", [])
    return items if isinstance(items, list) else []


def call_data_go_kr_api(
    endpoint: str,
    params: dict[str, Any] | None = None,
    service_name: str = "",
    timeout: int = 8,
    prefer_json: bool = True,
) -> dict[str, Any]:
    operation = _operation_name(endpoint)
    if not get_data_go_kr_key():
        return make_api_result(service_name, "missing_key", source="fallback", endpoint_name=operation, reason_code="missing_key")

    request_params = build_public_data_params(params, json=prefer_json)
    tried_param_set_name = str(request_params.pop("_param_set_name", "default"))
    try:
        response = requests.get(endpoint, params=request_params, timeout=timeout)
        kind = _response_kind(response)
        summary_base = {
            "http_status": response.status_code,
            "response_kind": kind,
            "operation_name": operation,
            "tried_param_set_name": tried_param_set_name,
        }
        if response.status_code >= 400:
            reason = classify_public_data_error(response)
            return make_api_result(
                service_name,
                reason if reason in {"timeout", "network_error", "parse_error"} else "api_error",
                source="fallback",
                endpoint_name=operation,
                reason_code=reason,
                summary=summary_base,
            )
        if kind == "empty":
            return make_api_result(service_name, "parse_error", source="fallback", endpoint_name=operation, reason_code="empty_response", summary=summary_base)
        if kind == "html":
            return make_api_result(service_name, "parse_error", source="fallback", endpoint_name=operation, reason_code="html_response", summary=summary_base)

        try:
            raw = response.json() if kind == "json" else _parse_xml_to_dict_or_items(response.content)
        except Exception:
            try:
                raw = _parse_xml_to_dict_or_items(response.content)
                kind = "xml"
            except Exception:
                return make_api_result(service_name, "parse_error", source="fallback", endpoint_name=operation, reason_code="parse_error", summary=summary_base)

        normalized = normalize_public_data_response(raw, service_name)
        items = extract_public_data_items(normalized)
        result_code = _extract_header_code(normalized)
        result_message = normalized.get("result_message", "")
        total_count = _extract_total_count(normalized)
        summary = {
            **summary_base,
            "response_kind": kind,
            "result_code": result_code,
            "result_msg_code": result_message,
            "item_count": len(items),
            "total_count": total_count,
        }
        if _is_no_data_code(result_code, result_message):
            return make_api_result(
                service_name,
                "real_api_no_data",
                items=[],
                source="public_data",
                endpoint_name=operation,
                reason_code="no_data",
                summary=summary,
            )
        if _is_success_code(result_code) and items:
            return make_api_result(
                service_name,
                "real_api",
                items=items,
                source="public_data",
                endpoint_name=operation,
                reason_code="normal",
                summary=summary,
            )
        if _is_success_code(result_code) and total_count == 0:
            return make_api_result(
                service_name,
                "real_api_no_data",
                items=[],
                source="public_data",
                endpoint_name=operation,
                reason_code="normal_no_data",
                summary=summary,
            )
        if not result_code and items:
            return make_api_result(
                service_name,
                "real_api",
                items=items,
                source="public_data",
                endpoint_name=operation,
                reason_code="items_without_code",
                summary=summary,
            )
        return make_api_result(
            service_name,
            "api_error",
            source="fallback",
            endpoint_name=operation,
            reason_code=result_code or "api_error",
            action_needed="요청 파라미터 또는 operation 확인",
            summary=summary,
        )
    except Exception as exc:
        reason = classify_public_data_error(exc)
        return make_api_result(
            service_name,
            reason if reason in {"timeout", "network_error", "parse_error"} else "api_error",
            source="fallback",
            endpoint_name=operation,
            reason_code=reason,
        )


def _call_param_sets(
    base: str,
    operation: str,
    service_name: str,
    param_sets: list[tuple[str, dict[str, Any], bool]],
    timeout: int = 8,
) -> dict[str, Any]:
    endpoint = _join_endpoint(base, operation)
    best: dict[str, Any] | None = None
    for name, params, prefer_json in param_sets:
        attempt_params = {**params, "_param_set_name": name}
        result = call_data_go_kr_api(endpoint, attempt_params, service_name=service_name, timeout=timeout, prefer_json=prefer_json)
        if result["status"] in {"real_api", "real_api_no_data"}:
            return result
        if best is None or _result_rank(result["status"]) > _result_rank(best["status"]):
            best = result
    return best or make_api_result(service_name, "api_error", source="fallback", endpoint_name=operation, reason_code="not_tried")


def _result_rank(status: str) -> int:
    order = {
        "real_api": 100,
        "real_api_no_data": 90,
        "missing_params": 50,
        "missing_key": 40,
        "timeout": 30,
        "network_error": 25,
        "parse_error": 20,
        "api_error": 10,
        "fallback": 0,
    }
    return order.get(status, 0)


def _keyword_filter(items: list[Any], keywords: tuple[str, ...]) -> list[Any]:
    if not keywords:
        return items
    return [item for item in items if any(keyword and keyword in str(item) for keyword in keywords)]


def _with_fallback(result: dict[str, Any], fallback_items: list[dict[str, Any]], fallback_message: str, action_needed: str = "") -> dict[str, Any]:
    if result["status"] in {"real_api", "real_api_no_data"}:
        return result
    return make_api_result(
        result["service_name"],
        result["status"],
        items=fallback_items,
        message=f"{result['message']} {fallback_message}",
        source="fallback",
        endpoint_name=result["endpoint_name"],
        fallback_count=len(fallback_items),
        reason_code=result.get("reason_code", result["status"]),
        action_needed=action_needed or result.get("action_needed", ""),
        summary=result.get("summary", {}),
    )


def _sports_facility_fallback() -> list[dict[str, Any]]:
    return [{"facility_name": "김포반다비체육센터", "area": "김포", "data_type": "fallback_sample", "note": "시설 API 실응답 확인 실패 시 표시되는 대체 샘플"}]


def _disabled_convenience_fallback() -> list[dict[str, Any]]:
    return [{"facility_name": "김포 접근성 편의시설 참고 샘플", "area": "김포", "data_type": "fallback_sample", "note": "장애인편의시설 API 실응답 확인 실패 시 표시되는 대체 샘플"}]


def _mobility_support_fallback() -> list[dict[str, Any]]:
    return [{"area": "김포", "candidate": "이동지원 후보 추천", "review": "운영기관 확인 필요", "availability": "이용 가능 여부 확인 필요", "data_type": "fallback_sample"}]


def _weather_fallback() -> list[dict[str, Any]]:
    return [{"category": "weather_summary", "summary": "기상 API 대체 응답: 현장 상태와 최신 예보 확인 필요", "route_impact": "주의", "data_type": "fallback_sample"}]


def _bus_arrival_fallback() -> list[dict[str, Any]]:
    return [{"service": "TAGO 버스도착정보", "status": "파라미터 확인 필요", "data_type": "fallback_sample"}]


def _bus_route_fallback() -> list[dict[str, Any]]:
    return [{"service": "TAGO 버스노선정보", "status": "파라미터 확인 필요", "data_type": "fallback_sample"}]


def fetch_sports_facilities(keyword: str = "김포", page_no: int = 1, num_of_rows: int = 10) -> dict[str, Any]:
    service_name = "전국체육시설 정보"
    param_sets = [
        ("gyeonggi_gimpo_city", {"pageNo": page_no, "numOfRows": num_of_rows, "resultType": "JSON", "cp_nm": "경기도", "cpb_nm": "김포시"}, False),
        ("gyeonggi_gimpo", {"pageNo": page_no, "numOfRows": num_of_rows, "resultType": "JSON", "cp_nm": "경기도", "cpb_nm": "김포"}, False),
        ("bandabi_name", {"pageNo": page_no, "numOfRows": num_of_rows, "resultType": "JSON", "faci_nm": "반다비"}, False),
        ("unfiltered", {"pageNo": page_no, "numOfRows": num_of_rows, "resultType": "JSON"}, False),
    ]
    result = _call_param_sets(SPORTS_FACILITY_URL, "TODZ_API_SFMS_FACI", service_name, param_sets)
    if result["status"] == "real_api" and keyword:
        filtered = _keyword_filter(result["items"], (keyword, "김포", "반다비"))
        if filtered:
            result = make_api_result(service_name, "real_api", items=filtered, source="public_data", endpoint_name=result["endpoint_name"], reason_code=result["reason_code"], summary=result["summary"])
    return _with_fallback(result, _sports_facility_fallback(), "대체 샘플입니다.", "cp_nm/cpb_nm 또는 시설명 파라미터 확인")


def fetch_sports_facility_detail(facility_id: str | None = None, facility_name: str = "김포반다비체육센터") -> dict[str, Any]:
    service_name = "공공체육시설 상세 정보"
    name = facility_name or "김포반다비체육센터"
    param_sets = [
        ("managed_gyeonggi_gimpo_city", {"pageNo": 1, "numOfRows": 10, "resultType": "JSON", "fmng_cp_nm": "경기도", "fmng_cpb_nm": "김포시"}, False),
        ("managed_gyeonggi_gimpo", {"pageNo": 1, "numOfRows": 10, "resultType": "JSON", "fmng_cp_nm": "경기도", "fmng_cpb_nm": "김포"}, False),
        ("facility_name", {"pageNo": 1, "numOfRows": 10, "resultType": "JSON", "faci_nm": name}, False),
        ("unfiltered", {"pageNo": 1, "numOfRows": 10, "resultType": "JSON"}, False),
    ]
    if facility_id:
        param_sets.insert(0, ("facility_id", {"pageNo": 1, "numOfRows": 10, "resultType": "JSON", "faci_id": facility_id}, False))
    result = _call_param_sets(SPORTS_FACILITY_DETAIL_URL, "TODZ_SFMS_FACIL_INFO", service_name, param_sets[:4])
    return _with_fallback(result, _sports_facility_fallback(), "대체 샘플입니다.", "fmng_cp_nm/fmng_cpb_nm 또는 시설명 파라미터 확인")


def fetch_disabled_convenience_facilities(keyword: str = "김포", page_no: int = 1, num_of_rows: int = 20) -> dict[str, Any]:
    service_name = "장애인편의시설 현황"
    param_sets = [
        ("gyeonggi_gimpo_city_xml", {"pageNo": page_no, "numOfRows": num_of_rows, "siDoNm": "경기도", "cggNm": "김포시"}, False),
        ("bandabi_facility_xml", {"pageNo": page_no, "numOfRows": num_of_rows, "faclNm": "반다비"}, False),
        ("unfiltered_xml", {"pageNo": page_no, "numOfRows": num_of_rows}, False),
    ]
    result = _call_param_sets(DISABLED_CONVENIENCE_URL, "getDisConvFaclList", service_name, param_sets)
    if result["status"] == "real_api" and keyword:
        filtered = _keyword_filter(result["items"], (keyword, "반다비"))
        if filtered:
            result = make_api_result(service_name, "real_api", items=filtered, source="public_data", endpoint_name=result["endpoint_name"], reason_code=result["reason_code"], summary=result["summary"])
    return _with_fallback(result, _disabled_convenience_fallback(), "대체 샘플입니다.", "XML operation 또는 지역 파라미터 확인")


def fetch_disabled_convenience_eval_info(wfclt_id: str | None = None) -> dict[str, Any]:
    service_name = "장애인편의시설 기구표목록"
    if not wfclt_id:
        return make_api_result(service_name, "real_api_no_data", source="public_data", endpoint_name="getFacInfoOpenApiJpEvalInfoList", reason_code="not_attempted_no_wfcltId", action_needed="wfcltId 확보 시 상세조회 가능")
    result = _call_param_sets(
        DISABLED_CONVENIENCE_URL,
        "getFacInfoOpenApiJpEvalInfoList",
        service_name,
        [("wfclt_id_xml", {"wfcltId": wfclt_id}, False)],
    )
    return result


def fetch_mobility_support_realtime(area: str = "김포", page_no: int = 1, num_of_rows: int = 10) -> dict[str, Any]:
    service_name = "교통약자 이동지원 실시간 정보"
    use_result = _call_param_sets(
        MOBILITY_SUPPORT_URL,
        "info_vehicle_use_v2",
        service_name,
        [
            ("gimpo_stdg_json", {"pageNo": page_no, "numOfRows": num_of_rows, "type": "JSON", "stdgCd": GIMPO_STDG_CD}, False),
            ("gimpo_area_json", {"pageNo": page_no, "numOfRows": num_of_rows, "type": "JSON", "area": area, "stdgCd": GIMPO_STDG_CD}, False),
        ],
    )
    if use_result["status"] in {"real_api", "real_api_no_data"}:
        center = _call_param_sets(
            MOBILITY_SUPPORT_URL,
            "center_info_v2",
            "교통약자 이동지원 센터 정보",
            [("center_gimpo_json", {"pageNo": 1, "numOfRows": 10, "type": "JSON", "stdgCd": GIMPO_STDG_CD}, False)],
        )
        vehicle = _call_param_sets(
            MOBILITY_SUPPORT_URL,
            "info_vehicle_v2",
            "교통약자 이동지원 차량 정보",
            [("vehicle_gimpo_json", {"pageNo": 1, "numOfRows": 10, "type": "JSON", "stdgCd": GIMPO_STDG_CD}, False)],
        )
        use_result["summary"] = {
            **use_result.get("summary", {}),
            "center_status": center["status"],
            "center_real_count": center["real_count"],
            "vehicle_status": vehicle["status"],
            "vehicle_real_count": vehicle["real_count"],
            "center_items": center.get("items", [])[:3],
            "vehicle_items": vehicle.get("items", [])[:3],
        }
        return use_result
    return _with_fallback(use_result, _mobility_support_fallback(), "대체 샘플입니다.", "stdgCd 또는 operation 응답 상태 확인")


def _safe_weather_base_time(now: datetime | None = None) -> tuple[str, str]:
    target = (now or datetime.now()) - timedelta(minutes=45)
    base_times = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
    current = target.strftime("%H%M")
    selected = None
    for base in base_times:
        if current >= base:
            selected = base
    if selected is None:
        target = target - timedelta(days=1)
        selected = "2300"
    return target.strftime("%Y%m%d"), selected


def fetch_weather_short_forecast(nx: int = 55, ny: int = 128, base_date: str | None = None, base_time: str | None = None) -> dict[str, Any]:
    service_name = "기상청 단기예보"
    safe_date, safe_time = _safe_weather_base_time()
    params = {
        "pageNo": 1,
        "numOfRows": 50,
        "dataType": "JSON",
        "base_date": base_date or safe_date,
        "base_time": base_time or safe_time,
        "nx": nx,
        "ny": ny,
    }
    result = call_data_go_kr_api(_join_endpoint(WEATHER_URL, "getVilageFcst"), params=params, service_name=service_name, timeout=8, prefer_json=False)
    if result["status"] in {"real_api", "real_api_no_data"}:
        result["summary"] = {**result.get("summary", {}), "weather_summary": summarize_weather_items(result["items"])}
        result["message"] = sanitize_public_claims(result["summary"]["weather_summary"])
        return result
    fallback = _with_fallback(result, _weather_fallback(), "기상청 단기예보 대체 샘플입니다.", "base_date/base_time 또는 API 운영 상태 확인")
    fallback["summary"] = {**fallback.get("summary", {}), "weather_summary": _weather_fallback()[0]["summary"]}
    return fallback


def summarize_weather_items(items: list[Any]) -> str:
    if not items:
        return "기상 항목이 비어 있습니다. 현장 상태 확인이 필요합니다."
    categories: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            category = str(item.get("category", ""))
            if category and category not in categories:
                categories[category] = item.get("fcstValue", item.get("obsrValue", ""))
    parts = []
    for key in ("SKY", "PTY", "TMP", "POP", "WSD"):
        if key in categories:
            parts.append(f"{key}={categories[key]}")
    return "기상 API 참고 요약: " + (", ".join(parts) if parts else "세부 항목 확인 필요")


def _first_value(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    lower_map = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        value = lower_map.get(key.lower())
        if value not in (None, ""):
            return str(value)
    return None


def fetch_tago_city_codes() -> dict[str, Any]:
    return _call_param_sets(
        BUS_ROUTE_URL,
        "getCtyCodeList",
        "TAGO 도시코드목록",
        [
            ("city_codes_json", {"pageNo": 1, "numOfRows": 200, "_type": "json"}, False),
            ("city_codes_xml", {"pageNo": 1, "numOfRows": 200, "_type": "xml"}, False),
        ],
    )


def find_tago_city_code(keyword: str = "김포", city_code_override: str | None = None) -> tuple[str | None, dict[str, Any]]:
    if city_code_override:
        return city_code_override, make_api_result("TAGO 도시코드목록", "real_api", items=[{"citycode": city_code_override}], source="public_data", endpoint_name="manual_cityCode", reason_code="manual_input")
    result = fetch_tago_city_codes()
    if result["status"] != "real_api":
        return None, result
    for item in result["items"]:
        if isinstance(item, dict) and keyword in str(item):
            city_code = _first_value(item, ("citycode", "cityCode", "cityCd"))
            if city_code:
                return city_code, result
    return None, make_api_result("TAGO 도시코드목록", "real_api_no_data", source="public_data", endpoint_name="getCtyCodeList", reason_code="no_city_code", action_needed="cityCode 직접 입력")


def fetch_tago_route_no_list(city_code: str | None, route_no: str = DEFAULT_TAGO_ROUTE_NO) -> dict[str, Any]:
    service_name = "TAGO 버스노선번호목록"
    if not city_code or not route_no:
        return make_api_result(service_name, "missing_params", items=_bus_route_fallback(), source="fallback", endpoint_name="getRouteNoList", fallback_count=1, reason_code="missing_cityCode_or_routeNo", action_needed="cityCode와 routeNo 필요")
    result = _call_param_sets(
        BUS_ROUTE_URL,
        "getRouteNoList",
        service_name,
        [
            ("route_no_json", {"pageNo": 1, "numOfRows": 20, "_type": "json", "cityCode": city_code, "routeNo": route_no}, False),
            ("route_no_xml", {"pageNo": 1, "numOfRows": 20, "_type": "xml", "cityCode": city_code, "routeNo": route_no}, False),
        ],
    )
    return result


def fetch_tago_route_stations(city_code: str | None, route_id: str | None) -> dict[str, Any]:
    service_name = "TAGO 노선경유정류소"
    if not city_code or not route_id:
        return make_api_result(service_name, "missing_params", source="fallback", endpoint_name="getRouteAcctoThrghSttnList", reason_code="missing_cityCode_or_routeId", action_needed="routeId 필요")
    return _call_param_sets(
        BUS_ROUTE_URL,
        "getRouteAcctoThrghSttnList",
        service_name,
        [
            ("route_stations_json", {"pageNo": 1, "numOfRows": 50, "_type": "json", "cityCode": city_code, "routeId": route_id}, False),
            ("route_stations_xml", {"pageNo": 1, "numOfRows": 50, "_type": "xml", "cityCode": city_code, "routeId": route_id}, False),
        ],
    )


def fetch_tago_route_info(city_code: str | None, route_id: str | None) -> dict[str, Any]:
    service_name = "TAGO 노선상세정보"
    if not city_code or not route_id:
        return make_api_result(service_name, "missing_params", source="fallback", endpoint_name="getRouteInfoIem", reason_code="missing_cityCode_or_routeId", action_needed="routeId 필요")
    return _call_param_sets(
        BUS_ROUTE_URL,
        "getRouteInfoIem",
        service_name,
        [
            ("route_info_json", {"pageNo": 1, "numOfRows": 10, "_type": "json", "cityCode": city_code, "routeId": route_id}, False),
            ("route_info_xml", {"pageNo": 1, "numOfRows": 10, "_type": "xml", "cityCode": city_code, "routeId": route_id}, False),
        ],
    )


def fetch_bus_route(city_code: str | None = None, route_id: str | None = None, route_no: str | None = DEFAULT_TAGO_ROUTE_NO) -> dict[str, Any]:
    service_name = "TAGO 버스노선정보"
    selected_city_code, city_result = find_tago_city_code("김포", city_code)
    if not selected_city_code:
        return _with_fallback(city_result, _bus_route_fallback(), "대체 샘플입니다.", "cityCode 직접 입력")
    selected_route_id = route_id
    route_list = None
    if not selected_route_id:
        route_list = fetch_tago_route_no_list(selected_city_code, route_no or DEFAULT_TAGO_ROUTE_NO)
        if route_list["status"] != "real_api":
            if route_list["status"] == "real_api_no_data":
                return route_list
            return _with_fallback(route_list, _bus_route_fallback(), "대체 샘플입니다.", "routeNo 또는 cityCode 확인")
        for item in route_list["items"]:
            if isinstance(item, dict):
                selected_route_id = _first_value(item, ("routeid", "routeId", "routeID"))
                if selected_route_id:
                    break
        if not selected_route_id:
            return make_api_result(service_name, "real_api_no_data", source="public_data", endpoint_name="getRouteNoList", reason_code="no_route_id", action_needed="routeNo 또는 routeId 확인")

    stations = fetch_tago_route_stations(selected_city_code, selected_route_id)
    route_info = fetch_tago_route_info(selected_city_code, selected_route_id)
    representative = route_list if route_list and route_list["status"] in {"real_api", "real_api_no_data"} else route_info
    if representative["status"] in {"real_api", "real_api_no_data"}:
        representative["service_name"] = service_name
        representative["summary"] = {
            **representative.get("summary", {}),
            "city_code_status": city_result["status"],
            "city_code": selected_city_code,
            "route_no": route_no or "",
            "route_id_found": bool(selected_route_id),
            "route_id_source": "manual" if route_id else "route_no_list",
            "stations_status": stations["status"],
            "stations_real_count": stations["real_count"],
            "route_info_status": route_info["status"],
            "route_info_real_count": route_info["real_count"],
        }
        return representative
    return _with_fallback(representative, _bus_route_fallback(), "대체 샘플입니다.", "routeId 기반 노선 상세 operation 확인")


def fetch_tago_arrivals_by_station(city_code: str | None, node_id: str | None) -> dict[str, Any]:
    service_name = "TAGO 버스도착정보"
    if not city_code or not node_id:
        return make_api_result(service_name, "missing_params", items=_bus_arrival_fallback(), source="fallback", endpoint_name="getSttnAcctoArvlPrearngeInfoList", fallback_count=1, reason_code="missing_cityCode_or_nodeId", action_needed="cityCode와 nodeId 필요")
    return _call_param_sets(
        BUS_ARRIVAL_URL,
        "getSttnAcctoArvlPrearngeInfoList",
        service_name,
        [
            ("arrival_station_json", {"pageNo": 1, "numOfRows": 20, "_type": "json", "cityCode": city_code, "nodeId": node_id}, False),
            ("arrival_station_xml", {"pageNo": 1, "numOfRows": 20, "_type": "xml", "cityCode": city_code, "nodeId": node_id}, False),
        ],
    )


def fetch_tago_arrivals_by_station_and_route(city_code: str | None, node_id: str | None, route_id: str | None) -> dict[str, Any]:
    service_name = "TAGO 버스도착정보"
    if not city_code or not node_id or not route_id:
        return make_api_result(service_name, "missing_params", items=_bus_arrival_fallback(), source="fallback", endpoint_name="getSttnAcctoSpcifyRouteBusArvlPrearngeInfoList", fallback_count=1, reason_code="missing_cityCode_nodeId_or_routeId", action_needed="cityCode, nodeId, routeId 필요")
    return _call_param_sets(
        BUS_ARRIVAL_URL,
        "getSttnAcctoSpcifyRouteBusArvlPrearngeInfoList",
        service_name,
        [
            ("arrival_route_json", {"pageNo": 1, "numOfRows": 20, "_type": "json", "cityCode": city_code, "nodeId": node_id, "routeId": route_id}, False),
            ("arrival_route_xml", {"pageNo": 1, "numOfRows": 20, "_type": "xml", "cityCode": city_code, "nodeId": node_id, "routeId": route_id}, False),
        ],
    )


def fetch_bus_arrival(city_code: str | None = None, node_id: str | None = None, route_id: str | None = None, route_no: str | None = DEFAULT_TAGO_ROUTE_NO) -> dict[str, Any]:
    if city_code and node_id and route_id:
        result = fetch_tago_arrivals_by_station_and_route(city_code, node_id, route_id)
        return _with_fallback(result, _bus_arrival_fallback(), "대체 샘플입니다.", "cityCode/nodeId/routeId 확인")
    if city_code and node_id:
        result = fetch_tago_arrivals_by_station(city_code, node_id)
        return _with_fallback(result, _bus_arrival_fallback(), "대체 샘플입니다.", "cityCode/nodeId 확인")

    selected_city_code, city_result = find_tago_city_code("김포", city_code)
    if not selected_city_code:
        return _with_fallback(city_result, _bus_arrival_fallback(), "대체 샘플입니다.", "cityCode 직접 입력")

    selected_route_id = route_id
    if not selected_route_id:
        route_list = fetch_tago_route_no_list(selected_city_code, route_no or DEFAULT_TAGO_ROUTE_NO)
        if route_list["status"] == "real_api":
            for item in route_list["items"]:
                if isinstance(item, dict):
                    selected_route_id = _first_value(item, ("routeid", "routeId", "routeID"))
                    if selected_route_id:
                        break
        elif route_list["status"] == "real_api_no_data":
            return make_api_result("TAGO 버스도착정보", "real_api_no_data", source="public_data", endpoint_name="getRouteNoList", reason_code="no_route_id", action_needed="routeNo 또는 routeId 확인")

    if not selected_route_id:
        return make_api_result("TAGO 버스도착정보", "missing_params", items=_bus_arrival_fallback(), source="fallback", endpoint_name="getSttnAcctoArvlPrearngeInfoList", fallback_count=1, reason_code="no_route_id", action_needed="routeId 또는 nodeId 직접 입력")

    stations = fetch_tago_route_stations(selected_city_code, selected_route_id)
    selected_node_id = node_id
    if stations["status"] == "real_api":
        for item in stations["items"]:
            if isinstance(item, dict):
                selected_node_id = _first_value(item, ("nodeid", "nodeId", "nodeID"))
                if selected_node_id:
                    break
    elif stations["status"] == "real_api_no_data":
        return make_api_result("TAGO 버스도착정보", "real_api_no_data", source="public_data", endpoint_name="getRouteAcctoThrghSttnList", reason_code="no_node_id", action_needed="nodeId 직접 입력")

    if not selected_node_id:
        return make_api_result("TAGO 버스도착정보", "missing_params", items=_bus_arrival_fallback(), source="fallback", endpoint_name="getSttnAcctoArvlPrearngeInfoList", fallback_count=1, reason_code="missing_nodeId", action_needed="nodeId 직접 입력")

    arrival = fetch_tago_arrivals_by_station(selected_city_code, selected_node_id)
    arrival["summary"] = {
        **arrival.get("summary", {}),
        "city_code": selected_city_code,
        "route_no": route_no or "",
        "route_id_found": bool(selected_route_id),
        "node_id_found": bool(selected_node_id),
        "stations_status": stations["status"],
        "stations_real_count": stations["real_count"],
    }
    return _with_fallback(arrival, _bus_arrival_fallback(), "대체 샘플입니다.", "도착정보 operation 또는 정류소 파라미터 확인")


def fetch_weather_stub() -> dict[str, Any]:
    return make_api_result("날씨 API stub", "fallback", items=_weather_fallback(), source="fallback", endpoint_name="weather_stub", fallback_count=1)


def fetch_bus_stub() -> dict[str, Any]:
    return make_api_result("버스 API stub", "fallback", items=_bus_arrival_fallback(), source="fallback", endpoint_name="bus_stub", fallback_count=1)


def fetch_public_facility_stub() -> dict[str, Any]:
    return make_api_result("공공시설 API stub", "fallback", items=_sports_facility_fallback(), source="fallback", endpoint_name="public_facility_stub", fallback_count=1)
