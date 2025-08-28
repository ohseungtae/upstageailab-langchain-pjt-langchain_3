# /src/core/config.py

import os
from dotenv import load_dotenv

# 현재 파일(config.py)의 위치를 기준으로 프로젝트 루트 경로를 계산합니다.
# /src/core/config.py -> /src/core -> /src -> /
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(project_root, '.env'))

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# --- 경로 설정 (새로운 'data' 폴더 구조 반영) ---
DATA_DIR = os.path.join(project_root, "data")
CRAWLED_DATA_DIR = os.path.join(DATA_DIR, "crawled")
PREPROCESSED_DATA_DIR = os.path.join(DATA_DIR, "preprocessed")
EVAL_DATA_DIR = os.path.join(DATA_DIR, "evaluation_sets")

MERGED_PREPROCESSED_FILE = os.path.join(PREPROCESSED_DATA_DIR, "all_recipes_cleaned.json")
EVAL_DATASET_FILE = os.path.join(EVAL_DATA_DIR, "eval_data_with_answers.json")

# --- DB 경로 ---
CHROMA_DB_PATH = os.path.join(project_root, "chroma_db") # 이름은 원하는대로 변경 가능

# --- 전처리 설정 ---
# 0.0 (완전 다름) ~ 1.0 (완전 같음). 0.75는 "꽤 비슷하면 중복으로 보자"는 의미.
SIMILARITY_THRESHOLD = 0.75