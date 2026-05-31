# 반다비 AI — Streamlit Native UI

**`bandabi_purple.html`** 시안의 화면·탭·흐름을 참고해 **Streamlit native UI**로 구현한 프로토타입입니다.  
배포 경로는 **GitHub → Streamlit Cloud → `app.py` 단독 실행**입니다.

## 구조

```
project/
├── app.py                 ← Streamlit native 진입점 (iframe 미사용)
├── bandabi_purple.html    ← 디자인 참고용 (삭제·변경 금지, 배포에서 iframe 렌더 안 함)
├── components/            ← 테마, mock UI, 앱 셸
├── views/                 ← 탭별 화면 (A~I)
├── modules/               ← 엔진 (이번 단계는 status/mock 위주)
├── requirements.txt
└── README.md
```

## 로컬 실행

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

FastAPI·실시간 API 연동·SendGrid 실발송은 **이번 UI 1차 단계 범위가 아닙니다.**

## 화면 구성

| 구분 | 설명 |
|------|------|
| A. 로그인/회원가입 | `@st.dialog` · User/Admin 역할 · `st.session_state` 프로토타입 |
| B. 사용자 시작 | 출발지/목적지 · 알림 토글 · AI 추천 시작 |
| C. MAIN 01 경로분석 | mock 경로 카드 · AI 소견 · 확정/다시하기 |
| D. MAIN 02 버디 | 버디/센터/보호자 카드 |
| E. Program AI | 지도자 추천 |
| F. MAIN 03 리포트 | 성취도·가이드·BT·보호자 공유 |
| G. 일정 추천 | 선호 조건 · 추천 시간 3개 |
| H. 접근성 점검 | 사진 업로드 · mock 결과 · 공문 초안 · SendGrid payload 미리보기 |
| I. 기관 대시보드 | KPI mock · 공공데이터/CSV/RAG status (키 미표시) |

## 김포 제2거점

`김포 제2 반다비 교육거점`은 예정 시설로, 선택 시 경고 후 **김포 반다비체육센터**로 되돌립니다.  
목적지 저장·경로분석에 제2거점이 사용되지 않습니다.

## Git / 보안

- `.env`, `.streamlit/secrets.toml`, `backup/`은 커밋하지 않습니다.
- API Key는 코드·로그·UI에 출력하지 않습니다.

## Chrome 비밀번호 관리자

Streamlit native 로그인 폼은 브라우저 자동완성 인식 가능성이 iframe 방식보다 높습니다.  
Chrome 비밀번호 UI는 브라우저 정책에 따르며 코드로 강제할 수 없습니다.
