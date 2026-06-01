# Codex 인수인계 패키지

HTML UI(`bandabi_purple.html`)를 Streamlit native로 정합하기 위한 **참고 자료 묶음**입니다.

## 포함 파일

| 파일 | 설명 |
|------|------|
| `bandabi_purple.html` | 디자인·플로우 기준 HTML |
| `app.py` | 현재 Streamlit 진입점 스냅샷 |
| `.env.example` | 환경변수 **이름만** (값 없음) |
| `requirements.txt` | Python 의존성 |
| `CODEX_TASK.md` | 구현 요구사항 |
| `SCREENSHOT_GUIDE.md` | 화면 캡처 가이드 |
| `MODULES_OVERVIEW.md` | modules/data/docs 구조 요약 |

## 미포함 (의도적)

- `.env`, `.streamlit/secrets.toml` — **절대 포함하지 않음**
- `views/`, `components/`, `modules/` 소스 — repo 루트에서 작업 (`MODULES_OVERVIEW.md`로 구조만 전달)
- `backup/`, API Key

## 시작 순서

1. `CODEX_TASK.md` 읽기
2. `bandabi_purple.html` 브라우저에서 9화면 확인
3. `SCREENSHOT_GUIDE.md`대로 HTML vs Streamlit 캡처
4. repo 루트에서 `streamlit run app.py`로 현재 1차 구현 확인
5. HTML 정합 작업 진행

## 생성 일시

2026-06-01 (로컬 repo 기준, commit 없음)
