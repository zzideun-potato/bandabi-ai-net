# 화면 캡처 가이드 (Codex / 디자인 QA용)

이 문서는 **HTML 기준 UI**(`bandabi_purple.html`)와 **현재 Streamlit native 1차 구현**을 비교·보완할 때 필요한 스크린샷 목록입니다.

캡처는 **실제 `.env` / API Key / secrets 없이** 로컬 또는 Streamlit Cloud에서 mock 상태로 진행합니다.

---

## 공통 캡처 규칙

| 항목 | 권장 |
|------|------|
| 해상도 | Desktop 1440×900 또는 1280×800 |
| 브라우저 | Chrome 최신, 100% 줌 |
| 파일명 | `01_login.png`, `02_start.png` … 번호 접두 |
| 저장 위치 | `handoff_to_codex/screenshots/` (폴더는 캡처 시 생성) |
| 비교 기준 | HTML을 브라우저에서 직접 열어 **같은 화면**을 나란히 캡처 |

---

## 필수 캡처 화면 (9종)

### 1. 로그인/회원가입 화면
- **HTML 기준:** 로그인 모달 진입 → 로그인/회원가입 폼 → User/Admin 역할 선택
- **Streamlit:** `@st.dialog` 인증 플로우 (`views/auth_flow.py`)
- **포함 요소:** 반다비 AI 로고·타이틀, 이름/이메일/비밀번호, 이용자·관리자 모드 버튼
- **파일명 예:** `01_auth_entry.png`, `01_auth_form.png`, `01_auth_role.png`

### 2. 사용자 시작 화면
- **HTML 기준:** `#start-screen` — “반갑습니다, 000님 :)”, 접근성 유형, 출발지, 목적지, 알림 토글, `AI 추천 시작`
- **Streamlit:** `views/tab_main_journey.py` → `render_start()`
- **파일명 예:** `02_start.png`

### 3. MAIN 01 — AI 기반 도착 가능성 / 경로분석
- **HTML 기준:** `#route-screen` — 추천 경로, AI 종합 소견, 총 시간/도보/환승, 위험도·날씨·시설·버스 카드, `다시하기`/`확정하기`
- **Streamlit:** `render_route()`
- **주의:** 성남→김포 등 장거리는 **90분+** 수준 mock. 18분처럼 비현실적 수치 금지
- **파일명 예:** `03_main01_route.png` (스크롤 하단 버튼까지 포함해 **전체 세로** 캡처)

### 4. MAIN 02 — 버디 추천
- **HTML 기준:** `#care-screen` — 첫 방문 버디, 센터 도우미, 보호자 모드 카드, `건너뛰기`/`확정하기`
- **Streamlit:** `render_care()`
- **파일명 예:** `04_main02_buddy.png`

### 5. Program AI — 강습·지도자 추천
- **HTML 기준:** `#class-screen` — 추천 지도자 카드, 요일/시간/소그룹, `다른 지도자`/`확정하기`
- **Streamlit:** `render_class()`
- **파일명 예:** `05_program_ai.png`

### 6. MAIN 03 — 생활체육 리포트
- **HTML 기준:** `#report-screen` — 성취도/지속참여, 오늘 참여 요약, 다음 가이드, BT, 보호자 공유
- **Streamlit:** `render_report()` + `render_guardian()` (필요 시 2장)
- **파일명 예:** `06_main03_report.png`, `06_guardian_share.png`
- **스크롤:** 리포트 하단까지 세로 캡처

### 7. 내 운동 일정 추천
- **HTML 기준:** `#schedule-tab` — 선호 요일/시간, 이동지원·버디 우선, 추천 시간 3카드, 예약 버튼
- **Streamlit:** `views/tab_schedule.py`
- **파일명 예:** `07_schedule_before.png` (분석 전), `07_schedule_after.png` (추천 후)

### 8. 접근성 점검 보조
- **HTML 기준:** `#vision-tab` — 사진 업로드, 미리보기, AI 결과 카드, 공문 초안/SendGrid payload 영역
- **Streamlit:** `views/tab_vision.py`
- **파일명 예:** `08_vision_scan.png`, `08_gov_draft.png`
- **스크롤:** 공문·payload 영역까지 세로 캡처

### 9. 기관용 대시보드
- **HTML 기준:** `#dashboard-tab` — KPI 4종, 차트 영역, 운영 액션 보드, 공공데이터/status 카드
- **Streamlit:** `views/tab_dashboard.py` (**Admin 모드** 로그인 필요)
- **파일명 예:** `09_dashboard.png`
- **스크롤:** 하단 status 카드까지 세로 캡처

---

## 선택 캡처 (권장)

| 화면 | 목적 |
|------|------|
| 상단 헤더 + 탭 네비 | `components/app_shell.py` — BT 포인트, 로그아웃, 4탭 |
| Flow step 바 | 경로→동행→강습→리포트 단계 표시 |
| 김포 제2거점 선택 시 경고 | toast/warning 문구 QA |
| 고대비 모드 | 접근성 CSS (`components/theme.py`) |

---

## HTML만 별도 캡처하는 방법

1. `handoff_to_codex/bandabi_purple.html`을 브라우저에서 직접 연다.
2. 로그인 모달 → 이용자 모드 → 각 flow/tab 순서대로 동일 9화면 캡처.
3. Streamlit 캡처와 **같은 파일명 규칙**으로 `screenshots/html/` 하위에 저장하면 diff가 쉽다.

---

## Codex에게 전달할 때

- 스크린샷 + `bandabi_purple.html` + `CODEX_TASK.md`를 함께 제공.
- “HTML 대비 Streamlit에서 어긋난 카드/색/간격”을 스크린샷에 빨간 박스로 표시한 메모 PNG 1장 추가하면 효과적.
