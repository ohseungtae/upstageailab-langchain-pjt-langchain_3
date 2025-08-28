# /src/core/pipeline.py

import os
from langchain.storage import InMemoryStore

# 변경된 경로에 맞게 import 경로 수정
from src.core import config
from src.rag_components.vector_store import VectorStoreManager
from src.rag_components.retriever import AdvancedRetriever
from src.rag_components.llm_handler import LLMHandler
from src.utils.docstore import register_parent_docs # utils_docstore.py는 src/utils/docstore.py로 이동했다고 가정

def initialize_rag_pipeline():
    """
    RAG 파이프라인 전체를 초기화하고 QA 체인을 반환합니다.
    이 함수는 Streamlit 앱과 성능 평가에서 공통으로 사용됩니다.
    """
    print("--- RAG 시스템을 로드합니다... ---")
    
    if not os.path.exists(config.CHROMA_DB_PATH):
        print(f"CRITICAL: 벡터 DB가 '{config.CHROMA_DB_PATH}' 경로에 존재하지 않습니다.")
        print("먼저 `python main.py build-db`를 실행하여 DB를 구축해주세요.")
        return None

    # 1. VectorStore 및 Docstore 로드
    vs_manager = VectorStoreManager()
    vectorstore = vs_manager.load()
    
    docstore = InMemoryStore()
    parent_documents = vs_manager._load_documents_from_json(config.MERGED_PREPROCESSED_FILE)
    register_parent_docs(docstore, parent_documents)

    if not vectorstore:
        print("CRITICAL: 벡터 DB 로드에 실패했습니다.")
        return None

    # 2. Retriever 설정
    adv_retriever = AdvancedRetriever(vectorstore, docstore)
    retriever = adv_retriever.get_retriever()
    
    # 3. LLM 핸들러 및 RAG 체인 생성
    llm_handler = LLMHandler(retriever=retriever)
    rag_chain = llm_handler.create_rag_chain()
    
    print("--- RAG 시스템 로드 완료 ---")
    return rag_chain