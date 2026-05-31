# 반다비 AI — HTML 프로토타입 (Streamlit 배포)

김포 반다비 AI 서비스 **완성형 HTML 프론트**(`bandabi_purple.html`)를 Streamlit Community Cloud에서 그대로 보여 주는 진입점입니다.  
UI·화면 전환·로그인/회원가입 흐름은 HTML/JS mock을 유지하며, **AI·SendGrid 등 실 API는 아직 연결하지 않습니다.**

## 프로젝트 구조

```
project/
├── app.py                 # Streamlit 진입 — st.components.v1.html() 로 HTML 렌더
├── bandabi_purple.html    # 완성형 UI (Downloads 시안과 동일)
├── requirements.txt       # streamlit
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

**레거시 (선택):** 이전 Streamlit 위젯+엔진 버전은 `app_engine_tabs.py`, `modules/`, `components/` 에 보관되어 있습니다.

---

## 로컬 실행

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

브라우저에서 HTML 프로토타입 전체(로그인 모달 → 탭 전환 → AI mock)가 iframe 안에 표시됩니다.

---

## Streamlit Community Cloud 배포

1. GitHub에 이 폴더 push ( **`bandabi_purple.html` 반드시 포함** )
2. [share.streamlit.io](https://share.streamlit.io) → **New app**
3. **Main file path:** `app.py`
4. (선택) **Secrets** — 백엔드 URL만 미리 넣을 수 있음:

```toml
BACKEND_API_URL = "https://your-api.example.com"
```

5. **Deploy**

> SendGrid·OpenRouter 등 **API Key는 HTML/JS에 넣지 마세요.** Streamlit Secrets 또는 백엔드 환경변수만 사용합니다.

---

## 백엔드 API 연결 (추후)

모델링이 끝난 **FastAPI(또는 별도) 백엔드**를 붙일 때 권장 구조:

```
project/
├── app.py
├── bandabi_purple.html
├── requirements.txt
└── backend/              # 추후 생성
    ├── main.py           # FastAPI
    ├── requirements.txt
    └── .env              # SENDGRID_API_KEY 등 (gitignore)
```

### 데이터 흐름

| 기능 | 프론트 (HTML) | 백엔드 | 비고 |
|------|---------------|--------|------|
| 경로 분석 | `triggerAiEngine()` | `POST /route-analysis` | mock → API JSON |
| 일정 추천 | `runScheduleOptimize()` | `POST /schedule-optimize` | |
| 비전 점검 | `startVisionScan()` | `POST /vision-analyze` | 이미지 multipart/base64 |
| 이메일 미리보기 | `refreshSendGridPayload()` | `POST /email/preview` | payload 검증만 |
| **실제 발송** | `prepareSendGridEmail()` | **`POST /send-email`** | **SendGrid는 백엔드에서만** |

HTML `bandabi_purple.html` 스크립트 상단에 `window.BACKEND_API_URL` 이 주입됩니다 (`app.py`가 `__BACKEND_API_URL__` 치환).

### JS 연결 예시 (나중에 mock 교체)

```javascript
async function callRouteAnalysis(payload) {
  const response = await fetch(`${window.BACKEND_API_URL}/route-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}
```

`triggerAiEngine()` 안에서 `routeInfo()` + `setTimeout` 대신 위 API 결과를 `#route-title`, `#route-risk` 등에 매핑하면 됩니다.

### SendGrid 보안

```
HTML (payload만 생성)
  → POST /send-email (백엔드)
    → SendGrid API (서버 env의 SENDGRID_API_KEY)
```

브라우저에서 SendGrid를 직접 호출하면 API Key가 노출됩니다.

---

## HTML에 표시된 [BACKEND HOOK] 함수

`bandabi_purple.html` 내 주석으로 표시된 후보:

- `triggerAiEngine()` — 경로 분석
- `runScheduleOptimize()` — 일정 최적화
- `startVisionScan()` — 비전 분석
- `refreshSendGridPayload()` — 발송 payload 미리보기
- `prepareSendGridEmail()` — 발송 준비 (실발송은 `/send-email`)

---

## 문제 해결

| 증상 | 조치 |
|------|------|
| `HTML 파일을 찾을 수 없습니다` | `bandabi_purple.html`을 `app.py`와 같은 폴더에 배치 |
| iframe 높이 부족 | `app.py`의 `components.html(..., height=2400)` 값 조정 |
| CDN 차단 | Tailwind/Font Awesome CDN 네트워크 확인 |

---

## 보안 체크리스트

- [ ] `.streamlit/secrets.toml` / `.env` 는 git에 커밋하지 않음
- [ ] HTML·JS에 API Key 문자열 없음
- [ ] SendGrid 발송은 백엔드 전용
