# CODEX_PROMPT_ADDON_DRIVE_REFERENCES

현재 프로젝트 폴더의 `references/` 폴더에는 Google Drive에서 가져온 이전 RAG/Streamlit 참고 자료가 들어 있다.
Codex는 Google Drive를 직접 읽는다고 가정하지 말고, 현재 로컬 `references/` 파일만 참고하라.

## 참고할 것

1. `README_실행방법_from_drive.md`의 Streamlit 실행 구조: `streamlit run app.py`.
2. `노트북_핵심코드_안전추출.md`의 입력 추출, 문서 근거 포맷팅, chunking 개념.
3. `requirements_*_from_drive.txt`의 패키지 목록 중 필요한 것만 선별.
4. `DX_LangGraph_RAG_summary.md`의 State/Node/Conditional Edge 개념.

## 금지할 것

1. `api_key.txt` 직접 읽기 금지.
2. 키 파일이 없다는 이유로 앱 중단 금지.
3. `OpenAIEmbeddings`를 필수 경로로 두지 말 것.
4. FAISS를 기본 필수 검색기로 쓰지 말 것.
5. AIVLE School 전용 문구, 백서 전용 프롬프트, sample questions를 가져오지 말 것.
6. PDF 하나만 대상으로 하는 RAG 구조 금지.
7. 실제 API Key 값을 코드, README, 예시 파일, 로그에 쓰지 말 것.

## 이번 프로젝트 RAG 기준

1. `docs/*.md`, `docs/*.txt`를 우선 읽는다.
2. PDF는 optional로만 지원한다.
3. 기본 검색기는 `rank_bm25` 기반 BM25다.
4. OpenRouter는 검색기가 아니라 답변 생성 LLM으로만 사용한다.
5. OpenRouter 키가 없거나 실패하면 BM25 검색 결과 요약과 템플릿 답변으로 fallback한다.
6. 모든 외부 API와 LLM 호출은 try/except로 감싼다.
7. 앱은 secrets, docs, data, API가 없어도 실행되어야 한다.

Drive 참고 코드의 목적은 “구조 참고”이지 “그대로 복붙”이 아니다.
