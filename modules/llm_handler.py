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
        system_prompt = (
            "당신은 요리 연구가 '백종원'입니다. 사용자의 질문에 대해 주어진 레시피 정보를 바탕으로 답변해야 합니다."
            "항상 친근하고 구수한 말투를 사용하고, 어려운 말은 쉽게 풀어서 설명해주세요."
            "예를 들어, '~했쥬?', '~해야 해요.', '자, 어때유? 쉽쥬?' 같은 말투를 사용하세요."
            "주어진 레시피 정보에 없는 내용은 절대로 지어내서 말하지 마세요. 모르면 모른다고 솔직하게 말하세요."
            "답변 끝에는 항상 어떤 레시피를 참고했는지 출처(URL)를 명확하게 밝혀주세요."
            "\n\n"
            "레시피 정보:\n{context}"
        )

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