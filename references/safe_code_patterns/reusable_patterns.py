"""
Safe reusable patterns extracted/adapted from the Google Drive RAG notebook.
Do not import this file directly as the production module unless you want to.
Use it as a reference for modules/rag_bm25.py and modules/llm_client.py.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, List


def extract_question(value: Any) -> str:
    """Accept either a string or a dict-like input and return a user query safely."""
    if isinstance(value, dict):
        return str(value.get("input") or value.get("question") or value.get("query") or "").strip()
    return str(value).strip()


def format_context(results: Iterable[Dict[str, Any]]) -> str:
    """Format BM25 search results as grounded context for an LLM prompt."""
    formatted: List[str] = []
    for idx, item in enumerate(results, start=1):
        source = Path(str(item.get("source_file", "unknown"))).name
        heading = item.get("heading") or "위치 정보 없음"
        score = item.get("score")
        text = str(item.get("text", "")).strip()
        score_text = f" | score={score:.3f}" if isinstance(score, (float, int)) else ""
        formatted.append(f"[근거 {idx} | {source} | {heading}{score_text}]\n{text}")
    return "\n\n".join(formatted)


def get_secret(name: str, default: str = "") -> str:
    """
    Streamlit secrets/env safe loader pattern.
    Production code should place this in modules/config.py.
    """
    import os
    try:
        import streamlit as st
        value = st.secrets.get(name, None)
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def safe_fallback_answer(question: str, context: str = "") -> str:
    """Fallback answer when OpenRouter or other LLM is unavailable."""
    if context.strip():
        return (
            "OpenRouter LLM 호출이 불가능하여 검색된 문서 근거를 요약합니다.\n\n"
            f"질문: {question}\n\n"
            f"검색 근거:\n{context}\n\n"
            "현재 등록된 문서에서 확인되지 않는 내용은 단정하지 않습니다. "
            "최신 정보는 김포반다비체육센터 또는 김포시교통약자이동지원센터 확인이 필요합니다."
        )
    return (
        "현재 등록된 문서에서 확인되지 않습니다. "
        "최신 정보는 김포반다비체육센터 또는 김포시교통약자이동지원센터 확인이 필요합니다."
    )
