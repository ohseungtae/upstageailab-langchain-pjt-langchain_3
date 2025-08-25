# vector_store.py
import json
import os
import sys
import sqlite3
# 내장 sqlite3 모듈을 pysqlite3로 덮어쓰기
sys.modules["sqlite3"] = sqlite3
from langchain_community.vectorstores import Chroma
#from langchain_openai import OpenAIEmbeddings
from langchain_upstage import UpstageEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from . import config
import uuid # --- 추가된 부분 ---
from langchain.storage import InMemoryStore # --- 추가된 부분 ---


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

    # --- 👇 여기가 핵심 수정 부분입니다! (DB 구축 로직 변경) 👇 ---
    def build(self, docstore: InMemoryStore, json_path=config.MERGED_PREPROCESSED_FILE):
        print("INFO: ParentDocumentRetriever용 벡터 DB 구축을 시작합니다...")
        
        parent_documents = self._load_documents_from_json(json_path)
        if not parent_documents:
            print("ERROR: 벡터 DB를 구축할 문서가 없습니다.")
            return None

        # 부모 문서(원본 레시피)에 고유 ID를 부여하고 docstore에 저장
        doc_ids = [str(uuid.uuid4()) for _ in parent_documents]
        for i, doc in enumerate(parent_documents):
            doc.metadata["doc_id"] = doc_ids[i] # ✅ 부모 메타데이터에도 기록!
        # docstore에 "doc_id" : doc 저장
        docstore.mset(list(zip(doc_ids, parent_documents)))

        # 자식 문서(잘게 쪼갠 조각) 생성
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
        child_documents = []
        for i, doc in enumerate(parent_documents):
            _id = doc_ids[i]
            splits = child_splitter.split_documents([doc])
            for _doc in splits:
                # 자식 문서의 메타데이터에 부모 문서의 ID를 연결!
                _doc.metadata["doc_id"] = _id
            child_documents.extend(splits)
        
        print(f"INFO: 총 {len(parent_documents)}개의 부모 문서를 {len(child_documents)}개의 자식 청크로 분할했습니다.")
        print("INFO: 'passage' 모델로 자식 청크 임베딩 및 DB 저장을 진행합니다.")

        # 자식 문서를 벡터DB에 저장 (Langchain의 from_documents는 자동 배치 처리 기능이 있음)
        vectorstore = Chroma.from_documents(
            documents=child_documents,
            embedding=self.doc_embedding,
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