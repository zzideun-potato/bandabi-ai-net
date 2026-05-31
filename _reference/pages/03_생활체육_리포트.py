from __future__ import annotations

import pandas as pd
import streamlit as st

import modules.rag_bm25 as rag_bm25
from modules.api_clients import fetch_sports_facilities, fetch_sports_facility_detail
from modules.llm_client import generate_rag_answer
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


st.set_page_config(page_title="생활체육 리포트", page_icon="🏊", layout="wide")
inject_global_styles()


PROGRAMS = ["수영", "아쿠아로빅", "GX", "기구 필라테스", "보치아", "컬링", "플로어테니스", "피클볼"]
SUPPORT_TYPES = ["휠체어 또는 보행 보조 필요", "음성 안내 또는 유도 동선 필요", "단계별 안내 또는 보호자·동행 지원 필요", "일반"]
REQUIRED_NOTICE = "본 리포트는 의료 진단, 치료, 재활치료 또는 의학적 판단을 대체하지 않습니다. 생활체육 참여를 돕기 위한 참고 정보이며, 운동 강도 변경은 지도자 확인 후 진행해야 합니다."


def s(text: object) -> str:
    return sanitize_public_claims(str(text))


def api_status_line(result: dict) -> str:
    status = result.get("status", "fallback")
    if status == "real_api":
        return f"실응답 {result.get('real_count', 0)}건"
    if status == "real_api_no_data":
        return "검색 조건 기준 결과 없음"
    return "시설 API 실응답 확인 실패, RAG/대체 응답 사용"


def facility_rows(*results: dict) -> list[dict]:
    rows: list[dict] = []
    for result in results:
        if result.get("status") != "real_api":
            continue
        for item in result.get("items", [])[:5]:
            if not isinstance(item, dict):
                rows.append({"raw": s(item)})
                continue
            rows.append(
                {
                    "시설명": item.get("faci_nm") or item.get("faciNm") or item.get("facility_name") or "",
                    "주소": item.get("faci_road_addr") or item.get("faci_addr") or item.get("lNmAddr") or "",
                    "지역": item.get("addr_cpb_nm") or item.get("fmng_cpb_nm") or item.get("area") or "",
                    "종목": item.get("fcob_nm") or "",
                    "유형": item.get("ftype_nm") or "",
                    "상태": item.get("faci_stat_nm") or item.get("faci_stat_cd") or "",
                }
            )
    return rows


def build_template_report(inputs: dict, context: str, facility_result: dict, detail_result: dict) -> str:
    discomfort_text = "있음" if inputs["has_discomfort"] else "없음"
    instructor_text = "필요" if inputs["needs_instructor_check"] else "권장"
    report = f"""
### 요약
- 선택 프로그램: {inputs["program"]}
- 참여 횟수: {inputs["participation_count"]}회
- 피로도: {inputs["fatigue"]}/10
- 불편감 여부: {discomfort_text}
- 달성도: {inputs["achievement"]}/10

### 참여 변화 참고
- 현재 입력 기준으로 참여 지속성과 피로도 변화를 함께 관찰하는 단계입니다.
- 불편감이 있으면 강도 변경보다 지도자 확인을 우선합니다.

### 다음 참여 가이드
- 다음 목표: {inputs["next_goal"] or "다음 참여 목표 미입력"}
- 접근성 지원 필요 유형: {inputs["support_type"]}
- 참여 전 이동 동선, 대기 공간, 보조 안내 가능 여부를 확인합니다.

### 지도자 확인 필요 사항
- 지도자 확인 필요 여부: {instructor_text}
- 피로도, 불편감, 접근성 지원 필요 유형을 지도자에게 공유합니다.

### 시설 참고 정보
- 전국체육시설 정보 API: {api_status_line(facility_result)}
- 공공체육시설 상세 정보 API: {api_status_line(detail_result)}

### 참고 근거
{context}

### 주의 문구
{REQUIRED_NOTICE}
"""
    return s(report.strip())


render_app_header(
    "김포반다비센터 생활체육 추천 리포트",
    "입력 영역과 결과 영역을 분리해 지도자 확인용 참고 리포트를 생성합니다.",
    "B2C",
)
render_disclaimer_box(get_disclaimer("sports"))
render_disclaimer_box(REQUIRED_NOTICE)

render_section_header("INPUT", "리포트 입력", "참여 기록과 다음 목표를 입력합니다.")
with st.form("sports_report_form"):
    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox(s("프로그램 선택"), [s(item) for item in PROGRAMS])
        participation_count = st.number_input(s("참여 횟수"), min_value=0, max_value=100, value=4, step=1)
        fatigue = st.slider(s("피로도"), min_value=0, max_value=10, value=4)
        has_discomfort = st.checkbox(s("불편감 여부"), value=False)
    with col2:
        achievement = st.slider(s("달성도"), min_value=0, max_value=10, value=6)
        next_goal = st.text_input(s("다음 목표"), placeholder=s("예: 주 1회 꾸준히 참여"))
        support_type = st.selectbox(s("접근성 지원 필요 유형"), [s(item) for item in SUPPORT_TYPES])
        needs_instructor_check = st.checkbox(s("지도자 확인 필요 여부"), value=True)

    submitted = st.form_submit_button(s("생활체육 리포트 생성"))

if submitted:
    facility_result = fetch_sports_facilities(keyword="김포")
    detail_result = fetch_sports_facility_detail(facility_name="김포반다비체육센터")
    rag_query = f"반다비 프로그램 생활체육 리포트 {program} 참여 피로도 달성도 지도자 확인"
    rag_index = rag_bm25.build_index("docs")
    rag_results = rag_bm25.search(rag_query, top_k=4, index=rag_index)
    context = rag_bm25.format_context(rag_results)
    inputs = {
        "program": program,
        "participation_count": participation_count,
        "fatigue": fatigue,
        "has_discomfort": has_discomfort,
        "achievement": achievement,
        "next_goal": next_goal,
        "support_type": support_type,
        "needs_instructor_check": needs_instructor_check,
    }
    template_report = build_template_report(inputs, context, facility_result, detail_result)
    llm_result = generate_rag_answer(
        "생활체육 리포트 문장을 문서 근거 안에서 안전하게 정리해 주세요.",
        f"작성 초안:\n{template_report}\n\n참고 근거:\n{context}",
    )
    final_report = s(str(llm_result.get("text", ""))) if llm_result.get("ok") else template_report
    st.session_state["sports_report"] = {
        "report": final_report,
        "program": s(program),
        "rag_status": rag_index.data_status,
        "rag_count": len(rag_results),
        "source": s(str(llm_result.get("source", "template"))),
        "context": context,
        "results": rag_results,
        "facility_result": facility_result,
        "detail_result": detail_result,
    }

saved = st.session_state.get("sports_report")
if saved:
    facility_result = saved["facility_result"]
    detail_result = saved["detail_result"]
    render_section_header("REPORT", "생활체육 추천 결과", "리포트와 RAG 근거, 공공데이터 시설 참고 정보를 함께 확인합니다.")
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("프로그램", saved["program"], "생활체육", "purple")
    with cols[1]:
        render_metric_card("문서 상태", saved["rag_status"], f"results={saved['rag_count']}", "info")
    with cols[2]:
        render_metric_card("시설 API", facility_result["status"], f"real={facility_result.get('real_count', 0)} 대체={facility_result.get('fallback_count', 0)}", "success" if facility_result["status"] == "real_api" else "warning")
    with cols[3]:
        render_metric_card("상세 API", detail_result["status"], f"real={detail_result.get('real_count', 0)} 대체={detail_result.get('fallback_count', 0)}", "success" if detail_result["status"] == "real_api" else "warning")
    render_metric_card("문장 개선", saved["source"], "OpenRouter optional", "muted")
    render_info_card("리포트", saved["report"], status="info")
    render_disclaimer_box(REQUIRED_NOTICE)

    with st.expander("생활체육 시설 공공데이터 참고"):
        render_status_badge(f"전국체육시설 정보: {facility_result['status']}", "success" if facility_result["status"] == "real_api" else "warning")
        render_status_badge(f"공공체육시설 상세 정보: {detail_result['status']}", "success" if detail_result["status"] == "real_api" else "warning")
        st.caption(s(f"시설 API reason={facility_result.get('reason_code', '')} action={facility_result.get('action_needed', '')}"))
        st.caption(s(f"상세 API reason={detail_result.get('reason_code', '')} action={detail_result.get('action_needed', '')}"))
        rows = facility_rows(facility_result, detail_result)
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch")
        elif facility_result["status"] == "real_api_no_data" or detail_result["status"] == "real_api_no_data":
            st.write("검색 조건 기준 결과 없음 상태입니다.")
        else:
            st.write("시설 API 실응답 확인 실패, RAG/대체 응답 사용 상태입니다.")

    with st.expander("RAG 참고 근거"):
        if saved["results"]:
            for item in saved["results"]:
                st.write(s(f"{item['rank']}. {item['source_file']} | {item['heading']} | score={item['score']}"))
            st.text_area("근거 context", saved["context"], height=260)
        else:
            st.write("현재 등록된 문서에서 관련 근거가 확인되지 않습니다.")
else:
    render_warning_box("입력값을 작성한 뒤 생활체육 리포트를 생성하세요.")

render_page_footer_note()
