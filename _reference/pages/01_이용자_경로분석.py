from __future__ import annotations

from datetime import time

import pandas as pd
import streamlit as st

from modules.api_clients import fetch_weather_short_forecast, geocode_vworld, mock_coordinate
from modules.safety import get_disclaimer, sanitize_public_claims
from modules.scoring import calculate_viable_path_score
from modules.ui_components import (
    inject_global_styles,
    render_app_header,
    render_disclaimer_box,
    render_info_card,
    render_metric_card,
    render_page_footer_note,
    render_section_header,
    render_status_badge,
    render_warning_box,
)


st.set_page_config(page_title="이용자 경로분석", page_icon="🧭", layout="wide")
inject_global_styles()


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def resolve_coordinate(address: str, fallback_kind: str) -> dict:
    geocode, meta = geocode_vworld(address)
    if geocode:
        try:
            return {
                "lat": float(geocode["y"]),
                "lon": float(geocode["x"]),
                "label": address,
                "data_status": meta.get("data_status", "real_api"),
                "source": meta.get("source", ""),
                "reason": meta.get("reason", ""),
                "reason_code": meta.get("reason_code", ""),
                "search_type": meta.get("search_type", ""),
                "address_type_tried": meta.get("address_type_tried", ""),
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
        "reason": meta.get("reason", "mock_coordinate"),
        "reason_code": meta.get("reason_code", meta.get("reason", "mock_coordinate")),
        "search_type": meta.get("search_type", ""),
        "address_type_tried": meta.get("address_type_tried", ""),
        "display_message": meta.get("display_message", "VWorld 실응답을 확인하지 못해 시연용 대체 좌표를 사용했습니다."),
    }


def render_reference_map(origin: dict, destination: dict) -> None:
    try:
        import folium
        from streamlit_folium import st_folium

        center = [(origin["lat"] + destination["lat"]) / 2, (origin["lon"] + destination["lon"]) / 2]
        fmap = folium.Map(location=center, zoom_start=12, control_scale=True)
        folium.Marker(
            [origin["lat"], origin["lon"]],
            tooltip=s("출발지 참고 위치"),
            popup=s(f"출발지: {origin['label']}"),
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(fmap)
        folium.Marker(
            [destination["lat"], destination["lon"]],
            tooltip=s("목적지 참고 위치"),
            popup=s(f"목적지: {destination['label']}"),
            icon=folium.Icon(color="green", icon="flag"),
        ).add_to(fmap)
        folium.PolyLine(
            [[origin["lat"], origin["lon"]], [destination["lat"], destination["lon"]]],
            color="#38bdf8",
            weight=3,
            opacity=0.75,
            dash_array="8",
            tooltip=s("참고 좌표 연결선"),
        ).add_to(fmap)
        st_folium(fmap, height=440, use_container_width=True, key="route_reference_map", returned_objects=[])
    except Exception:
        try:
            st.map(
                pd.DataFrame(
                    [
                        {"lat": origin["lat"], "lon": origin["lon"]},
                        {"lat": destination["lat"], "lon": destination["lon"]},
                    ]
                ),
                latitude="lat",
                longitude="lon",
                width="stretch",
            )
        except Exception:
            st.write(s(f"출발지 좌표: {origin['lat']}, {origin['lon']}"))
            st.write(s(f"목적지 좌표: {destination['lat']}, {destination['lon']}"))


def load_weather_if_enabled(enabled: bool) -> dict:
    if not enabled:
        return {
            "status": "disabled",
            "data_status": "disabled",
            "source": "disabled",
            "real_count": 0,
            "fallback_count": 0,
            "summary": {"weather_summary": "날씨 영향 반영을 선택하지 않았습니다."},
            "message": "날씨 영향 반영을 선택하지 않았습니다.",
            "items": [],
        }
    return fetch_weather_short_forecast()


def weather_summary_text(weather_result: dict) -> str:
    summary = weather_result.get("summary", {})
    if isinstance(summary, dict):
        return s(summary.get("weather_summary", weather_result.get("message", "fallback")))
    return s(summary or weather_result.get("message", "fallback"))


def store_route_result(inputs: dict) -> None:
    origin_coord = resolve_coordinate(inputs["origin"], "default_origin")
    destination_coord = resolve_coordinate(inputs["destination"], "default_destination")
    weather_result = load_weather_if_enabled(bool(inputs.get("weather_enabled")))
    score_inputs = {
        **inputs,
        "origin_geocode_status": origin_coord["data_status"],
        "destination_geocode_status": destination_coord["data_status"],
        "weather_api_status": weather_result.get("status", "fallback"),
    }
    st.session_state["route_analysis_result"] = {
        "inputs": inputs,
        "origin_coord": origin_coord,
        "destination_coord": destination_coord,
        "weather_result": weather_result,
        "score_result": calculate_viable_path_score(score_inputs),
        "show_map": True,
    }


def render_route_result(saved: dict) -> None:
    origin_coord = saved["origin_coord"]
    destination_coord = saved["destination_coord"]
    result = saved["score_result"]
    inputs = saved["inputs"]
    weather_result = saved.get("weather_result", {})
    weather_status = str(weather_result.get("status", weather_result.get("data_status", "fallback")))

    render_section_header("MAP", "참고 지도", f"{inputs['origin'] or '출발지 미입력'} → {inputs['destination'] or '목적지 미입력'}", "지도")
    render_info_card(
        "참고 좌표 기반 시각화",
        "아래 지도는 실제 보행 경로가 아닌 참고 좌표 기반 시각화입니다. 장소명은 VWorld 장소 검색 API를 우선 사용하고, 주소형 입력은 주소 변환 API를 사용합니다. 검색 실패 시 시연용 대체 좌표를 사용할 수 있습니다.",
        status="info",
    )
    render_reference_map(origin_coord, destination_coord)
    render_disclaimer_box("실제 보행 경로가 아닌 참고 좌표 기반 시각화입니다. 좌표는 참고용이며 실제 현장 위치 검증과 운영기관 안내 확인이 필요합니다.")
    if origin_coord.get("data_status") != "real_api" or destination_coord.get("data_status") != "real_api":
        render_warning_box("VWorld 주소 변환 API가 일시적으로 응답하지 않아 시연용 대체 좌표를 사용했을 수 있습니다. 실제 현장 위치 확인이 필요합니다.")

    col_score, col_level, col_source, col_weather = st.columns(4)
    with col_score:
        render_metric_card("접근성 점수", f"{result['score']} / 100", "공공데이터와 입력값 기반 참고 점수", "success")
    with col_level:
        render_metric_card("등급", s(result["mobility_level"]), s(result["ai_name"]), "purple")
    with col_source:
        coord_status = f"{origin_coord['data_status']} / {destination_coord['data_status']}"
        coord_status_style = "success" if origin_coord["data_status"] == "real_api" and destination_coord["data_status"] == "real_api" else "warning"
        render_metric_card("좌표 상태", coord_status, "origin / destination", coord_status_style)
    with col_weather:
        render_metric_card(
            "기상 API",
            weather_status,
            f"real={weather_result.get('real_count', 0)} 대체={weather_result.get('fallback_count', 0)}",
            "success" if weather_status == "real_api" else "warning",
        )
    render_status_badge(f"기상 요약: {weather_summary_text(weather_result)}", "success" if weather_status == "real_api" else "warning")
    coord_rows = [
        {
            "구분": "출발지",
            "status": origin_coord.get("data_status", ""),
            "source": origin_coord.get("source", ""),
            "reason_code": origin_coord.get("reason_code", ""),
            "search_type": origin_coord.get("search_type", ""),
            "address_type_tried": origin_coord.get("address_type_tried", ""),
            "message": origin_coord.get("display_message", ""),
        },
        {
            "구분": "목적지",
            "status": destination_coord.get("data_status", ""),
            "source": destination_coord.get("source", ""),
            "reason_code": destination_coord.get("reason_code", ""),
            "search_type": destination_coord.get("search_type", ""),
            "address_type_tried": destination_coord.get("address_type_tried", ""),
            "message": destination_coord.get("display_message", ""),
        },
    ]
    st.dataframe(pd.DataFrame(coord_rows), width="stretch")

    render_section_header("SCORE", "주요 사유", "점수 항목과 확인 필요 사항입니다.")
    st.dataframe(pd.DataFrame([{"항목": key, "점수": value} for key, value in result["item_scores"].items()]), width="stretch")

    cols = st.columns(2)
    with cols[0]:
        render_section_header("RISK", "확인 필요 요인")
        for item in result["risk_factors"]:
            render_warning_box(s(item))
    with cols[1]:
        render_section_header("ACTION", "권장 확인")
        for item in result["recommended_actions"]:
            render_info_card("확인 항목", s(item), status="success")

    render_disclaimer_box(s(result["explanation"]))


render_app_header(
    "이용자 경로분석",
    "출발지와 목적지의 참고 위치, 접근성 점수, 기상 API 상태, 확인 필요 사항을 함께 표시합니다.",
    "B2C",
)
render_disclaimer_box(get_disclaimer("mobility"))
render_disclaimer_box("장소명은 VWorld 장소 검색 API를 우선 사용하고, 주소형 입력은 주소 변환 API를 사용합니다. 검색 실패 시 시연용 대체 좌표를 사용할 수 있습니다.")

with st.form("route_form"):
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input(s("출발지"), placeholder=s("예: 운양역, 경기도 김포시 사우중로 1"))
        use_date = st.date_input(s("이용 희망일"))
        support_type = st.selectbox(
            s("접근성 지원 필요 유형"),
            [
                s("휠체어 또는 보행 보조 필요"),
                s("음성 안내 또는 유도 동선 필요"),
                s("단계별 안내 또는 보호자·동행 지원 필요"),
                s("일반"),
            ],
        )
        mobility_needed = st.checkbox(s("이동지원 필요 여부"), value=False)
        weather_enabled = st.checkbox(s("날씨 영향 반영 여부"), value=True)
    with col2:
        destination = st.text_input(s("목적지"), value=s("김포반다비체육센터"))
        use_time = st.time_input(s("이용 희망 시간"), value=time(10, 0))
        companion_needed = st.checkbox(s("동행 필요 여부"), value=False)
        public_transport_available = st.checkbox(s("대중교통 이용 가능 여부"), value=True)

    submitted = st.form_submit_button(s("경로 참고 분석"))

if submitted:
    store_route_result(
        {
            "origin": origin,
            "destination": destination,
            "use_date": str(use_date),
            "use_time": str(use_time),
            "accessibility_support_type": support_type,
            "mobility_support_needed": mobility_needed,
            "companion_needed": companion_needed,
            "weather_enabled": weather_enabled,
            "public_transport_available": public_transport_available,
        }
    )

saved_result = st.session_state.get("route_analysis_result")
if saved_result and saved_result.get("show_map"):
    render_route_result(saved_result)
else:
    render_warning_box("입력값을 작성한 뒤 경로 참고 분석을 실행하세요.")

render_page_footer_note()
