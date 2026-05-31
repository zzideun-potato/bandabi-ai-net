from __future__ import annotations

import streamlit as st

import modules.llm_client as llm_client
import modules.rag_bm25 as rag_bm25
from modules.safety import DATA_FALLBACK_NOTICE, SERVICE_DISCLAIMER, sanitize_public_claims
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
from modules.voice import render_browser_tts_button, render_voice_command_box


st.set_page_config(page_title="김포 반다비 AI Net", page_icon="♿", layout="wide")
inject_global_styles()


def s(text: str) -> str:
    return sanitize_public_claims(text)


with st.sidebar:
    render_section_header("ACCESSIBILITY", "접근성 안내", "고대비 카드 UI와 명확한 텍스트 배지를 사용합니다.")
    voice_result = render_voice_command_box("app_sidebar")
    render_status_badge(f"intent={voice_result['intent']}", "info")
    render_disclaimer_box("음성 입력은 optional입니다. 음성 파일은 저장하지 않으며 텍스트 대체 입력을 제공합니다.")

render_app_header(
    "김포 반다비 AI Net 파일럿",
    "교통약자 이동지원 · 생활체육 참여 · 접근성 검증을 연결하는 AI 의사결정 보조 시스템",
    "Pilot QA",
)
render_disclaimer_box(SERVICE_DISCLAIMER)

top_cols = st.columns(3)
with top_cols[0]:
    render_metric_card("서비스 상태", "파일럿", "실API 미응답 시 안전 대체", "info")
with top_cols[1]:
    render_metric_card("RAG 문서", "BM25", ".md · .md.md · .txt", "purple")
with top_cols[2]:
    render_metric_card("안전 고지", "필수", DATA_FALLBACK_NOTICE, "warning")

render_info_card(
    "GitHub / Streamlit Cloud 시연 안내",
    "공개 저장소와 Streamlit Cloud 시연용 MVP입니다. 배포 URL은 Streamlit Cloud 배포 URL 입력 예정으로 관리합니다.",
    "Demo",
    "info",
)

render_section_header("SERVICE AREAS", "B2C / B2G 사용 영역", "사용자 분석 흐름과 기관 검토 흐름을 분리해 표시합니다.")

b2c, b2g = st.columns(2)
with b2c:
    render_info_card(
        "B2C 사용자 영역",
        "경로 참고 분석, 이동지원 후보 추천, 생활체육 참여 리포트를 제공합니다. 결과는 참고 정보이며 운영기관과 지도자 확인이 필요합니다.",
        "B2C",
        "info",
    )
with b2g:
    render_info_card(
        "B2G 관리자 영역",
        "AI 임시 검토, 운영 참고 대시보드, 관리자 검증용 공문 초안을 제공합니다. 공식 절차 전환 전 담당자 확인이 필요합니다.",
        "B2G",
        "purple",
    )

page_cols = st.columns(3)
with page_cols[0]:
    render_info_card("01 경로분석", "참고 좌표와 접근성 점수를 함께 확인합니다.", "01", "success")
with page_cols[1]:
    render_info_card("02 이동지원 후보", "운영기관 검토용 후보 정보를 정리합니다.", "02", "info")
with page_cols[2]:
    render_info_card("03 생활체육 리포트", "참여 기록과 문서 근거를 카드형 리포트로 정리합니다.", "03", "purple")

page_cols_2 = st.columns(3)
with page_cols_2[0]:
    render_info_card("04 AI 비전검증", "이미지 제보를 임시 검토 결과로 정리합니다.", "04", "warning")
with page_cols_2[1]:
    render_info_card("05 B2G 대시보드", "파일럿 상태와 대체 응답 사용 여부를 점검합니다.", "05", "success")
with page_cols_2[2]:
    render_info_card("06 공문 초안", "관리자 검증용 초안과 발송 안전장치를 분리합니다.", "06", "info")

render_section_header("RAG TEST", "RAG 문서 질문 테스트", "`docs/` 문서를 BM25로 검색하고 OpenRouter 또는 로컬 대체 답변을 표시합니다.")
rag_index = rag_bm25.build_index("docs")

rag_stats = st.columns(3)
with rag_stats[0]:
    render_metric_card("docs 상태", rag_index.data_status, f"documents={len(rag_index.documents)}", "info")
with rag_stats[1]:
    render_metric_card("검색기", rag_index.search_status, f"chunks={len(rag_index.chunks)}", "purple")
with rag_stats[2]:
    render_metric_card("읽기 오류", len(rag_index.errors), "errors", "warning" if rag_index.errors else "success")

if rag_index.errors:
    with st.expander("문서 읽기 오류"):
        for error in rag_index.errors:
            st.write(s(f"- {error}"))

with st.container():
    rag_question = st.text_input("문서 질문", placeholder="예: 반다비 프로그램 이용 시 확인해야 할 점은?")
    rag_top_k = st.slider("검색 결과 수", min_value=1, max_value=8, value=5)

    if st.button("RAG 검색 및 답변 생성", type="primary"):
        if not rag_question.strip():
            render_warning_box("질문을 입력하세요.")
        else:
            results = rag_bm25.search(rag_question, top_k=rag_top_k, index=rag_index)
            context = rag_bm25.format_context(results)

            if results:
                st.dataframe(
                    [
                        {
                            "rank": item["rank"],
                            "source_file": item["source_file"],
                            "heading": item["heading"],
                            "score": item["score"],
                    }
                    for item in results
                ],
                width="stretch",
            )
            else:
                render_warning_box("검색된 문서 근거가 없습니다. 로컬 대체 답변을 표시합니다.")

            with st.expander("검색 context"):
                st.text_area("context", context, height=260)

            answer = llm_client.generate_rag_answer(rag_question, context)
            render_section_header("ANSWER", "답변", "OpenRouter 실패 또는 키 누락 시 로컬 대체 답변을 사용합니다.")
            st.write(s(str(answer["text"])))
            render_browser_tts_button(str(answer["text"])[:700])
            render_status_badge(f"source={answer.get('source', 'fallback')}", "muted")

render_page_footer_note()
