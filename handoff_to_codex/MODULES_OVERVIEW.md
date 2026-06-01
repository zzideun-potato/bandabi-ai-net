# modules / data / docs / components / views 구조 요약

> Codex 후속 기능 연결용 참고. **API Key·`.env` 값은 포함하지 않음.**

---

## `modules/` (12 files)

| 파일 | 역할 | UI 연결 시점 |
|------|------|--------------|
| `config.py` | `.env` 로드, `get_config_status()` — **키 값 미반환** | 대시보드 status 카드 |
| `api_clients.py` | VWorld, 기상, 버스, TAGO 등 HTTP 클라이언트 | 경로분석 C |
| `scoring.py` | 이동 가능성 점수·등급·설명 | 경로분석 C |
| `data_loader.py` | `data/*.csv` 탐색·로드·fallback | 대시보드 CSV status |
| `rag_bm25.py` | `docs/` BM25 검색·답변 context | 리포트 F, RAG Q&A |
| `llm_client.py` | OpenRouter / fallback 텍스트 | RAG, 공문 초안 |
| `vision.py` | 이미지 접근성 분석 | 접근성 H |
| `emailer.py` | 공문 초안, SendGrid (**기본 발송 off**) | 접근성 H payload |
| `safety.py` | 고지문, `sanitize_public_claims()` | 전 화면 |
| `ui_components.py` | 레거시 카드/헤더 helper | 일부 disclaimer |
| `voice.py` | 음성 intent demo (optional) | 헤더 음성 버튼 |
| `__init__.py` | 패키지 마커 | — |

### config status 키 이름 (값 없음)

`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `VWORLD_API_KEY`, `DATA_GO_KR_SERVICE_KEY`, `SENDGRID_API_KEY`, `EMAIL_ADDRESS`, `ENABLE_SENDGRID_SEND`, `VISION_MODEL`

---

## `components/` (Streamlit UI 레이어)

| 파일 | 역할 |
|------|------|
| `theme.py` | HTML purple CSS → `st.markdown` inject |
| `app_shell.py` | 헤더, 탭 nav, toast, logout |
| `session_state.py` | `init_session_state()`, role/tab defaults |
| `mock_ui.py` | **UI 1차 mock** — 경로·비전·SendGrid payload |
| `route_engine.py` | 경로 orchestration (mock 교체 지점) |
| `flow_steps.py` | MAIN flow step bar |
| `confirm_dialog.py` | 확정·BT 적립 modal |
| `html_assets.py` | 로고 SVG, 경로 map SVG |
| `vision_ui.py` | Vision 데모 SVG·배지 helper |

---

## `views/` (화면)

| 파일 | 화면 ID |
|------|---------|
| `auth_flow.py` | A |
| `tab_main_journey.py` | B, C, D, E, F (+ guardian) |
| `tab_schedule.py` | G |
| `tab_vision.py` | H |
| `tab_dashboard.py` | I (B2G only) |

---

## `data/` (CSV — repo 루트, handoff 미포함)

| 파일 | 내용 |
|------|------|
| `경기도_김포시_교통약자이동지원센터정보_20260105.csv` | 이동지원 센터 |
| `경기도_김포시_노인장애인보호구역_20251222.csv` | 보호구역 |
| `한국교통안전공단_...저상버스...csv` | 저상버스 노선 |
| `README_CSV_PLACEMENT.md` | CSV 배치 안내 |

로더: `modules/data_loader.py` → `load_csv_inventory()`, `load_mobility_center_data()` 등

---

## `docs/` (RAG — repo 루트, handoff 미포함)

| 파일 | 내용 |
|------|------|
| `gimpo_bandabi_center.md.md` | 센터 정보 |
| `gimpo_bandabi_life_sports_article.md.md` | 생활체육 |
| `gimpo_mobility_support.md.md` | 이동지원 |
| `gimpo_goldline_accessibility.md.md` | 접근성 |
| `README_RAG_DOCS.md` | RAG 문서 안내 |

인덱스: `modules/rag_bm25.build_index("docs")`

---

## mock ↔ real 교체 포인트

```
views/tab_main_journey._start_analysis()
  └─ 현재: components/mock_ui.mock_route_analysis()
  └─ 후속: components/route_engine.run_route_analysis()

views/tab_vision._run_analysis()
  └─ 현재: try modules/vision → except mock_ui.mock_vision_result
  └─ 후속: modules/vision.analyze_accessibility_image()

views/tab_dashboard status cards
  └─ modules/config, api_clients, data_loader, rag_bm25, emailer (status only)
```

---

## `backend/` (범위 외)

FastAPI + SQLite + JWT — **Streamlit Cloud 메인 경로에서 사용하지 않음.** Codex UI 작업 시 참고만.
