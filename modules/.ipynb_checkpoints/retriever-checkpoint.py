# retriever.py
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
#from .vector_store import VectorStoreManager

class AdvancedRetriever:
    """
    ParentDocumentRetriever를 사용하여 향상된 검색 기능을 제공하는 클래스.
    """
    # --- 수정된 부분: __init__에서 store를 받도록 변경 ---
    def __init__(self, vectorstore, store):
        self.vectorstore = vectorstore
        self.store = store # 부모 문서를 저장할 공간

    def get_retriever(self):
        # 자식 청크는 DB 구축 시 이미 생성되었으므로 여기서는 splitter 정의가 필요 없음
        # 하지만 retriever 객체는 구조상 splitter를 필요로 하므로 형식적으로 정의
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
        
        retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.store,
            child_splitter=child_splitter,
            id_key="doc_id"
            # parent_splitter는 add_documents시에만 사용되므로 여기서는 불필요
        )
        return retriever