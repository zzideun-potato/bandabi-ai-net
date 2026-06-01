# Codex 작업 지시서 — Streamlit Native UI (HTML 정합)

## 1. 프로젝트 목표

**김포 반다비 AI** 프로토타입의 UI를 `bandabi_purple.html` 시안과 **최대한 동일한 시각·흐름**으로 Streamlit native에 재현한다.

| 우선순위 | 내용 |
|----------|------|
| 1 | 화면/탭/카드/버튼/색감/스크롤/플로우 |
| 2 | mock 데이터로 자연스러운 데모 |
| 3 | (후속) `modules/` 실기능 연결 — **이번 라운드 범위 아님** |

---

## 2. 배포·아키텍처 (필수 준수)

```
GitHub → Streamlit Cloud → app.py 단독 실행
```

| 금지 | 허용 |
|------|------|
| `components.html()`로 HTML 전체 iframe 렌더 | Streamlit `st.*` 컴포넌트 + custom CSS |
| FastAPI를 메인 배포 경로에 포함 | `modules/` import (status·mock 위주) |
| `.env` / API Key / secrets 파일 커밋·로그·UI 출력 | `.env.example` 키 **이름만** 참고 |

---

## 3. 디자인 기준 (`bandabi_purple.html`)

### 색상 토큰 (CSS `:root`)

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--ink` | `#2d2040` | 주요 텍스트 |
| `--mid` | `#7868a0` | 서브 텍스트·레이블 |
| `--lav` | `#b8acd8` | 액센트·배지 |
| `--surface` | `#f0ecf8` | 연보라 패널 |
| `--base` | `#e8e2f4` | 페이지 배경 |
| `--white` | `#ffffff` | 카드 표면 |
| `--accent` | `#4a2d7a` | Primary 버튼 |
| `--accent-2` | `#6b4fa0` | 보조 강조 |

### UI 패턴

- Pretendard Variable, Font Awesome 6
- `.glass` / `.toss-card` — 흰 카드 + 연보라 border + soft shadow
- 둥근 모서리 18~32px (`rounded-[2rem]` 느낌)
- 토스형 넓은 카드 레이아웃, `layout="wide"`
- 상단 헤더: 브랜드 · 역할 · BT · 로그아웃
- 탭: AI 추천 / 일정 / 접근성 / 대시보드(B2G)

### 금지 스타일

- 네온·과한 gradient
- polygon/세모 장식
- 버튼 오른쪽 화살표 장식

> 참고: HTML 주석은 “다크 보라”보다 **연보라 라이트 퍼플** 계열. Codex는 HTML 실제 색을 따를 것.

---

## 4. 구현할 화면 (A~I)

| ID | 화면 | 핵심 요소 |
|----|------|-----------|
| A | 로그인/회원가입 | 중앙 카드, 이름·이메일·비밀번호, User/Admin, `st.session_state` 프로토타입 |
| B | 사용자 시작 | 인사, 접근성 유형, 출발지, 목적지, 4종 토글, `AI 추천 시작` |
| C | MAIN 01 경로분석 | 경로 카드, AI 소견, 시간/도보/환승/대체수단, 위험도·날씨·시설·버스, 다시하기/확정 |
| D | MAIN 02 버디 | 3카드, 건너뛰기/확정 |
| E | Program AI | 지도자 카드, 다른 지도자/확정 |
| F | MAIN 03 리포트 | 성취도, 가이드, BT, 보호자 공유 |
| G | 일정 추천 | 선호 조건, 추천 3슬롯, 예약 버튼 |
| H | 접근성 점검 | 업로드·미리보기·결과 카드·공문 초안·SendGrid payload 미리보기(미발송) |
| I | 기관 대시보드 | KPI, 이용률/배차/매칭/제보, status 카드(키 값 미표시) |

---

## 5. 비즈니스 규칙 (필수)

### 김포 제2 반다비 교육거점

- 선택지는 **표시 가능**, 선택 시 **진행 불가**
- 경고 문구:
  > 김포 제2 반다비 교육거점은 아직 등록되지 않은 예정 시설입니다. 현재는 김포 반다비체육센터 기준으로 이용해 주세요.
- 제2거점을 목적지·경로분석에 **저장/사용 금지**
- 기본 목적지: **김포 반다비체육센터**

### 경로 mock 시간

- 장거리(예: 성남→김포): **70분+ / 90분+**
- 근거리(구래→센터): **약 20~30분** 수준
- **18분** 같은 비현실적 장거리 수치 금지

### 스크롤

- iframe 고정 높이 **사용 금지**
- 경로·리포트·접근성·대시보드 **페이지 기본 스크롤**로 하단까지 도달

---

## 6. `app.py` 구조 (현재 스냅샷 기준)

`handoff_to_codex/app.py`는 **얇은 진입점**:

```python
st.set_page_config(page_title="반다비 AI", page_icon="🐻", layout="wide")
init_session_state()
inject_purple_theme(...)
ensure_authenticated()  # views/auth_flow.py
render_header()           # components/app_shell.py
render_tab_nav()
render_tab_content()      # views/*.py
```

Codex는 **로직을 views/components로 분리** 유지. `app.py`에 화면 코드를 몰아넣지 말 것.

---

## 7. 레포 전체 구조 (작업 시 참고 — handoff 폴더 밖)

```
project/
├── app.py                      ← Streamlit 진입 (handoff에 스냅샷 포함)
├── bandabi_purple.html         ← 디자인 SSOT (handoff에 포함)
├── components/
│   ├── theme.py                ← HTML 정렬 CSS inject
│   ├── app_shell.py            ← 헤더·탭·toast
│   ├── session_state.py        ← session defaults
│   ├── mock_ui.py              ← UI mock payloads
│   ├── route_engine.py         ← (후속) 경로 orchestration
│   ├── flow_steps.py, confirm_dialog.py, html_assets.py, vision_ui.py
├── views/
│   ├── auth_flow.py
│   ├── tab_main_journey.py     ← A~F
│   ├── tab_schedule.py         ← G
│   ├── tab_vision.py           ← H
│   └── tab_dashboard.py        ← I
├── modules/                    ← 후속 API/RAG/Vision (MODULES_OVERVIEW.md 참고)
├── data/                       ← CSV (경로·이동지원·저상버스 등)
├── docs/                       ← RAG 문서 (.md.md 포함)
├── backend/                    ← FastAPI (메인 배포 경로 아님 — 사용 금지)
└── requirements.txt
```

---

## 8. mock vs 실연동 경계

### 이번 라운드 (mock OK)

- `st.session_state` 화면 전환
- mock 경로·버디·지도자·리포트·일정·접근성·대시보드
- SendGrid **payload 미리보기만** (실발송 X)

### 후속 라운드 (Codex가 함수만 분리해 두면 됨)

- VWorld geocoding, data.go.kr, 버스 API
- RAG (`modules/rag_bm25.py`, `docs/`)
- Vision (`modules/vision.py`)
- SendGrid (`modules/emailer.py`, `ENABLE_SENDGRID_SEND=false` 기본)
- 실제 인증 / DB

`components/mock_ui.py` ↔ `components/route_engine.py` / `modules/*` 교체 지점을 명확히 유지.

---

## 9. Git·보안

- **절대 `git add .` 하지 말 것**
- 커밋 금지: `.env`, `.streamlit/secrets.toml`, `backup/`, API Key
- 커밋 전: `git diff --cached --name-only` 확인

---

## 10. QA 체크리스트

- [ ] HTML 9화면과 Streamlit 9화면 나란히 비교 (`SCREENSHOT_GUIDE.md`)
- [ ] iframe / FastAPI 의존 없음
- [ ] 제2거점 차단 동작
- [ ] 장거리 경로 시간 sanity
- [ ] 4개 긴 화면 하단 스크롤
- [ ] Admin 전용 대시보드 gate
- [ ] UI에 API Key·`.env` 값 미노출

---

## 11. handoff 패키지 파일

| 파일 | 역할 |
|------|------|
| `bandabi_purple.html` | 디자인·플로우 SSOT |
| `app.py` | 현재 진입점 스냅샷 |
| `.env.example` | 키 **이름**만 (값 비움) |
| `requirements.txt` | Python deps |
| `MODULES_OVERVIEW.md` | modules/data/docs 요약 |
| `SCREENSHOT_GUIDE.md` | 캡처 목록 |
| `CODEX_TASK.md` | 본 문서 |

---

## 12. 로컬 실행

```bash
pip install -r requirements.txt
# 프로젝트 루트에서 (handoff 폴더가 아닌 전체 repo)
python -m streamlit run app.py
```

handoff 폴더만으로는 `views/`, `components/` import가 실패한다. **반드시 repo 루트**에서 작업할 것.
