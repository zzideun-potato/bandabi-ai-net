# 김포 반다비 AI Net — Streamlit 파일럿

교통약자 이동지원·생활체육 참여·접근성 점검을 연결하는 **단일 페이지 Streamlit 앱** (`app.py`)입니다.  
HTML 보라 시안(`bandabi_purple (4).html`) 기반 UI이며, 엔진 로직은 `modules/`에 있습니다.

## 현재 구현 범위 (배포 대상)

| 영역 | 파일 | 상태 |
|---|---|---|
| 진입점 | `app.py` | 배포 메인 파일 |
| 탭1 이용자 여정 | `views/tab_main_journey.py` | start → route → care → class → report → guardian |
| 탭3 AI 비전 점검 | `views/tab_vision.py` | 이미지·데모 분석, fallback 안전 표기 |
| 탭2·탭4 | `views/tab_schedule.py`, `views/tab_dashboard.py` | 플레이스홀더 |
| 구버전 참고 | `_reference/pages/`, `app_reference.py` | **실행·배포 대상 아님** (보관용) |
| 자동 테스트 | `tests/` | 로컬·CI용, Cloud 런타임에 포함되지 않음 |

**Secrets 없이도** 탭1·탭3는 fallback / 「예상(참고용)」「예시(참고용)」 경로로 동작합니다.

---

## 로컬 실행

```bash
pip install -r requirements-dev.txt
python -m streamlit run app.py
```

테스트만 실행:

```bash
python -m pytest tests/ -q
```

---

## Streamlit Community Cloud 배포 절차

### 1단계 — GitHub 저장소 준비

1. 이 프로젝트 폴더(`02. 반다비`)만 **별도 공개 저장소**로 올리는 것을 권장합니다.  
   (상위 `★공모전` 모노레포에 두는 경우 → 4단계 경로 주의)
2. **절대 커밋하지 말 것:** `.streamlit/secrets.toml`, `.env`, `api_key*.txt`, 실제 키가 들어간 파일  
3. 레포에는 `.streamlit/secrets.toml.example`만 포함 (키 이름 템플릿)

### 2단계 — Streamlit Cloud 앱 생성

1. [share.streamlit.io](https://share.streamlit.io) 로그인 → **New app**
2. **Repository** · **Branch**(`main`) 선택
3. **Main file path**
   - 단독 레포: `app.py`
   - 모노레포: `02. 반다비/app.py` (폴더명에 맞게 조정)
4. **Advanced settings** (모노레포일 때)
   - Python version: `3.11` (`runtime.txt`와 동일)
   - Requirements file: `requirements.txt` 또는 `02. 반다비/requirements.txt`

### 3단계 — Secrets 입력 (선택, 키 없어도 앱은 동작)

Cloud → 앱 → **Settings → Secrets** 에 TOML 형식으로 입력.  
이름은 `.streamlit/secrets.toml.example` 과 동일하게 사용합니다.

```toml
OPENROUTER_API_KEY = ""
OPENROUTER_MODEL = ""
OPENAI_API_KEY = ""
HF_TOKEN = ""
VWORLD_API_KEY = ""
DATA_GO_KR_SERVICE_KEY = ""
SENDGRID_API_KEY = ""
EMAIL_ADDRESS = ""
ENABLE_SENDGRID_SEND = "false"
VISION_MODEL = ""
```

| 키 | 용도 | 없을 때 |
|---|---|---|
| `OPENROUTER_API_KEY` + `OPENROUTER_MODEL` | RAG·LLM 답변 | BM25/키워드 fallback |
| `VISION_MODEL` (+ OpenRouter 키) | AI 비전 분석 | 데모 fallback |
| `VWORLD_API_KEY` | 주소 좌표 | mock 좌표 |
| `DATA_GO_KR_SERVICE_KEY` | 버스·기상·체육 API | fallback 응답 |
| `SENDGRID_*` | 이메일 (탭4·레거시) | 전송 비활성 |

> `ENABLE_SENDGRID_SEND` 는 기본 `"false"` 권장.

### 4단계 — Deploy

**Deploy** 클릭 후 빌드 로그에서 `requirements.txt` 설치·`app.py` 기동을 확인합니다.

### 5단계 — 배포 후 확인 체크리스트

- [ ] 로그인(이용자 모드) 후 탭1 **「AI 추천 시작」** → 예외 없음, 경로 카드에 **「예상(참고용)」** 배지
- [ ] 탭1 report 단계 RAG 블록 표시 (키 없으면 fallback 답변)
- [ ] 탭3 **「데모 이미지로 분석」** → **「예시(참고용)」**, **「공식 판정 아님」**, 마스킹 고지 표시
- [ ] 탭3·탭1에 **96.8%** 같은 확정형 정밀 수치 없음 (fallback 환경)
- [ ] `.streamlit/secrets.toml` 이 GitHub에 없음 (`git ls-files` 로 확인)
- [ ] 탭2·탭4 플레이스홀더만 보이고 앱 전체가 죽지 않음

---

## 의존성 (`requirements.txt`)

Cloud 배포용 최소 패키지 (실제 `app.py` → `modules/` import 기준):

| 패키지 | 사용처 |
|---|---|
| `streamlit` | UI |
| `requests` | 공공 API (`modules/api_clients.py`) |
| `rank_bm25` | RAG BM25 (`modules/rag_bm25.py`, 없으면 키워드 fallback) |
| `openai` | OpenRouter 클라이언트 (`modules/llm_client.py`, `modules/vision.py` lazy import) |

**제거한 패키지** (현재 `app.py` 경로에서 미사용): `pandas`, `numpy`(직접), `pymupdf`, `plotly`, `folium`, `streamlit-folium`, `sendgrid`, `streamlit-mic-recorder`, `python-dotenv`  
→ 탭4·레거시 `_reference/pages/` 구현 시 필요하면 그때 추가.

개발·테스트: `requirements-dev.txt` (`pytest` 포함)

Python 버전: `runtime.txt` → **3.11**

---

## 보안 주의

- `api_key*.txt`, `.env`, `.streamlit/secrets.toml` 업로드 금지 (`.gitignore`에 등록됨)
- 코드·README·로그에 실제 키 값 표시 금지 — `modules/config.py`는 `st.secrets` / 환경변수만 읽음
- `ENABLE_SENDGRID_SEND` 기본 `false` 권장

---

## 안전 고지

- 본 서비스는 이동지원 확정, 배차 확정, 공식 민원 접수, 의료 진단을 수행하지 않습니다.
- AI 검출·경로·RAG 결과는 **참고 정보**이며 운영기관·지도자 확인이 필요합니다.
- 탭3 비전 결과는 **공식 판정·행정처분·시설 적합 판정을 대체하지 않습니다.**

---

## docs / data

- `docs/` — BM25 RAG 검색 대상 (`.md`, `.txt`)
- `data/*.csv` — CSV 로더용 (탭4 대시보드 등에서 사용 예정)
- 파일이 없어도 fallback으로 화면 유지

---

## 레거시 참고

- `app_reference.py`, `_reference/pages/` — 이전 멀티페이지 Streamlit 구조 보관본
- Streamlit Cloud는 **`app.py`만** 지정하면 `_reference/`, `tests/`는 자동 실행되지 않습니다.
