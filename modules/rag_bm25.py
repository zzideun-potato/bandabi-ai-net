"""Markdown BM25 RAG utilities with keyword fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from modules.safety import sanitize_public_claims

try:
    from rank_bm25 import BM25Okapi
except Exception:  # pragma: no cover - fallback path is required for deployments without rank_bm25
    BM25Okapi = None


TOKEN_PATTERN = re.compile(r"[0-9A-Za-z가-힣]+")
HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
MAX_CHUNK_CHARS = 1100
CHUNK_OVERLAP = 120

QUERY_EXPANSIONS = {
    "차량 신청": ["교통약자", "이동지원", "예약", "콜센터", "특별교통수단"],
    "반다비 프로그램": ["생활체육", "수영", "보치아", "플로어테니스", "피클볼"],
    "편의시설": ["엘리베이터", "장애인 화장실", "유도블럭", "핸드레일"],
    "운양역": ["김포골드라인", "역", "접근성", "엘리베이터"],
    "리포트": ["생활체육", "참여", "피로도", "달성도", "지도자 확인"],
}


@dataclass(frozen=True)
class RagIndex:
    documents: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    tokenized_chunks: list[list[str]]
    bm25: Any | None
    data_status: str
    search_status: str
    errors: list[str]

    @property
    def ready(self) -> bool:
        return bool(self.chunks)


def _document_type(path: Path) -> str:
    if path.name.endswith(".md.md") or path.suffix.lower() == ".md":
        return "markdown"
    if path.suffix.lower() == ".txt":
        return "text"
    return "unknown"


def _candidate_doc_files(docs_dir: str | Path) -> list[Path]:
    base = Path(docs_dir)
    if not base.exists() or not base.is_dir():
        return []

    files: dict[Path, Path] = {}
    for pattern in ("*.md", "*.md.md", "*.txt"):
        try:
            for path in base.glob(pattern):
                if path.is_file():
                    files[path.resolve()] = path
        except Exception:
            continue
    return sorted(files.values(), key=lambda item: item.name)


def _read_text_safely(path: Path) -> tuple[str | None, str | None]:
    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            return path.read_text(encoding=encoding), None
        except Exception as exc:
            last_error = str(exc)
    return None, last_error or "read_error"


def _load_documents_with_errors(docs_dir: str | Path = "docs") -> tuple[list[dict[str, Any]], list[str]]:
    documents: list[dict[str, Any]] = []
    errors: list[str] = []

    for path in _candidate_doc_files(docs_dir):
        text, error = _read_text_safely(path)
        if text is None:
            errors.append(f"{path.name}: {error}")
            continue
        documents.append(
            {
                "source_file": path.name,
                "text": text,
                "document_type": _document_type(path),
                "metadata": {"path": str(path), "suffix": path.suffix},
            }
        )

    return documents, errors


def load_documents(docs_dir: str | Path = "docs") -> list[dict[str, Any]]:
    """Load docs/*.md, docs/*.md.md, and docs/*.txt. Failed files are skipped."""
    documents, _errors = _load_documents_with_errors(docs_dir)
    return documents


def _split_long_text(text: str) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text or "").strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + MAX_CHUNK_CHARS, len(normalized))
        if end < len(normalized):
            paragraph_break = normalized.rfind("\n\n", start, end)
            sentence_break = normalized.rfind(". ", start, end)
            candidate = max(paragraph_break, sentence_break)
            if candidate > start + 300:
                end = candidate + 1
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def split_markdown(text: str, source_file: str) -> list[dict[str, Any]]:
    document_type = "markdown" if source_file.endswith((".md", ".md.md")) else "text"
    chunks: list[dict[str, Any]] = []
    current_heading = "문서 개요"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        block = "\n".join(buffer).strip()
        if not block:
            buffer = []
            return
        for part in _split_long_text(block):
            chunks.append(
                {
                    "source_file": source_file,
                    "heading": current_heading,
                    "document_type": document_type,
                    "text": part,
                }
            )
        buffer = []

    for line in (text or "").splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            flush()
            current_heading = match.group(2).strip() or "문서 개요"
            continue
        buffer.append(line)
    flush()

    if not chunks and text.strip():
        for part in _split_long_text(text):
            chunks.append(
                {
                    "source_file": source_file,
                    "heading": current_heading,
                    "document_type": document_type,
                    "text": part,
                }
            )
    return chunks


def tokenize_korean(text: str) -> list[str]:
    tokens = []
    for token in TOKEN_PATTERN.findall(text or ""):
        lowered = token.lower()
        if len(lowered) >= 2:
            tokens.append(lowered)
    return tokens


def expand_query(query: str) -> str:
    expanded_terms: list[str] = [query or ""]
    for trigger, terms in QUERY_EXPANSIONS.items():
        if trigger in (query or ""):
            expanded_terms.extend(terms)
    return " ".join(term for term in expanded_terms if term)


def build_index(docs_dir: str | Path = "docs") -> RagIndex:
    documents, errors = _load_documents_with_errors(docs_dir)
    chunks: list[dict[str, Any]] = []
    for document in documents:
        chunks.extend(split_markdown(document["text"], document["source_file"]))

    tokenized_chunks = [tokenize_korean(f"{chunk['heading']} {chunk['text']}") for chunk in chunks]
    bm25 = None
    search_status = "keyword_fallback"

    if chunks and BM25Okapi is not None:
        try:
            bm25 = BM25Okapi(tokenized_chunks)
            search_status = "bm25"
        except Exception as exc:
            errors.append(f"BM25 index error: {exc}")

    if errors:
        data_status = "read_error"
    elif chunks:
        data_status = "real_docs"
    else:
        data_status = "empty_docs"

    return RagIndex(
        documents=documents,
        chunks=chunks,
        tokenized_chunks=tokenized_chunks,
        bm25=bm25,
        data_status=data_status,
        search_status=search_status,
        errors=errors,
    )


def _keyword_scores(query_tokens: list[str], tokenized_chunks: list[list[str]]) -> list[float]:
    query_set = set(query_tokens)
    scores: list[float] = []
    for tokens in tokenized_chunks:
        if not tokens:
            scores.append(0.0)
            continue
        overlap = query_set.intersection(tokens)
        repeated_hits = sum(tokens.count(token) for token in query_set)
        scores.append(float(len(overlap) * 2 + repeated_hits))
    return scores


def search(
    query: str,
    top_k: int = 5,
    docs_dir: str | Path = "docs",
    index: RagIndex | None = None,
) -> list[dict[str, Any]]:
    rag_index = index or build_index(docs_dir)
    query_tokens = tokenize_korean(expand_query(query))
    if not query_tokens or not rag_index.chunks:
        return []

    try:
        if rag_index.bm25 is not None:
            scores = [float(score) for score in rag_index.bm25.get_scores(query_tokens)]
        else:
            scores = _keyword_scores(query_tokens, rag_index.tokenized_chunks)
    except Exception:
        scores = _keyword_scores(query_tokens, rag_index.tokenized_chunks)

    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    results: list[dict[str, Any]] = []
    for rank, (chunk_index, score) in enumerate(ranked[:top_k], start=1):
        if score <= 0:
            continue
        chunk = rag_index.chunks[chunk_index]
        results.append(
            {
                "source_file": chunk["source_file"],
                "heading": chunk["heading"],
                "text": chunk["text"],
                "score": round(float(score), 4),
                "rank": rank,
            }
        )
    return results


def format_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return "검색된 문서 근거가 없습니다."

    blocks = []
    for idx, result in enumerate(results, start=1):
        blocks.append(
            f"[근거 {idx} | {result.get('source_file', '')} | {result.get('heading', '')}]\n"
            f"{result.get('text', '')}"
        )
    return "\n\n".join(blocks)


def answer_with_rag(query: str, top_k: int = 5, docs_dir: str | Path = "docs") -> dict[str, Any]:
    rag_index = build_index(docs_dir)
    results = search(query, top_k=top_k, docs_dir=docs_dir, index=rag_index)
    context = format_context(results)

    if not results:
        return {
            "ok": False,
            "answer": sanitize_public_claims(
                "현재 등록된 문서에서 확인되지 않습니다. docs 폴더에 관련 Markdown 문서를 추가한 뒤 다시 검색하세요."
            ),
            "context": context,
            "results": results,
            "data_status": rag_index.data_status,
            "search_status": rag_index.search_status,
            "errors": rag_index.errors,
        }

    try:
        from modules.llm_client import generate_rag_answer

        llm_result = generate_rag_answer(query, context)
        answer = llm_result.get("text", "")
        ok = bool(llm_result.get("ok"))
        source = llm_result.get("source", "fallback")
    except Exception:
        answer = _fallback_rag_text(query, context)
        ok = False
        source = "fallback_exception"

    return {
        "ok": ok,
        "answer": sanitize_public_claims(answer),
        "context": context,
        "results": results,
        "data_status": rag_index.data_status,
        "search_status": rag_index.search_status,
        "source": source,
        "errors": rag_index.errors,
    }


def _fallback_rag_text(question: str, context: str) -> str:
    return sanitize_public_claims(
        "현재 등록된 문서 근거 기준의 참고 답변입니다.\n\n"
        f"질문: {question}\n\n"
        f"{context[:1800]}\n\n"
        "최신 정보는 김포반다비체육센터 또는 김포시교통약자이동지원센터 확인이 필요합니다."
    )


def tokenize(text: str) -> list[str]:
    """Backward-compatible alias."""
    return tokenize_korean(text)


def search_docs(index: RagIndex, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Backward-compatible search wrapper."""
    return search(query, top_k=top_k, index=index)


def format_docs(results: list[dict[str, Any]]) -> str:
    """Backward-compatible context formatter."""
    return format_context(results)
