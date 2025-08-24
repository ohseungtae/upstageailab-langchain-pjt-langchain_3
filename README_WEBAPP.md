# 백종원 레시피 챗봇 웹앱 🍳

백종원 스타일의 친근한 요리 레시피 챗봇을 웹 인터페이스로 사용할 수 있습니다.

## 🚀 빠른 시작

### 1. 벡터 DB 준비 (최초 1회)
```bash
python main.py --rebuild-db
```

### 2. 웹앱 실행
```bash
# 방법 1: 스마트 런처 (권장)
python launch_chatbot.py

# 방법 2: 직접 실행
streamlit run streamlit_app.py
```

### 3. 브라우저에서 접속
웹앱이 실행되면 자동으로 브라우저가 열리거나, 다음 주소로 접속하세요:
```
http://localhost:8501
```

## 🎯 주요 기능

### 💬 대화형 챗봇
- 백종원 스타일의 친근한 말투로 요리 레시피 안내
- 연속 대화 지원 (이전 대화 내용 기억)
- 실시간 응답

### 🎨 사용자 친화적 인터페이스
- 깔끔한 채팅 UI
- 예시 질문 버튼 제공
- 대화 기록 초기화 기능
- 반응형 디자인

### 🔍 스마트 검색
- RAG (Retrieval-Augmented Generation) 기반
- 백종원 레시피 데이터베이스에서 정확한 정보 검색
- 출처 정보 제공

## 💡 사용 예시

### 질문 예시
- "김치찌개 만드는 법 알려줘"
- "냉라면 레시피가 뭐야?"
- "간단한 볶음밥 만들기"
- "유부김밥 만드는 방법"
- "된장찌개 끓이는 법"

### 연속 질문
- "김치찌개 만드는 법 알려줘"
- "거기서 돼지고기 대신 소고기 써도 돼?"
- "몇 인분 기준이야?"

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: LangChain + Upstage AI
- **Vector DB**: ChromaDB
- **Embeddings**: Upstage Solar Embedding
- **LLM**: Upstage Solar Pro2

## 📁 파일 구조

```
upstageailab-langchain-pjt-langchain_3/
├── streamlit_app.py          # 메인 웹앱 파일
├── launch_chatbot.py         # 스마트 웹앱 런처 (권장)
├── main.py                   # CLI 버전 (DB 구축용)
├── modules/                  # 핵심 모듈들
│   ├── config.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── llm_handler.py
│   └── ...
├── chroma_db/               # 벡터 데이터베이스
├── preprocessed_data/       # 전처리된 레시피 데이터
└── .env                     # API 키 설정
```

## 🔧 문제 해결

### 벡터 DB 오류
```bash
# DB를 다시 구축하세요
python main.py --rebuild-db
```

### API 키 오류
`.env` 파일에 Upstage API 키가 올바르게 설정되어 있는지 확인하세요:
```
UPSTAGE_API_KEY=your_api_key_here
```

### 포트 충돌
다른 포트로 실행하려면:
```bash
streamlit run streamlit_app.py --server.port 8502
```

## 🎉 즐거운 요리하세요!

백종원 챗봇과 함께 맛있는 요리를 만들어보세요! 🍳👨‍🍳