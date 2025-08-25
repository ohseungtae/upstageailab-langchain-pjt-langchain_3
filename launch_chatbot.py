#!/usr/bin/env python3
"""
백종원 레시피 챗봇 런처
웹앱 실행 전 필요한 조건들을 확인하고 실행합니다.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_prerequisites():
    """실행 전 필요한 조건들을 확인합니다."""
    print("🔍 시스템 상태를 확인하고 있습니다...")
    
    issues = []
    
    # 1. .env 파일 확인
    if not os.path.exists('.env'):
        issues.append("❌ .env 파일이 없습니다. API 키를 설정해주세요.")
    else:
        print("✅ .env 파일 확인됨")
    
    # 2. 벡터 DB 확인
    if not os.path.exists('chroma_db'):
        issues.append("❌ 벡터 DB가 없습니다. 'python main.py --rebuild-db'를 먼저 실행해주세요.")
    else:
        print("✅ 벡터 DB 확인됨")
    
    # 3. 전처리된 데이터 확인
    preprocessed_file = Path('preprocessed_data/all_recipes_cleaned.json')
    if not preprocessed_file.exists():
        issues.append("❌ 전처리된 데이터가 없습니다. 'python main.py --rebuild-db'를 먼저 실행해주세요.")
    else:
        print("✅ 전처리된 데이터 확인됨")
    
    # 4. Streamlit 설치 확인
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} 설치됨")
    except ImportError:
        issues.append("❌ Streamlit이 설치되지 않았습니다. 'pip install streamlit'을 실행해주세요.")
    
    return issues

def main():
    """메인 실행 함수"""
    print("🚀 백종원 레시피 챗봇을 시작합니다!")
    print("=" * 50)
    
    # 전제 조건 확인
    issues = check_prerequisites()
    
    if issues:
        print("\n⚠️  다음 문제들을 해결해주세요:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 해결 방법:")
        print("   1. API 키 설정: .env 파일에 UPSTAGE_API_KEY=your_key 추가")
        print("   2. 데이터 준비: python main.py --rebuild-db 실행")
        print("   3. 패키지 설치: pip install -r requirements.txt 실행")
        return
    
    print("\n🎉 모든 조건이 충족되었습니다!")
    print("📱 웹앱을 시작합니다...")
    print("🌐 브라우저에서 http://localhost:8501 로 접속하세요")
    print("⏹️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 50)
    
    try:
        # Streamlit 앱 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 챗봇을 종료합니다. 맛있게 해드세유~!")
    except subprocess.CalledProcessError as e:
        print(f"❌ 웹앱 실행 중 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()