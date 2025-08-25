import streamlit as st
import os
import sys
from datetime import datetime

# Add the current directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import config
from modules.vector_store import VectorStoreManager
from modules.retriever import AdvancedRetriever
from modules.llm_handler import LLMHandler
from langchain.storage import InMemoryStore

# Page configuration
st.set_page_config(
    page_title="백종원 레시피 챗봇",
    page_icon="👨‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .bot-message {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
    }
    .sidebar-info {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_qa_system():
    """Initialize the QA system (cached to avoid reloading)"""
    try:
        with st.spinner("🔄 QA 시스템을 초기화하고 있습니다..."):
            # Check if vector DB exists
            if not os.path.exists(config.CHROMA_DB_PATH):
                st.error("❌ 벡터 DB가 존재하지 않습니다. 먼저 `python main.py --rebuild-db`를 실행해주세요.")
                st.stop()
            
            # Initialize vector store manager
            vs_manager = VectorStoreManager()
            vectorstore = vs_manager.load()
            
            if not vectorstore:
                st.error("❌ 벡터 DB 로드에 실패했습니다.")
                st.stop()
            
            # Initialize docstore and load parent documents
            docstore = InMemoryStore()
            parent_documents = vs_manager._load_documents_from_json(config.MERGED_PREPROCESSED_FILE)
            doc_ids = [doc.metadata.get("id", str(i)) for i, doc in enumerate(parent_documents)]
            docstore.mset(list(zip(doc_ids, parent_documents)))
            
            # Initialize retriever
            adv_retriever = AdvancedRetriever(vectorstore, docstore)
            retriever = adv_retriever.get_retriever()
            
            # Initialize LLM handler and create QA chain
            llm_handler = LLMHandler(retriever=retriever)
            qa_chain = llm_handler.create_rag_chain()
            
            return qa_chain, llm_handler
            
    except Exception as e:
        st.error(f"❌ 시스템 초기화 중 오류가 발생했습니다: {str(e)}")
        st.stop()

def main():
    # Header
    st.markdown('<h1 class="main-header">👨‍🍳 백종원 레시피 챗봇</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 사용 방법")
        st.markdown("""
        <div class="sidebar-info" style="color: black;">
        \n
        1. 궁금한 요리나 레시피에 대해 질문하세요 \n
        2. 백종원 스타일로 친근하게 답변해드립니다 \n
        3. 대화 기록이 유지되어 연속 질문이 가능합니다
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💡 질문 예시")
        example_questions = [
            "김치찌개 만드는 법 알려줘",
            "냉라면 레시피가 뭐야?",
            "간단한 볶음밥 만들기",
            "유부김밥 만드는 방법",
            "된장찌개 끓이는 법"
        ]
        
        for i, question in enumerate(example_questions):
            if st.button(f"💬 {question}", key=f"example_{i}"):
                st.session_state.example_question = question
        
        st.markdown("---")
        if st.button("🗑️ 대화 기록 초기화"):
            if 'messages' in st.session_state:
                st.session_state.messages = []
            if 'session_id' in st.session_state:
                st.session_state.session_id = f"streamlit_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()
    
    # Initialize QA system
    qa_chain, llm_handler = initialize_qa_system()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message" style="color: black;">
                        <strong>🤔 질문:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message bot-message" style="color: black;">
                        <strong>👨‍🍳 백주부:</strong><br>{message["content"]}
                    </div>
                    """, unsafe_allow_html=True)

    
    # Handle example question clicks
    if 'example_question' in st.session_state:
        user_input = st.session_state.example_question
        del st.session_state.example_question
        process_user_input = True
    else:
        process_user_input = False
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if not process_user_input:
                user_input = st.text_input(
                    "질문을 입력하세요:",
                    placeholder="예: 김치찌개 만드는 법 알려줘",
                    label_visibility="collapsed"
                )
        
        with col2:
            send_button = st.form_submit_button("전송", type="primary", use_container_width=True)
        
        # Process form submission or example question
        if (send_button and user_input) or process_user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get response from QA system
            with st.spinner("🤔 백종원이 생각하고 있습니다..."):
                try:
                    response = qa_chain.invoke(
                        {"input": user_input},
                        config={"configurable": {"session_id": st.session_state.session_id}}
                    )
                    
                    bot_response = response['answer']
                    
                    # Add bot response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    
                    # Rerun to show new messages
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}")
    
    # Welcome message if no conversation yet
    if not st.session_state.messages:
        st.markdown("""
<div style="text-align: center; padding: 2rem; background-color: #F8F9FA; border-radius: 10px; margin: 2rem 0; color: black;">
    <h3>👋 안녕하세요! 백주부입니다!</h3>
    <p>궁금한 요리나 레시피에 대해 뭐든 물어보셔유~</p>
    <p>왼쪽 사이드바의 예시 질문을 클릭하거나 직접 질문을 입력해보세요!</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()