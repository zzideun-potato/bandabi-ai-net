# DX LangGraph 기반 RAG 구현 PDF 요약

이 문서는 Google Drive의 `[참고] DX_LangGraph 기반 RAG 구현.pdf`에서 반다비 Streamlit 프로젝트에 필요한 개념만 요약한 참고 문서입니다.

## 핵심 개념

| 개념 | 의미 | 반다비 적용 |
|---|---|---|
| State | 단계별 결과가 쌓이는 상태 객체 | 질문, 의도, 검색결과, 점수, 답변 저장 |
| Node | 특정 작업 수행 단위 | RAG 검색, 점수 계산, 리포트 생성, 비전검증 |
| Edge | 노드 간 연결 | 입력 → 의도분류 → 기능 실행 |
| Conditional Edge | 조건에 따라 다른 경로 선택 | 경로분석/리포트/비전/공문 등 음성명령 라우팅 |
| Reflection | 결과가 부족할 때 재작업 | 검색결과 부족 시 query expansion 또는 fallback |
| End Node | 최종 출력 | 사용자에게 카드/리포트/공문 초안 표시 |

## 반다비 적용 권장

1차 구현에서는 LangGraph를 필수로 쓰지 말고, 단순 라우터 함수로 구현하세요.

```text
사용자 입력 또는 음성명령
→ intent 분류
→ 기능별 함수 호출
→ 결과 카드 출력
```

2차 고도화에서 LangGraph를 optional로 붙입니다.

## 오류 방지 지침

- `langgraph`는 설치/버전 이슈가 생길 수 있으므로 MVP 필수 import로 두지 마세요.
- 음성명령 라우팅은 먼저 if/elif 또는 dict router로 구현하세요.
- LangGraph는 `ENABLE_LANGGRAPH=true` 같은 옵션일 때만 사용하세요.
