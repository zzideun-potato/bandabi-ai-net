from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.api_clients import (
    DEFAULT_TAGO_ROUTE_NO,
    data_go_kr_status,
    fetch_bus_arrival,
    fetch_bus_route,
    fetch_disabled_convenience_facilities,
    fetch_mobility_support_realtime,
    fetch_public_facility_stub,
    fetch_sports_facilities,
    fetch_sports_facility_detail,
    fetch_weather_short_forecast,
    fetch_weather_stub,
    test_vworld_geocode_connection,
    vworld_status,
)
from modules.config import list_config_status
from modules.data_loader import load_csv_inventory, load_low_floor_bus_data, load_mobility_center_data, load_protected_zone_data
from modules.emailer import email_status
from modules.llm_client import test_openrouter_text_connection
from modules.safety import DATA_FALLBACK_NOTICE, get_disclaimer, sanitize_public_claims
from modules.scoring import calculate_viable_path_score
from modules.ui_components import (
    inject_global_styles,
    render_app_header,
    render_disclaimer_box,
    render_metric_card,
    render_page_footer_note,
    render_section_header,
    render_status_badge,
    render_warning_box,
)
from modules.vision import test_vision_model_available, vision_status
from modules.voice import voice_status


st.set_page_config(page_title="B2G 대시보드", page_icon="📊", layout="wide")
inject_global_styles()


def s(text: Any) -> str:
    return sanitize_public_claims(str(text))


def folder_status(path: str, pattern: str = "*") -> dict[str, str | int]:
    base = Path(path)
    if not base.exists() or not base.is_dir():
        return {"folder": path, "status": "empty", "count": 0}
    try:
        return {"folder": path, "status": "available", "count": len([item for item in base.glob(pattern) if item.is_file()])}
    except Exception:
        return {"folder": path, "status": "mock_fallback", "count": 0}


def status_style(status: str) -> str:
    if status in {"configured", "enabled_ready", "loaded", "real_api", "real_csv"}:
        return "success"
    if status in {"real_api_no_data", "disabled", "fallback", "mock_fallback", "missing_model", "missing_params", "missing_key"}:
        return "warning"
    if status in {"missing", "missing_config", "empty", "api_error", "timeout", "network_error", "parse_error"}:
        return "danger"
    return "muted"


def public_api_result_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "service_name": result.get("service_name", ""),
            "status": result.get("status", ""),
            "real_count": result.get("real_count", 0),
            "fallback_count": result.get("fallback_count", 0),
            "source": result.get("source", ""),
            "reason_code": result.get("reason_code", ""),
            "action_needed": result.get("action_needed", ""),
        }
        for result in results
    ]


def run_public_data_api_checks(city_code: str, node_id: str, route_id: str, route_no: str) -> list[dict[str, Any]]:
    city = city_code.strip() or None
    node = node_id.strip() or None
    route = route_id.strip() or None
    route_number = route_no.strip() or DEFAULT_TAGO_ROUTE_NO
    return [
        fetch_sports_facilities(keyword="김포"),
        fetch_sports_facility_detail(facility_name="김포반다비체육센터"),
        fetch_disabled_convenience_facilities(keyword="김포"),
        fetch_mobility_support_realtime(area="김포"),
        fetch_weather_short_forecast(),
        fetch_bus_arrival(city_code=city, node_id=node, route_id=route, route_no=route_number),
        fetch_bus_route(city_code=city, route_id=route, route_no=route_number),
    ]


def render_chart(frame: pd.DataFrame) -> None:
    try:
        import plotly.express as px

        fig = px.bar(frame, x="metric", y="value", color="status", text="value", title=s("파일럿 운영 참고 차트"))
        fig.update_layout(showlegend=True, height=420, paper_bgcolor="#0f172a", plot_bgcolor="#111c33", font_color="#e5edf7")
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.bar_chart(frame.set_index("metric")["value"])


render_app_header(
    "B2G 운영 참고 대시보드",
    "Secrets, RAG, CSV, 공공데이터 API 7종 상태를 파일럿 기준으로 점검합니다.",
    "B2G",
)
render_disclaimer_box(get_disclaimer("general"))
render_disclaimer_box(DATA_FALLBACK_NOTICE)

rag_index = rag_bm25.build_index("docs")
inventory = load_csv_inventory()
config_status = list_config_status()
mobility = load_mobility_center_data()
protected_zone = load_protected_zone_data()
low_floor_bus = load_low_floor_bus_data()
weather_stub = fetch_weather_stub()
facility_stub = fetch_public_facility_stub()
vision = vision_status()
voice = voice_status()
email = email_status()
vworld = vworld_status()
data_go = data_go_kr_status()

sample_scores = [
    calculate_viable_path_score({"destination": "김포반다비체육센터", "public_transport_available": True})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "mobility_support_needed": True, "public_transport_available": False})["score"],
    calculate_viable_path_score({"destination": "김포반다비체육센터", "accessibility_support_type": "휠체어 또는 보행 보조 필요"})["score"],
]
average_score = round(sum(sample_scores) / len(sample_scores), 1)
configured_count = sum(1 for status in config_status.values() if status in {"configured", "enabled"})

render_section_header("KPI", "파일럿 KPI 카드", "표시된 운영 지표는 파일럿 시연용 점검 수치입니다.")
kpi_cards = [
    ("RAG 문서", rag_index.data_status, f"chunks={len(rag_index.chunks)}", "info"),
    ("CSV 파일", len(inventory), "탐색된 파일 수", "success" if not inventory.empty else "warning"),
    ("Secrets 상태", f"{configured_count}/{len(config_status)}", "값 미표시", "purple"),
    ("이동 가능성 평균", average_score, "파일럿 지표", "warning"),
]
cols = st.columns(4)
for col, (label, value, helper, status) in zip(cols, kpi_cards):
    with col:
        render_metric_card(label, value, helper, status)

render_status_badge("파일럿 상태 점검", "info")
render_status_badge("시연용 점검 지표 포함", "warning")
render_status_badge("키 값 미표시", "success")
render_warning_box("표시된 운영 지표는 파일럿 시연용 점검 수치입니다. 실제 운영 통계가 아닌 MVP 검증용 지표입니다.")

render_section_header("SECRETS QA", "Secrets 기반 QA 상태", "실제 키 값, 일부 마스킹 값, 길이 정보는 표시하지 않습니다.")
text_model_status = "configured" if config_status.get("OPENROUTER_API_KEY") == "configured" and config_status.get("OPENROUTER_MODEL") == "configured" else "fallback"
vision_model_status = "configured" if vision["data_status"] == "configured" else "fallback"
vworld_key_status = "configured" if vworld["data_status"] == "configured" else "fallback"
sendgrid_status = str(email["data_status"])
rag_docs_status = "loaded" if len(rag_index.chunks) > 0 else "empty"
csv_status = "loaded" if not inventory.empty else "empty"
qa_rows = [
    {"item": "OpenRouter Text Model", "status": text_model_status, "note": "버튼 실행 시에만 연결 테스트"},
    {"item": "OpenRouter Vision Model", "status": vision_model_status, "note": "이미지 분석은 업로드 후에만 실행"},
    {"item": "VWorld API Key", "status": vworld_key_status, "note": "주소 변환 실패 시 시연용 대체 좌표 사용"},
    {"item": "DATA GO KR Key", "status": data_go["data_status"], "note": "공공데이터 7종은 별도 버튼으로만 호출"},
    {"item": "SendGrid", "status": sendgrid_status, "note": "기본 disabled 권장"},
    {"item": "RAG Docs", "status": rag_docs_status, "note": rag_index.data_status},
    {"item": "CSV Data", "status": csv_status, "note": "real_csv 또는 안전 대체 데이터"},
]
st.dataframe(pd.DataFrame(qa_rows), width="stretch")

vworld_input_cols = st.columns(2)
with vworld_input_cols[0]:
    vworld_place_query = st.text_input("VWorld 장소명 테스트", value="운양역")
with vworld_input_cols[1]:
    vworld_address_query = st.text_input("VWorld 주소형 테스트", value="경기도 김포시 사우중로 1")

qa_cols = st.columns(3)
with qa_cols[0]:
    if st.button("OpenRouter 텍스트 간단 연결 테스트", width="stretch"):
        result = test_openrouter_text_connection()
        render_status_badge(s(result["status"]), status_style(str(result["status"])))
        st.caption(s(f"source={result['source']} reason={result['reason']}"))
        st.write(s(result["text"]))
with qa_cols[1]:
    if st.button("Vision 설정 상태 확인", width="stretch"):
        result = test_vision_model_available()
        render_status_badge(s(result["status"]), status_style(str(result["status"])))
        st.caption(s(f"source={result['source']} reason={result['reason']}"))
        st.write(s(result["message"]))
with qa_cols[2]:
    if st.button("VWorld 주소 변환 간단 테스트", width="stretch"):
        vworld_results = [
            {"input_type": "PLACE", **test_vworld_geocode_connection(vworld_place_query)},
            {"input_type": "ADDRESS", **test_vworld_geocode_connection(vworld_address_query)},
        ]
        for result in vworld_results:
            render_status_badge(s(f"{result['input_type']} {result['status']}"), status_style(str(result["status"])))
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "input_type": item.get("input_type", ""),
                        "status": item.get("status", ""),
                        "source": item.get("source", ""),
                        "reason_code": item.get("reason_code", ""),
                        "has_coordinate": item.get("has_coordinate", False),
                        "search_type": item.get("search_type", ""),
                        "address_type_tried": item.get("address_type_tried", ""),
                        "display_message": item.get("display_message", ""),
                    }
                    for item in vworld_results
                ]
            ),
            width="stretch",
        )
        if any(item.get("status") != "real_api" for item in vworld_results):
            render_warning_box("VWorld 주소 변환 API가 일시적으로 응답하지 않아 시연용 대체 좌표를 사용할 수 있습니다. 좌표는 참고용이며 실제 현장 위치 검증이 필요합니다.")

render_section_header("PUBLIC API", "공공데이터 API 7종 연동 상태", "자동 호출하지 않으며, 버튼을 누를 때만 DATA_GO_KR_SERVICE_KEY 기반 호출을 시도합니다.")
render_disclaimer_box("real_api는 실제 공공데이터 응답을 받은 상태입니다. real_api_no_data는 API 호출은 정상이나 현재 조건에 해당하는 데이터가 없는 상태입니다. fallback은 실API 성공이 아니라 앱 안정성을 위한 대체 응답입니다.")
render_disclaimer_box("TAGO 버스도착정보는 실시간 데이터 특성상 현재 시점에 도착 예정 정보가 없을 수 있습니다.")
tago_cols = st.columns(4)
with tago_cols[0]:
    tago_route_no = st.text_input("TAGO routeNo", value=DEFAULT_TAGO_ROUTE_NO, help="기본 시연값입니다. 직접 수정할 수 있습니다.")
with tago_cols[1]:
    tago_city_code = st.text_input("TAGO cityCode", value="", help="비워두면 김포 cityCode 자동탐색을 시도합니다.")
with tago_cols[2]:
    tago_route_id = st.text_input("TAGO routeId", value="", help="직접 입력값이 있으면 우선 사용합니다.")
with tago_cols[3]:
    tago_node_id = st.text_input("TAGO nodeId", value="", help="직접 입력값이 있으면 도착정보에 우선 사용합니다.")

if st.button("공공데이터 7종 상태 점검", width="stretch"):
    st.session_state["public_data_api_results"] = run_public_data_api_checks(tago_city_code, tago_node_id, tago_route_id, tago_route_no)
    st.session_state["public_data_api_tago_inputs"] = {
        "route_no": tago_route_no or DEFAULT_TAGO_ROUTE_NO,
        "city_code": tago_city_code,
        "route_id": tago_route_id,
        "node_id": tago_node_id,
    }

public_api_results = st.session_state.get("public_data_api_results")
if public_api_results:
    rows = public_api_result_rows(public_api_results)
    st.dataframe(pd.DataFrame(rows), width="stretch")
    for item in public_api_results:
        if item.get("service_name") == "TAGO 버스도착정보" and item.get("status") == "real_api_no_data":
            render_disclaimer_box("버스도착정보 API는 정상 응답했으나, 현재 선택된 정류소/노선 조건에 도착 예정 데이터가 없습니다. 실시간 API 특성상 일시적으로 데이터가 없을 수 있습니다.")
            break
    api_cols = st.columns(5)
    real_success_count = sum(1 for item in public_api_results if item.get("status") == "real_api")
    real_no_data_count = sum(1 for item in public_api_results if item.get("status") == "real_api_no_data")
    fallback_count = len(public_api_results) - real_success_count - real_no_data_count
    tago_inputs = st.session_state.get("public_data_api_tago_inputs", {})
    with api_cols[0]:
        render_metric_card("real_api 성공", real_success_count, "실제 항목 있음", "success" if real_success_count else "muted")
    with api_cols[1]:
        render_metric_card("real_api_no_data", real_no_data_count, "정상 응답 결과 없음", "warning" if real_no_data_count else "muted")
    with api_cols[2]:
        render_metric_card("대체/오류", fallback_count, "실API 성공 외 상태", "danger" if fallback_count else "success")
    with api_cols[3]:
        render_metric_card("DATA GO KR", data_go["data_status"], "키 값 미표시", "info" if data_go["data_status"] == "configured" else "warning")
    with api_cols[4]:
        render_metric_card("TAGO routeNo", tago_inputs.get("route_no", DEFAULT_TAGO_ROUTE_NO), "기본값 81", "purple")
else:
    render_warning_box("공공데이터 7종 API는 아직 호출하지 않았습니다. 버튼을 누르면 결과가 session_state에 저장됩니다.")

render_section_header("CHART", "운영 참고 차트", "plotly 사용 가능 시 plotly, 실패 시 Streamlit bar chart로 표시합니다.")
chart_frame = pd.DataFrame(
    [
        {"metric": "이동 가능성 평균", "value": average_score, "status": "파일럿 지표"},
        {"metric": "이동지원 후보 요청", "value": 7, "status": "시연용 점검 지표"},
        {"metric": "AI 제보 검토 대기", "value": 3, "status": "시연용 점검 지표"},
        {"metric": "생활체육 리포트", "value": 5, "status": "시연용 점검 지표"},
    ]
)
render_chart(chart_frame)

render_section_header("STATUS", "데이터 및 API 상세 상태", "실패해도 앱 실행은 유지됩니다.")
detail_rows = [
    {"item": "mobility_center", "status": mobility.get("data_status", "missing"), "note": f"rows={len(mobility.get('data', []))}"},
    {"item": "protected_zone", "status": protected_zone.get("data_status", "missing"), "note": f"rows={len(protected_zone.get('data', []))}"},
    {"item": "low_floor_bus", "status": low_floor_bus.get("data_status", "missing"), "note": f"rows={len(low_floor_bus.get('data', []))}"},
    {"item": "weather_stub", "status": weather_stub["data_status"], "note": weather_stub["source"]},
    {"item": "facility_stub", "status": facility_stub["data_status"], "note": facility_stub["source"]},
    {"item": "vision", "status": vision["data_status"], "note": "optional"},
    {"item": "voice", "status": voice["data_status"], "note": "optional"},
    {"item": "email", "status": email["data_status"], "note": "optional"},
    {"item": "vworld", "status": vworld["data_status"], "note": "user-triggered test only"},
    {"item": "data_go_kr", "status": data_go["data_status"], "note": "7 endpoint checks are button-triggered"},
]
st.dataframe(pd.DataFrame(detail_rows), width="stretch")

with st.expander("CSV Inventory"):
    if inventory.empty:
        render_warning_box("탐색된 CSV가 없습니다. 실API 미응답 시 안전 대체 상태로 화면은 유지됩니다.")
        st.dataframe(pd.DataFrame(columns=["file_name", "path", "rows", "columns", "status", "data_status"]), width="stretch")
    else:
        st.dataframe(inventory, width="stretch")

with st.expander("폴더 상태"):
    folder_rows = [folder_status("docs", "*.md"), folder_status("docs", "*.md.md"), folder_status("references", "*")]
    st.dataframe(pd.DataFrame(folder_rows), width="stretch")

render_page_footer_note()
