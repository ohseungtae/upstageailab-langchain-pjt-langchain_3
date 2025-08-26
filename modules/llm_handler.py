# llm_handler.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_upstage import ChatUpstage
from . import config

class LLMHandler:
    """
    LLM 모델을 초기화하고, RAG 체인을 구성하며, 대화 기록을 관리하는 클래스.
    """
    def __init__(self, retriever):
        # Solar 모델을 사용하고 싶으면 model_name을 변경
        #self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, api_key=config.OPENAI_API_KEY)
        self.llm = ChatUpstage(model_name="solar-pro2", temperature=0.2,api_key=config.UPSTAGE_API_KEY)     
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

시작 표현: "아이고 그것도 몰라유?", "에이~ 그런 기본적인 것도 모르고", "참나, 이런 기본도 안 되나?"
중간 표현: "정신 차려유", "이거 안 하면 망한다니까", "아 답답해라"  
마무리 표현: "그래도 괜찮아유, 알려드릴게유", "자, 이제 제대로 해봐유", "다음엔 더 잘할 수 있을 거예유"

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
7. 답변 끝에 참고한 레시피 출처 URL 명시
8. 마지막으로 전체적으로 대화형으로 대화해줘야해 하고 괄호안에 그 문장에 대한 설명은 하지마

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
        
        # 4. 문서(레시피)와 질문 -> 답변 생성 체인
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

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