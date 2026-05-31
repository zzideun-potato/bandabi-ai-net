# 김포 반다비 AI Net Streamlit Manifest

공개 저장소 기준 주요 폴더와 파일 역할을 정리합니다. 실제 비밀 키 파일은 포함하지 않습니다.

## 루트 파일

- `app.py`: Streamlit 랜딩 화면, RAG 질문 테스트, 시연 안내 진입점
- `requirements.txt`: Streamlit Cloud와 로컬 실행용 Python 의존성
- `README.md`: 실행 방법, 배포 방법, 시연 동선, 보안 주의, 현재 한계
- `.gitignore`: 로컬 비밀 파일, 캐시, 에디터 파일 제외 규칙

## `.streamlit/`

- `config.toml`: Streamlit 테마와 기본 실행 설정
- `secrets.toml.example`: Secrets 키 이름만 담은 예시 파일
- `.streamlit/secrets.toml`: 저장소에 포함하지 않는 로컬 비밀 파일

## `pages/`

Streamlit 기본 멀티페이지 화면 6개만 둡니다.

- `01_이용자_경로분석.py`: 참고 지도, Viable Path Scoring AI, 기상청 단기예보 상태
- `02_이동지원_추천.py`: 이동지원 후보 추천, 교통약자 이동지원 공공데이터 참고
- `03_생활체육_리포트.py`: 생활체육 참여 참고 리포트, 체육시설 공공데이터 참고
- `04_AI_비전검증.py`: 이미지 기반 AI 임시 검토
- `05_B2G_대시보드.py`: 파일럿 운영 참고 대시보드, Secrets QA, 공공데이터 7종 버튼 기반 점검
- `06_공문_초안_이메일.py`: 관리자 검증용 공문 초안과 SendGrid 안전장치

## `modules/`

공통 기능 모듈입니다.

- `config.py`: Streamlit Secrets 또는 환경변수 읽기, 안전한 configured/missing 상태 반환
- `safety.py`: 금지 표현 치환, 안전 고지, public claim 정리
- `ui_components.py`: 공통 카드, 배지, 안내 박스 UI
- `data_loader.py`: CSV 탐색, 안전 로딩, 안전 대체 데이터 반환
- `api_clients.py`: VWorld geocode, 공공데이터 API 7종, 외부 API 안전 대체 구조
- `scoring.py`: Viable Path Scoring AI rule-based 계산
- `rag_bm25.py`: docs Markdown/TXT 기반 BM25 RAG
- `llm_client.py`: OpenRouter optional 호출과 로컬 대체 답변
- `voice.py`: 음성 명령 optional UI와 텍스트 대체 입력
- `vision.py`: 이미지 AI 임시 검토와 시연용 대체 응답
- `emailer.py`: 관리자 검증용 초안과 SendGrid 전송 안전장치

## 공공데이터 API 7종

`modules/api_clients.py`에서 `DATA_GO_KR_SERVICE_KEY` 하나만 사용하며, API별 operation path 기준으로 호출합니다. 전체 요청 URL과 키 값은 화면과 문서에 표시하지 않습니다.

- 전국체육시설 정보
- 공공체육시설 상세 정보
- 장애인편의시설 현황
- 교통약자 이동지원 현황 실시간 정보
- 기상청 단기예보 조회서비스
- TAGO 버스도착정보
- TAGO 버스노선정보

10단계 기준 시연 확인 상태:

- 전국체육시설 정보: `real_api`
- 공공체육시설 상세 정보: `real_api`
- 장애인편의시설 현황: `real_api`
- 교통약자 이동지원 실시간 정보: `real_api`
- 기상청 단기예보: `real_api`
- TAGO 버스노선정보: `real_api`
- TAGO 버스도착정보: `real_api_no_data` 가능

`real_api`는 실제 공공데이터 응답을 받은 상태입니다. `real_api_no_data`는 API 호출은 정상이나 현재 조건에 해당하는 데이터가 없는 상태입니다. `fallback`은 실API 성공이 아니라 앱 안정성을 위한 대체 응답입니다.

## `docs/`

BM25 RAG 검색 대상 문서 폴더입니다.

- `.md`, `.md.md`, `.txt` 파일을 읽습니다.
- 실제 서비스 문서 기반 검색 근거로 사용합니다.
- 문서가 없어도 `empty_docs` 또는 대체 응답 상태로 실행됩니다.

## `data/`

김포 관련 CSV 데이터를 담는 폴더입니다.

- 교통약자 이동지원센터 CSV
- 노인장애인보호구역 CSV
- 저상버스 관련 CSV
- CSV가 없거나 읽기 실패해도 안전 대체 데이터로 앱 실행을 유지합니다.

## `references/`

이전 RAG/Streamlit 참고자료를 보관하는 선택 폴더입니다.

- 구조와 안전 패턴 참고용입니다.
- 그대로 복붙하지 않습니다.
- 실제 키 또는 로컬 secrets 자료를 포함하지 않습니다.

## `prompts/`

개발 프롬프트와 추가 지시문을 담을 수 있는 선택 폴더입니다.

- 폴더가 없어도 앱 실행에는 영향이 없습니다.
- 실제 API 키나 로컬 비밀 파일을 넣지 않습니다.

## 포함하지 않는 파일

- `api_key*`
- `.env`
- `.env.local`
- `.streamlit/secrets.toml`
- 실제 API 키 값
- 로컬 캐시와 벡터 인덱스
