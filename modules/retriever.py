# retriever.py
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .vector_store import VectorStoreManager

class AdvancedRetriever:
    """
    ParentDocumentRetriever를 사용하여 향상된 검색 기능을 제공하는 클래스.
    """
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.store = InMemoryStore() # 부모 문서를 저장할 공간

    def get_retriever(self, parent_splitter_chunk_size=2000, child_splitter_chunk_size=400):
        # 큰 청크로 나눌 스플리터 (부모 청크)
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=parent_splitter_chunk_size)
        # 작은 청크로 나눌 스플리터 (자식 청크, 검색에 사용)
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=child_splitter_chunk_size)
        
        # ParentDocumentRetriever 설정
        # 작은 청크로 검색하고, 결과로는 부모 청크를 반환하여 LLM에 더 많은 맥락을 제공
        retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.store,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
        )
        
        # 여기서 retriever에 문서를 추가해줘야 합니다.
        # main.py에서 VectorStoreManager의 문서를 가져와 추가합니다.
        
        return retriever