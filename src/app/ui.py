# /src/app/ui.py
import os
import sys
import streamlit as st
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.pipeline import initialize_rag_pipeline

# --- UI 스타일링을 위한 CSS (기존과 동일) ---
def apply_custom_styling():
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            color: #FF6B35;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            color: black;
        }
        .user-message {
            background-color: #E3F2FD;
            border-left: 4px solid #2196F3;
        }
        .bot-message {
            background-color: #FFF3E0;
            border-left: 4px solid #FF9800;
            font-size: 1.1rem; /* 가독성을 위해 폰트 크기 조정 */
        }
        .sidebar-info {
            background-color: #F5F5F5;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            color: black;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바 UI 구성 ---
def draw_sidebar():
    with st.sidebar:
        st.markdown("### 📋 사용 방법")
        st.markdown("""
        <div class="sidebar-info">
            1. 궁금한 요리나 레시피에 대해 질문하세요.<br>
            2. 백종원 스타일로 친근하게 답변해드립니다.<br>
            3. 대화 기록이 유지되어 연속 질문이 가능합니다.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💡 질문 예시")
        example_questions = [
            "김치찌개 만드는 법 알려줘", "냉라면 레시피가 뭐야?", "간단한 볶음밥 만들기",
            "유부김밥 만드는 방법", "된장찌개 끓이는 법"
        ]
        
        for i, question in enumerate(example_questions):
            if st.button(f"💬 {question}", key=f"example_{i}"):
                # 사용자가 예시 질문을 클릭하면 session_state에 저장
                st.session_state.user_input = question
        
        st.markdown("---")
        if st.button("🗑️ 대화 기록 초기화"):
            st.session_state.messages = []
            st.session_state.session_id = f"streamlit_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()

# --- 메인 UI 및 채팅 로직 ---
def launch_app(qa_chain):
    """
    Streamlit 앱의 UI를 구성하고 실행합니다.
    RAG 체인은 외부(main.py)에서 주입받습니다.
    """
    st.set_page_config(
        page_title="백종원 레시피 챗봇",
        page_icon="👨‍🍳",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    apply_custom_styling()

    # --- 페이지 헤더 ---
    st.markdown('<h1 class="main-header">👨‍🍳 백종원 레시피 챗봇</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # --- 사이드바 렌더링 ---
    draw_sidebar()

    # --- 세션 상태 초기화 ---
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # --- 채팅 기록 표시 ---
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            if role == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>🤔 질문:</strong> {content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message"><strong>👨‍🍳 백주부:</strong><br>{content}</div>', unsafe_allow_html=True)

    # --- 사용자 입력 처리 ---
    # st.chat_input을 사용하면 더 깔끔한 UI를 만들 수 있습니다.
    if prompt := st.chat_input("여기에 질문을 입력하셔유~"):
        st.session_state.user_input = prompt

    # session_state에 user_input이 있으면 처리
    if 'user_input' in st.session_state and st.session_state.user_input:
        user_input = st.session_state.user_input
        # 처리 후에는 다시 None으로 만들어 중복 실행 방지
        st.session_state.user_input = None

        # 사용자 메시지를 채팅 기록에 추가하고 다시 그리기
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("🤔 백주부가 열심히 생각하고 있어유..."):
            try:
                # 주입받은 qa_chain을 사용하여 답변 생성
                response = qa_chain.invoke(
                    {"input": user_input},
                    config={"configurable": {"session_id": st.session_state.session_id}}
                )
                bot_response = response.get('answer', '죄송해유, 답변을 생성하는 데 문제가 생겼어유.')
                
                # 봇 응답을 채팅 기록에 추가
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
            except Exception as e:
                st.error(f"❌ 답변 생성 중 오류가 발생했어유: {str(e)}")
        
        # 새로운 메시지를 화면에 표시하기 위해 rerun
        st.rerun()

    # --- 대화 시작 전 안내 메시지 ---
    if not st.session_state.messages:
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem; background-color: #F8F9FA; border-radius: 10px; margin: 2rem 0; color: black;">
                <h3>👋 안녕하세요! 백주부입니다!</h3>
                <p>궁금한 요리나 레시피에 대해 뭐든 물어보셔유~</p>
                <p>왼쪽 사이드바의 예시 질문을 클릭하거나 아래 입력창에 직접 질문을 입력해보세유!</p>
            </div>
            """, unsafe_allow_html=True
        )


# 단, 혹시 직접 실행하는 경우에는 안내 메시지만 출력
if __name__ == "__main__":
    rag_chain = initialize_rag_pipeline()
    if rag_chain:
        launch_app(rag_chain)
    else:
        st.error("❌ RAG 파이프라인 초기화에 실패했습니다.")