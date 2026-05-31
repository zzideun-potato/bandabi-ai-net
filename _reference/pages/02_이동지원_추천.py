from __future__ import annotations

from datetime import time

import pandas as pd
import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.api_clients import fetch_mobility_support_realtime
from modules.safety import get_disclaimer, sanitize_public_claims
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


st.set_page_config(page_title="이동지원 추천", page_icon="🚐", layout="wide")
inject_global_styles()


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def build_mobility_recommendation(wheelchair_user: bool, origin: str, destination: str, api_result: dict) -> dict[str, str]:
    if wheelchair_user:
        candidate = "특별교통수단 우선 검토"
        reason = "휠체어 이용 조건이 있어 승하차 지원 가능 여부 확인이 필요합니다."
        status = "warning"
    else:
        candidate = "대체수단과 특별교통수단 병행 검토"
        reason = "보행 가능 조건과 대중교통 접근성을 함께 확인할 수 있습니다."
        status = "info"

    if api_result.get("status") == "real_api":
        reason = f"{reason} 공공데이터 실응답 {api_result.get('real_count', 0)}건을 참고할 수 있습니다."
    elif api_result.get("status") == "real_api_no_data":
        reason = f"{reason} 공공데이터는 정상 응답했으나 현재 검색 조건 기준 결과가 없습니다."
    else:
        reason = f"{reason} 공공데이터 실응답 확인 실패, 대체 응답 기반 추천 사용 상태입니다."

    return {
        "candidate": s(candidate),
        "route": s(f"{origin or '출발지 미입력'} → {destination or '목적지 미입력'}"),
        "reason": s(reason),
        "next_step": s("운영기관 확인 필요"),
        "availability": s("이용 가능 여부 확인 필요"),
        "status": status,
    }


def mobility_item_summary(items: list[dict]) -> pd.DataFrame:
    rows = []
    for item in items[:5]:
        if not isinstance(item, dict):
            rows.append({"raw": s(item)})
            continue
        rows.append(
            {
                "센터": item.get("ctrNm") or item.get("centerName") or item.get("센터명") or "",
                "운영차량대수": item.get("oprVhclCntom") or item.get("vhclCntom") or "",
                "가용차량대수": item.get("avlVhclCntom") or "",
                "예약건수": item.get("rsvtNocs") or "",
                "대기건수": item.get("wtngNocs") or "",
                "기준": item.get("totDt") or item.get("baseDt") or "",
            }
        )
    return pd.DataFrame(rows)


render_app_header(
    "교통약자 이동지원 후보 추천",
    "공공데이터 API, RAG 문서, 사용자 입력을 참고해 운영기관 검토용 후보 정보를 정리합니다.",
    "B2C",
)
render_disclaimer_box(get_disclaimer("mobility"))

guide_cols = st.columns(2)
with guide_cols[0]:
    render_info_card("특별교통수단 확인 카드", "휠체어 이용, 보행 보조, 동행 필요 여부를 기준으로 운영기관 검토 항목을 정리합니다.", "Support", "info")
with guide_cols[1]:
    render_info_card("대체수단 확인 카드", "대중교통 접근성, 동행 이동, 현장 접근성 확인을 함께 비교합니다.", "Alt", "purple")

with st.form("mobility_form"):
    col1, col2 = st.columns(2)
    with col1:
        wheelchair_user = st.checkbox(s("휠체어 이용 여부"), value=False)
        origin = st.text_input(s("출발지"), placeholder=s("예: 운양역 인근"))
        desired_date = st.date_input(s("희망일"))
    with col2:
        destination = st.text_input(s("목적지"), value=s("김포반다비체육센터"))
        desired_time = st.time_input(s("희망 시간"), value=time(10, 0))
        support_note = st.text_area(s("추가 확인사항"), placeholder=s("동행, 승하차 지원, 안내 필요 여부 등"))

    submitted = st.form_submit_button(s("이동지원 후보 추천"))

rag_index = rag_bm25.build_index("docs")
rag_results = rag_bm25.search("교통약자 이동지원 콜센터 특별교통수단 운영기관 검토", top_k=4, index=rag_index)
rag_context = rag_bm25.format_context(rag_results)

if submitted:
    mobility_api = fetch_mobility_support_realtime(area="김포")
    recommendation = build_mobility_recommendation(wheelchair_user, origin, destination, mobility_api)
    st.session_state["mobility_recommendation"] = {
        "recommendation": recommendation,
        "desired_date": str(desired_date),
        "desired_time": str(desired_time),
        "support_note": s(support_note),
        "public_api": mobility_api,
        "rag_data_status": rag_index.data_status,
        "rag_result_count": len(rag_results),
        "rag_context": rag_context,
        "rag_results": rag_results,
    }

saved = st.session_state.get("mobility_recommendation")
if saved:
    recommendation = saved["recommendation"]
    public_api = saved["public_api"]
    api_status = public_api.get("status", "fallback")
    render_section_header("RESULT", "후보 추천 결과", "실제 이용 가능 여부는 운영기관 확인이 필요합니다.")
    result_cols = st.columns(4)
    with result_cols[0]:
        render_metric_card("추천 후보", recommendation["candidate"], "candidate", recommendation["status"])
    with result_cols[1]:
        render_metric_card("희망 일정", f"{saved['desired_date']} {saved['desired_time']}", "사용자 입력", "info")
    with result_cols[2]:
        render_metric_card("공공데이터 API", api_status, f"real={public_api.get('real_count', 0)} 대체={public_api.get('fallback_count', 0)}", "success" if api_status == "real_api" else "warning")
    with result_cols[3]:
        render_metric_card("문서 상태", saved["rag_data_status"], f"results={saved['rag_result_count']}", "purple")

    render_info_card("이동 구간", recommendation["route"], status="info")
    render_info_card("추천 사유", recommendation["reason"], status="success")
    render_info_card("다음 확인", f"{recommendation['next_step']} · {recommendation['availability']}", status="warning")
    if saved["support_note"]:
        render_warning_box(f"추가 확인사항: {saved['support_note']}")

    render_status_badge(f"공공데이터 API: {api_status}", "success" if api_status == "real_api" else "warning")
    with st.expander("교통약자 이동지원 공공데이터 참고"):
        st.write(s(public_api.get("message", "")))
        st.caption(s(f"reason_code={public_api.get('reason_code', '')} action_needed={public_api.get('action_needed', '')}"))
        if api_status == "real_api" and public_api.get("items"):
            st.dataframe(mobility_item_summary(public_api["items"]), width="stretch")
        elif api_status == "real_api_no_data":
            st.write("공공데이터 정상 응답이나 검색 조건 기준 결과가 없습니다.")
        else:
            st.write("공공데이터 실응답 확인 실패, 대체 응답 기반 추천 사용 상태입니다.")

    render_status_badge("RAG 근거 있음" if saved["rag_results"] else "RAG 대체 응답", "success" if saved["rag_results"] else "warning")
    with st.expander("교통약자 이동지원 관련 RAG 근거"):
        if saved["rag_results"]:
            for item in saved["rag_results"]:
                st.write(s(f"{item['rank']}. {item['source_file']} | {item['heading']} | score={item['score']}"))
            st.text_area("근거 context", saved["rag_context"], height=260)
        else:
            st.write("현재 등록된 문서에서 관련 근거가 확인되지 않습니다.")

    if st.button(s("운영기관 검토 요청")):
        render_status_badge("UI 상태 등록", "info")
        render_info_card("검토 요청 상태", "요청 후보가 화면 상태로만 등록되었습니다. 실제 접수 처리 또는 이용 가능 여부 결정이 아닙니다.", status="info")
else:
    render_warning_box("입력값을 작성한 뒤 이동지원 후보 추천을 실행하세요.")

render_disclaimer_box("이동지원센터 연락 또는 운영기관 확인이 필요합니다. 이 화면의 결과는 후보 추천과 검토 자료입니다.")
render_page_footer_note()
