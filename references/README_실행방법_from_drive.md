# AIVLE School 학습도우미 코드 패키지

## 구성
- `01_백서_작성_및_RAG_파이프라인_구축_완성본.ipynb`: 교안 1일차 미션 2용 완성 노트북
- `rag_utils.py`: RAG 파이프라인 공통 모듈
- `app.py`: Hugging Face Space + Streamlit 배포용 앱
- `requirements.txt`: 설치 라이브러리 목록
- `AIVLE School 백서.pdf`: 기본 백서 파일

## Colab 실행
1. Google Drive의 `project04` 폴더에 `AIVLE School 백서.pdf`, `api_key.txt`, 완성 노트북을 업로드한다.
2. `api_key.txt`는 다음 형식 중 하나로 작성한다.
   - `OPENAI_API_KEY=sk-...`
   - 또는 API Key 한 줄만 입력
3. 노트북을 위에서부터 순서대로 실행한다.

## Streamlit 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Hugging Face Space 배포
1. Space SDK를 Streamlit으로 만든다.
2. `app.py`, `rag_utils.py`, `requirements.txt`, 필요 시 `AIVLE School 백서.pdf`를 업로드한다.
3. Space Settings > Secrets에 `OPENAI_API_KEY`를 등록한다.
4. 앱에서 PDF를 업로드하거나 기본 백서를 사용해 체인을 생성한다.
