# /src/core/runner.py

import os
import sys
import subprocess
from langchain.storage import InMemoryStore

# --- 프로젝트의 핵심 로직 및 구성요소 import ---
from src.core import config
from src.data_processing.crawler import RecipeCrawler
from src.data_processing.preprocess import DataPreprocessor
from src.rag_components.vector_store import VectorStoreManager
from src.core.pipeline import initialize_rag_pipeline
from src.app.ui import launch_app
from src.evaluation.evaluator import run_evaluation

def run_crawling():
    """데이터 크롤링을 실행합니다."""
    print("--- 1. 데이터 크롤링 시작 ---")
    os.makedirs(config.CRAWLED_DATA_DIR, exist_ok=True)
    if os.listdir(config.CRAWLED_DATA_DIR):
        print(f"INFO: '{config.CRAWLED_DATA_DIR}' 폴더에 파일이 이미 존재하여 크롤링을 건너뜁니다.")
        return

    crawler = RecipeCrawler()
    # 필요한 만큼 크롤링 실행 (예시: 1-3 페이지만)
    crawler.run(start_page=1, end_page=3, output_filename=os.path.join(config.CRAWLED_DATA_DIR, "baek_recipes_1-3.json"))
    # 추가 크롤링이 필요하면 여기에 crawler.run(...)을 더 추가합니다.
    print("--- 크롤링 완료 ---")

def run_preprocessing():
    """크롤링된 데이터의 전처리를 실행합니다."""
    print("\n--- 2. 데이터 전처리 시작 ---")
    if os.path.exists(config.MERGED_PREPROCESSED_FILE):
        print(f"INFO: '{config.MERGED_PREPROCESSED_FILE}' 파일이 이미 존재하여 전처리를 건너뜁니다.")
        return
        
    preprocessor = DataPreprocessor()
    success = preprocessor.run(config.CRAWLED_DATA_DIR, config.MERGED_PREPROCESSED_FILE)
    if not success:
        print("CRITICAL: 데이터 전처리에 실패하여 중단합니다.")
        sys.exit(1) # 오류 발생 시 프로그램 종료
    print("--- 전처리 완료 ---")

def build_vector_db(rebuild=False):
    """전처리된 데이터로 벡터 DB를 구축합니다."""
    print("\n--- 3. 벡터 DB 구축 시작 ---")
    vs_manager = VectorStoreManager()
    
    if not rebuild and os.path.exists(config.CHROMA_DB_PATH):
        print(f"INFO: '{config.CHROMA_DB_PATH}'가 이미 존재합니다. 새로 구축하려면 --rebuild 옵션을 사용하세요.")
        return

    if rebuild:
        print("INFO: --rebuild 옵션에 따라 DB를 새로 구축합니다.")
        
    docstore = InMemoryStore()
    vectorstore = vs_manager.build(docstore=docstore, json_path=config.MERGED_PREPROCESSED_FILE)
    
    if not vectorstore:
        print("CRITICAL: 벡터 DB 구축에 실패하여 중단합니다.")
        sys.exit(1)
    print("--- 벡터 DB 구축 완료 ---")


def launch_streamlit_app():
    """Streamlit 웹 앱 실행"""
    print("\n--- Streamlit 앱을 시작합니다 ---")
    # 내부적으로 streamlit run 호출
    ui_path = os.path.join("src", "app", "ui.py")
    subprocess.run(["streamlit", "run", ui_path])

def run_langsmith_evaluation():
    """LangSmith를 이용한 RAG 성능 평가를 실행합니다."""
    print("\n--- LangSmith 평가를 시작합니다 ---")
    run_evaluation()

