# /main.py

import argparse
import os
import sys

# src 폴더를 파이썬 경로에 추가하여 모듈을 찾을 수 있도록 합니다.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# ✨ 변경된 부분: runner 모듈에서 모든 실행 함수를 import 합니다.
from src.core.runner import (
    run_crawling,
    run_preprocessing,
    build_vector_db,
    launch_streamlit_app,
    run_langsmith_evaluation
)

def main():
    """
    프로젝트의 진입점(Entrypoint) 역할을 하는 메인 함수.
    커맨드 라인 인자를 파싱하여 적절한 작업을 실행합니다.
    """
    parser = argparse.ArgumentParser(
        description="백종원 레시피 RAG 챗봇 프로젝트",
        formatter_class=argparse.RawTextHelpFormatter # 도움말 포맷 개선
    )
    # dest='command'를 통해 어떤 서브파서가 선택되었는지 알 수 있습니다.
    subparsers = parser.add_subparsers(dest="command", required=True, help="실행할 작업 선택")

    # --- 데이터 준비 파이프라인 ---
    # 'prepare-data' 명령어: 데이터 수집부터 DB 구축까지 전체 실행
    parser_data = subparsers.add_parser(
        "prepare-data", 
        help="데이터 수집부터 DB 구축까지 전체 파이프라인을 실행합니다.\n(크롤링 -> 전처리 -> DB 구축)"
    )
    parser_data.add_argument('--rebuild', action='store_true', help="기존 벡터 DB를 무시하고 새로 구축합니다.")

    # --- 개별 데이터 처리 명령어 ---
    # 'build-db' 명령어: 전처리된 데이터로 벡터 DB만 구축
    parser_build = subparsers.add_parser("build-db", help="전처리된 데이터로 벡터 DB를 구축합니다.")
    parser_build.add_argument('--rebuild', action='store_true', help="기존 벡터 DB를 무시하고 새로 구축합니다.")
    
    # --- 앱 실행 및 평가 명령어 ---
    # 'app' 명령어: Streamlit 챗봇 웹 앱 실행
    subparsers.add_parser("app", help="Streamlit 챗봇 웹 앱을 실행합니다.")
    
    # 'evaluate' 명령어: LangSmith로 RAG 성능 평가 실행
    subparsers.add_parser("evaluate", help="LangSmith로 RAG 성능 평가를 실행합니다.")

    args = parser.parse_args()

    # --- 파싱된 명령어에 따라 적절한 함수 호출 ---
    if args.command == "prepare-data":
        run_crawling()
        run_preprocessing()
        build_vector_db(rebuild=args.rebuild)
        print("\n✅ 모든 데이터 준비 파이프라인이 완료되었습니다.")
    elif args.command == "build-db":
        build_vector_db(rebuild=args.rebuild)
    elif args.command == "app":
        launch_streamlit_app()
    elif args.command == "evaluate":
        run_langsmith_evaluation()

if __name__ == '__main__':
    main()