# 반다비 AI — HTML 프로토타입 (Streamlit 렌더링)

완성형 프론트 **`bandabi_purple.html`** 의 UI·탭·기능 흐름을 유지하고, **Streamlit 배포 시 로그인/회원가입만 `app.py` 최상위 화면**에서 처리합니다.

## 구조

```
project/
├── app.py                 ← Streamlit 진입 · 로그인/회원가입 · iframe 렌더
├── bandabi_purple.html    ← 메인 UI (mock 엔진 · 기능 흐름)
├── requirements.txt
└── README.md
```

## 로컬 실행

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

FastAPI·DB·SendGrid 실발송은 **현재 단계에서 사용하지 않습니다.**

## 인증 흐름 (Streamlit 배포)

| 단계 | 처리 위치 | 설명 |
|------|-----------|------|
| 회원가입 | `app.py` | 이름 · 이메일 · 비밀번호(8자+) · 역할 → `st.session_state` |
| 로그인 | `app.py` | 이메일 · 비밀번호 · 역할 → `st.session_state` |
| 앱 진입 | `bandabi_purple.html` (iframe) | 로그인 후에만 렌더 · `BANDABI_BOOTSTRAP`으로 모달 건너뜀 |
| 로그아웃 | `app.py` 상단 버튼 | iframe 내부 로그아웃은 Streamlit 모드에서 안내 토스트만 표시 |

### `st.session_state` 키

- `is_authenticated`
- `user_name`
- `user_email`
- `role` (`B2C` / `B2G`)
- `registered_users` (프로토타입용 in-memory 계정 목록)

※ **프로토타입용 로컬 인증**이며, 실제 DB·서버 보안 인증이 아닙니다.

## Chrome 비밀번호 관리자

| 환경 | 비밀번호 추천·저장·불러오기 |
|------|------------------------------|
| `app.py` Streamlit 최상위 로그인/회원가입 | **인식 가능성 높음** (`st.form` + `autocomplete` 속성 주입) |
| `components.html()` iframe 내부 HTML 폼 | **불안정** — Chrome이 강력한 비밀번호 추천·저장 UI를 표시하지 않을 수 있음 |

**중요:** Chrome 비밀번호 추천 UI는 브라우저가 판단하는 기능입니다. 코드로 강제로 띄울 수 없습니다.  
다만 iframe이 아닌 Streamlit 최상위 화면에 폼을 두어 인식 가능성을 높였습니다.

권장 input 속성 (로그인):

```html
<input type="email" name="email" autocomplete="email" />
<input type="password" name="current-password" autocomplete="current-password" />
```

회원가입:

```html
<input type="password" name="new-password" autocomplete="new-password" />
<input type="password" name="new-password-confirm" autocomplete="new-password" />
```

## HTML 직접 열기 (개발·비교용)

`bandabi_purple.html`을 브라우저에서 직접 열면 **HTML 내부 로그인 모달**이 그대로 동작합니다 (`localStorage` / `sessionStorage` 프로토타입 인증).

Streamlit 배포와는 별도 경로입니다.

## Streamlit Cloud 배포

1. GitHub에 `app.py` + `bandabi_purple.html` + `requirements.txt` push  
2. [share.streamlit.io](https://share.streamlit.io) → Main file: **`app.py`**  
3. Deploy  

## 보안

- API Key·SendGrid Key는 HTML/JS에 넣지 않음  
- `.streamlit/secrets.toml` 은 git에 커밋하지 않음  
- 비밀번호는 프로토타입용이며, 실제 배포 보안 인증으로 간주하지 않음  

## 레거시

- `backend/` — FastAPI 인증 샘플 (현재 Streamlit 단독 배포 경로에서는 미사용)  
- `app_engine_tabs.py`, `modules/` — 이전 Streamlit 위젯+엔진 버전  
