# 🍳 백종원 레시피 RAG QA 봇

이 프로젝트는 '만개의 레시피' 사이트에서 백종원 쉐프의 레시피를 크롤링하고, Upstage의 Solar LLM과 RAG(Retrieval-Augmented Generation) 기술을 사용하여 사용자의 요리 질문에 백종원 쉐프의 말투로 답변하는 QA 봇을 개발하는 것을 목표로 합니다.

## ✨ 주요 기능

-   **데이터 수집**: 특정 키워드("백종원")로 레시피를 검색하여 동적으로 크롤링
-   **데이터 전처리**: 수집된 데이터에서 불필요한 정보를 제거하고 LLM이 이해하기 쉬운 형태로 가공
-   **RAG 기반 QA**: ChromaDB와 `ParentDocumentRetriever`를 사용해 정확도 높은 답변 생성
-   **페르소나 적용**: 시스템 프롬프트를 통해 LLM이 '백종원' 쉐프의 말투와 스타일을 모방하도록 설정
-   **대화 기록 관리**: 이전 대화 내용을 기억하여 연속적인 질문에도 맥락에 맞는 답변 제공
-   **LangSmith 연동**: 모든 처리 과정을 추적하고 성능을 정량적으로 평가

## 📂 프로젝트 구조

```
/recipe-qa-engine/
├── modules/
│   ├── __init__.py
│   ├── config.py             # API 키 및 경로 관리
│   ├── crawler.py            # 레시피 데이터 크롤러
│   ├── preprocess.py         # 데이터 전처리기
│   ├── vector_store.py       # ChromaDB 벡터 저장소 구축
│   ├── retriever.py          # 향상된 RAG 검색기 (Retriever)
│   └── llm_handler.py        # LLM 모델 및 RAG 체인 관리
│
├── crawled_data/             # (Git 추적 안함) 크롤링 원본 데이터
├── preprocessed_data/        # (Git 추-적 안함) 전처리된 데이터
├── chroma_db/                # (Git 추적 안함) 로컬 벡터 DB
│
├── .env                      # (Git 추적 안함) API 키 등 비밀 정보
├── .gitignore                # Git에 올리지 않을 파일/폴더 목록
├── requirements.txt          # 프로젝트 의존성 라이브러리
└── main.py                   # 메인 실행 파일
```

## ⚙️ 설치 및 실행 방법

### 1. 프로젝트 복제

```bash
git clone [https://github.com/ohseungtae/upstageailab-langchain-pjt-langchain_3.git](hhttps://github.com/ohseungtae/upstageailab-langchain-pjt-langchain_3.git)

```

### 2. 가상 환경 설정 및 라이브러리 설치

```bash
# 가상 환경 생성
python -m venv myenv

# 가상 환경 활성화 (Windows)
myenv\Scripts\activate
# 가상 환경 활성화 (macOS/Linux)
source myenv/bin/activate

# 필요 라이브러리 설치
pip install -r requirements.txt
```

### 3. API 키 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래와 같이 API 키와 LangSmith 정보를 입력하세요.

```ini
# .env
OPENAI_API_KEY="sk-..."
UPSTAGE_API_KEY="sk-..."

LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="ls__..."
LANGCHAIN_PROJECT="Recipe QA Engine"
```

### 4. QA 엔진 실행

아래 명령어로 QA 봇을 실행합니다. 처음 실행 시 크롤링, 전처리, DB 구축이 자동으로 진행되며, 이후에는 구축된 DB를 바로 불러옵니다.

```bash
python main.py
```
터미널에서 main.py를 실행할 때 --until-step 이라는 옵션을 붙여서 원하는 단계까지만 실행할 수 있습니다.

1. 크롤링까지만 실행하고 싶을 때
crawled_data 폴더에 원본 JSON 파일들만 생성하고 프로그램을 종료합니다.
```bash
python main.py --until-step crawl
```

2. 전처리까지만 실행하고 싶을 때 (사용자가 원했던 기능!)
크롤링을 하고, 그 데이터로 preprocessed_data 폴더에 all_recipes_cleaned.json 파일까지만 만든 뒤 프로그램을 종료합니다.

```bash
python main.py --until-step preprocess
```

3. 만약 데이터베이스를 처음부터 다시 구축하고 싶다면 `--rebuild-db` 옵션을 사용하세요.

```bash
python main.py --rebuild-db
```

4. 전체 실행 (기존과 동일)
--until-step 옵션을 아예 주지 않거나 run으로 지정하면, 이전처럼 QA 봇 채팅 단계까지 모두 실행됩니다.

```bash
# 옵션을 주지 않는 경우 (기본값 'run')
python main.py

# 명시적으로 'run'을 지정하는 경우
python main.py --until-step run
```


---
이제 이 두 파일을 프로젝트 폴더에 추가하고 깃허브에 올리면, 다른 사람들도 쉽게 프로젝트를 이해하고 사용할 수 있을 겁니다!