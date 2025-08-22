# vector_store.py
# vector_store.py
import json
import os
import sys
import pysqlite3
# 내장 sqlite3 모듈을 pysqlite3로 덮어쓰기
sys.modules["sqlite3"] = pysqlite3
from langchain_chroma import Chroma
#from langchain_openai import OpenAIEmbeddings
from langchain_upstage import UpstageEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from . import config



class VectorStoreManager:
    """
    전처리된 데이터를 로드하여 벡터 DB를 구축하고 관리하는 클래스.
    """
    def __init__(self, persist_directory=config.CHROMA_DB_PATH):
        self.persist_directory = persist_directory
        self.doc_embedding = UpstageEmbeddings(model="solar-embedding-1-large-passage", api_key=config.UPSTAGE_API_KEY)
        self.query_embedding = UpstageEmbeddings(model="solar-embedding-1-large-query", api_key=config.UPSTAGE_API_KEY)

    
    def _load_documents_from_json(self, json_path):
        if not os.path.exists(json_path):
            print(f"WARNING: '{json_path}' 파일이 존재하지 않습니다.")
            return []
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            # combined_text를 주 내용으로, 나머지를 메타데이터로 저장
            metadata = {
                'id': item.get('id', ''),
                'title': item.get('title', ''),
                'ingredients': item.get('ingredients', ''),
                'url': item.get('url', '')
            }
            doc = Document(page_content=item.get('combined_text', ''), metadata=metadata)
            documents.append(doc)
        return documents

    def build(self, json_path=config.MERGED_PREPROCESSED_FILE):
        print("INFO: 벡터 DB 구축을 시작합니다...")
        
        documents = self._load_documents_from_json(json_path)
        if not documents:
            print("ERROR: 벡터 DB를 구축할 문서가 없습니다. 크롤링 및 전처리를 먼저 실행하세요.")
            return None

        # 다양하게 chunking 방법을 달리하여 QA성능을 높여주세요! -> 여기서 조절
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        print(f"INFO: 총 {len(documents)}개의 문서를 {len(splits)}개의 청크로 분할했습니다.")
        
        # --- 수정: DB 구축 시에는 'passage' 문서용 임베딩 모델 사용 ---
        print("INFO: 'passage' 모델로 문서 임베딩 및 DB 저장을 진행합니다.")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.doc_embedding, # 👈 문서용 모델 사용
            persist_directory=self.persist_directory
        )
        print(f"SUCCESS: 벡터 DB 구축 완료. '{self.persist_directory}'에 저장되었습니다.")
        return vectorstore
        
    def load(self):
        if not os.path.exists(self.persist_directory):
            print("ERROR: 저장된 벡터 DB가 없습니다. 먼저 DB를 구축해야 합니다.")
            return None
            
        # --- 수정: DB 로드(쿼리) 시에는 'query' 질문용 임베딩 모델 사용 ---
        print("INFO: 기존 벡터 DB를 'query' 모델로 불러옵니다...")
        vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.query_embedding # 👈 질문용 모델 사용
        )
        return vectorstore