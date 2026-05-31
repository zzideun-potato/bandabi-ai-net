# Codex용 Google Drive 참고자료 사용 가이드

## 이 references 폴더의 목적

Google Drive에 있던 이전 RAG/Streamlit 실습 코드에서 반다비 프로젝트에 필요한 구조만 참고하기 위한 폴더입니다.

## 그대로 가져가면 좋은 것

- `streamlit run app.py` 실행 구조
- 문서 로딩 → chunk 분할 → 검색 → context 구성 → LLM 답변 생성 흐름
- `format_docs()`와 비슷한 근거 포맷팅 방식
- `extract_question()`처럼 dict/string 입력을 모두 처리하는 방식
- chunk_size, chunk_overlap 개념
- requirements에서 `streamlit`, `requests`, `rank_bm25`, `pymupdf`, `openai` 등 필요한 패키지 선별

## 그대로 가져가면 안 되는 것

- `api_key.txt` 직접 읽기
- 키 파일이 없으면 앱을 중단시키는 `FileNotFoundError`
- `OpenAIEmbeddings` 필수 의존
- FAISS 필수 의존
- AIVLE School 전용 system prompt
- AIVLE 백서 전용 질문/답변
- PDF 하나만 대상으로 하는 RAG 구조
- 실제 API 키 값, 로컬 키 파일, secrets 파일

## 반다비 프로젝트 기본 구조

```text
BM25 검색
+ Markdown docs
+ OpenRouter optional LLM
+ Streamlit multipage UI
+ 모든 외부 호출 fallback
```
