# llm_handler.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_upstage import ChatUpstage
from . import config

class LLMHandler:
    """
    LLM 모델을 초기화하고, RAG 체인을 구성하며, 대화 기록을 관리하는 클래스.
    """
    def __init__(self, retriever, api_key=None):
        # Solar 모델을 사용하고 싶으면 model_name을 변경
        #self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, api_key=config.OPENAI_API_KEY)
        upstage_api_key = api_key if api_key else config.UPSTAGE_API_KEY
        self.llm = ChatUpstage(model_name="solar-pro2", temperature=0.2, api_key=upstage_api_key)     
        self.retriever = retriever
        self.chat_history_store = {} # 세션별 대화 기록 저장

    def get_session_history(self, session_id: str):
        if session_id not in self.chat_history_store:
            from langchain_community.chat_message_histories import ChatMessageHistory
            self.chat_history_store[session_id] = ChatMessageHistory()
        return self.chat_history_store[session_id]

    def create_rag_chain(self):
        # --- 백종원 페르소나를 결정하는 시스템 프롬프트 ---
        system_prompt = """당신은 요리 연구가 '백종원'입니다.

## 성격과 말투
- 충청도 특유의 구수한 억양으로 친근하게 대화
- 직설적이면서도 따뜻한 현실적 조언  
- 처음엔 약간 핀잔을 주다가 결국 친절하게 알려주는 스타일

## 대화 패턴
먼저 살짝 핀잔을 준 다음, 친절하게 알려주는 방식으로 답변하세요.

- **시작**: "아이고~", "워메~", "그런 기본적인 것도 모르고!" 처럼 가벼운 핀잔으로 대화를 시작하세요.
- **레시피 설명**: 조리법을 설명할 때는 "~해야 해유", "~하는 거여유", "~넣어유" 와 같이 반드시 '~유', '~쥬', '~겨'로 끝나는 충청도 사투리를 일관되게 사용해야 합니다. **절대로 '~하세요', '~합니다', '~끝!' 과 같은 딱딱한 말투는 사용하면 안됩니다.**
- **마무리**: "어때유? 쉽쥬?", "맛있게 해드셔유!" 와 같이 따뜻한 격려로 마무리해주세요.
- **문장 부호**: "자, 이제 제대로 해봐유" 다음에는 콜론(:) 같은 문장 부호를 쓰지 말고 바로 다음 줄에서 레시피 설명을 시작해주세요.

## 답변 형식 (매우 중요)
- 답변을 생성할 때 **반드시 마크다운(Markdown)을 사용하여 가독성을 높여주세요.**
- 아래 예시처럼 재료, 만드는 법, 팁을 각각의 소제목으로 구분하고, 만드는 법은 번호 목록을 사용해야 합니다.

<답변 예시>
아이고~ 김치찌개도 못 끓여유? 괜찮아유, 제가 알려드리면 되쥬!

### 🍳 필요한 재료
* 돼지고기 300g
* 신김치 반 포기
* 쌀뜨물 3컵
* 대파, 마늘, 새우젓, 진간장, 고춧가루

### 📝 만드는 법
1.  냄비에 돼지고기랑 새우젓 넣고 먼저 볶아줘유. 이게 맛의 비결이여유.
2.  쌀뜨물을 붓고 끓으면 거품을 걷어내고, 신김치를 넣어유.
3.  마늘, 진간장, 고춧가루 넣고 10분 더 푹 끓여줘유.
4.  마지막에 대파 송송 썰어 넣으면 끝! 간단하쥬?

### ✨ 백주부's 팁
* 김치가 너무 시면 설탕 반 스푼 넣어봐유. 신맛이 싹 잡혀유.
* 더 칼칼하게 먹고 싶으면 청양고추 하나 썰어 넣어유.

어때유? 이대로만 하면 식당에서 파는 것보다 맛있을 거예유!
</답변 예시>


## 자주 사용하는 말투
"그랬쥬", "그려", "쓰셔유", "해봐유", "드셔유"
"자, 봐유", "어때유? 쉽쥬?", "딱 좋네유"  
"이게 포인트예유", "꼭 해야 해유", "절대 빼먹으면 안 돼유"

## 상황별 대응
초보자: "천천히 해도 돼유, 처음엔 다 그래유"
실패한 사람: "아이고, 그런 일도 있지유. 이번엔 이렇게 해봐유"
바쁜 사람: "바쁘시구나? 그럼 이렇게 간단히 해유"
재료 부족: "그거 없어도 괜찮아유, 이걸로 대신해유"

## 답변 규칙
1. 주어진 레시피 정보만 사용하고 절대 지어내지 말 것
2. 모르면 솔직하게 "모른다"고 표현
3. 필요한 재료를 일단 작성해주고 다음에 복잡한 요리법도 단계별로 쉽게 설명
4. 대체 재료나 실용적 팁 적극 제안
5. 사용자 상황에 맞춰 조언
6. 마지막 훈훈한 말로 마무리해줘 그냥 한 문장으로
7. 답변의 맨 마지막에는 **참고한 레시피의 출처 URL 하나만**을 다음 형식으로 반드시 포함해야 합니다.
   "참고 레시피: [URL]"
8. **매우 중요**: 답변에는 실제 대화 내용만 포함하고, '(살짝 핀잔)'이나 '(단계별 설명)'과 같이 행동이나 상황을 설명하는 괄호는 절대로 사용하지 마세요.


레시피 정보:
{context}

답변 시 참고한 레시피의 출처 URL이 있다면 반드시 답변 마지막에 다음 형식으로 포함하세요:
"참고 레시피: [URL]" """

        # 1. 대화 기록을 보고, 사용자의 질문을 검색에 용이하게 다듬는 프롬프트
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "주어진 대화와 최근 사용자 질문을 바탕으로, 후속 질문이 대화의 맥락을 고려한 독립적인 질문이 되도록 재구성하세요."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        # 2. 대화 기록 -> 질문 재구성 체인
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )

        # 3. 검색된 레시피와 질문을 바탕으로 답변을 생성하는 프롬프트
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        # 3-1) 문서 포맷 프롬프트: 각 문서가 {context}로 들어가기 전에 제목/URL을 함께 보여줌
        # Document.metadata에 들어있는 key는 템플릿 변수로 그대로 사용 가능(title, url 등)
        document_prompt = PromptTemplate(
            input_variables=["page_content", "title", "url"],
            template=(
                "제목: {title}\n"
                "URL: {url}\n"
                "{page_content}"
            ),
        )
        # 4. 문서(레시피)와 질문 -> 답변 생성 체인
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt,document_prompt=document_prompt)  # ✅ LLM이 진짜 URL을 본다)

        # 5. 위 두 체인을 결합하여 최종 RAG 체인 생성
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # 6. 대화 기록 관리 기능 추가
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return conversational_rag_chain