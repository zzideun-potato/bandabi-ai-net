# 반다비 AI — HTML 프로토타입 (Streamlit 렌더링)

완성형 프론트 **`bandabi_purple.html`** 을 Streamlit에서 **수정 없이** iframe으로 보여 줍니다.  
HTML·CSS·JS는 **건드리지 않습니다.** 백엔드/API 연결은 추후 별도 작업입니다.

## 구조

```
project/
├── app.py
├── bandabi_purple.html
├── backend/              ← FastAPI 인증 API
├── requirements.txt
└── README.md
```

## 로컬 실행

**1) 인증 API (터미널 1)**

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**2) Streamlit UI (터미널 2)**

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

`app.py`는 `bandabi_purple.html`에 `BACKEND_API_URL`(기본 `http://localhost:8000`)만 주입합니다.  
로그인·회원가입은 FastAPI + SQLite(`backend/data/bandabi.db`) + JWT로 처리됩니다.

### 인증 흐름

| 단계 | 설명 |
|------|------|
| 회원가입 | 이름 · 이메일 · 비밀번호(8자+) → `/auth/signup` |
| 로그인 | 이메일 · 비밀번호 → `/auth/login` |
| 역할 선택 | 이용자(B2C) / 기관 관리자(B2G) → `/auth/select-role` |
| 세션 유지 | JWT를 브라우저 `localStorage`에 저장, 새로고침 시 `/auth/me`로 복원 |

배포 시 `.streamlit/secrets.toml`에 `BACKEND_API_URL`, 백엔드 env에 `JWT_SECRET`을 설정하세요.

API 서버 없이 Streamlit만 실행하면 로그인/회원가입 요청이 실패합니다. **1)+2)** 를 함께 실행하세요.

## 원본과 동일하게 보기

1. **브라우저에서 HTML 직접 열기:** `bandabi_purple.html` 더블클릭 또는 `file://` 로 열기  
2. **Streamlit:** `python -m streamlit run app.py`

두 화면을 나란히 비교합니다. Streamlit 쪽은 `app.py`가 여백·헤더만 제거하고 `components.html(..., height=3000, scrolling=True)` 로 렌더링합니다.

## Streamlit Cloud 배포

1. GitHub에 `app.py` + `bandabi_purple.html` + `requirements.txt` push  
2. [share.streamlit.io](https://share.streamlit.io) → Main file: **`app.py`**  
3. Deploy  

`bandabi_purple.html` 이 레포에 없으면 Streamlit에서 빈 화면/에러가 납니다.

## 백엔드 연결 (추후 — HTML 수정 없이)

현재 단계에서는 **HTML 파일을 변경하지 않습니다.**  
모델·SendGrid 연동은 다음 중 하나로 진행하는 것을 권장합니다.

| 방식 | 설명 |
|------|------|
| HTML 사본 + adapter JS | `bandabi_purple.adapter.html` 등 **별도 파일**에서 fetch만 추가 |
| FastAPI 백엔드 | `backend/` 폴더에 API 두고, adapter에서 `POST /route-analysis` 등 호출 |
| SendGrid | **브라우저/ HTML에 키 금지** → `POST /send-email` 은 서버 env만 |

`app.py`는 지금처럼 **렌더링만** 담당합니다. `BACKEND_API_URL` 주입·HTML 치환은 하지 않습니다.

### 추후 FastAPI 예시 구조

```
backend/
├── main.py
├── requirements.txt
└── .env          # SENDGRID_API_KEY 등 (gitignore)
```

---

## 화면 차이가 날 수 있는 이유 (점검 메모)

| 원인 | 직접 열기 | Streamlit iframe |
|------|-----------|------------------|
| 스크롤 | 문서 전체(body) 스크롤 | iframe 높이(3000px) + `scrolling=True` 이중 스크롤 가능 |
| 뷰포트 | 브라우저 전체 너비 | iframe 너비 100% (거의 동일) |
| Streamlit 크롬 | 없음 | `#MainMenu`, header, footer 숨김 처리 |
| CDN (Tailwind, FA, Chart.js) | 네트워크 필요 | iframe 내부에서도 동일 CDN 로드 |
| `file://` vs `http://localhost` | 일부 브라우저 보안 차이 | Streamlit은 localhost 서빙 |

iframe 높이가 부족하면 하단 탭이 잘릴 수 있습니다 → `app.py`의 `height=3000` 을 키우세요.

---

## 보안

- API Key·SendGrid Key는 HTML/JS에 넣지 않음  
- `.streamlit/secrets.toml` 은 git에 커밋하지 않음  

## 레거시

이전 Streamlit 위젯+엔진 버전: `app_engine_tabs.py`, `modules/` (이 HTML 렌더 방식과 무관)
