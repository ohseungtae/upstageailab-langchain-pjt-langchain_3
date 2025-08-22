import json
import re
import os

def clean_title(title):
    """
    레시피 제목에서 요리 이름과 관련 없는 불필요한 단어와 특수문자를 제거합니다.
    """
    # 제거할 단어 목록 (계속 추가 가능)
    stop_words = [
        '백종원', '레시피', '만들기', '만드는 법', '황금레시피', 
        '꿀맛이네', '초간단', '밑반찬'
    ]
    
    # 1. '백종원'과 같은 특정 단어 제거
    for word in stop_words:
        title = title.replace(word, '')
        
    # 2. 괄호와 그 안의 내용 제거 (예: (만개의레시피))
    title = re.sub(r'\([^)]*\)', '', title)
    
    # 3. 특수문자 (#, ♡ 등) 및 그 뒤에 오는 내용 제거
    title = re.split(r'[#♡~]', title)[0]
    
    # 4. 양쪽 끝의 공백 제거
    return title.strip()

def clean_ingredients(ingredients):
    """
    재료 문자열의 불필요한 공백, 줄바꿈 등을 제거하고 보기 좋게 정리합니다.
    """
    
    # 2. 여러 개의 쉼표를 하나로 변경 (예: ',,,')
    cleaned = re.sub(r',+', ',', ingredients)
    
    # 3. 여러 개의 공백을 하나의 공백으로 변경
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 4. '쉼표와 공백'이 반복되는 경우 정리 (예: ' , , ')
    cleaned = re.sub(r'(\s*,\s*)+', ', ', cleaned)

        # 1. 줄바꿈 문자(\n)를 쉼표(,)로 변경
    cleaned = cleaned.replace('\n', ' ')
    
    # 5. 양쪽 끝의 쉼표나 공백 제거
    return cleaned.strip(' ,')

def preprocess_recipe(recipe):
    """
    개별 레시피 데이터를 받아 전처리하고, 'combined_text' 필드를 추가합니다.
    """
    # 원본 데이터 복사
    processed_recipe = recipe.copy()
    
    # 각 필드 클리닝
    #processed_recipe['title'] = clean_title(recipe.get('title', ''))
    processed_recipe['ingredients'] = clean_ingredients(recipe.get('ingredients', ''))
    
    # VectorDB에 넣기 좋을 '통합 텍스트' 생성
    #title = processed_recipe['title']
    #ingredients = processed_recipe['ingredients']
    #steps = recipe.get('steps', '')
    
    # 백종원 스타일로 통합 텍스트를 구성
    #combined_text = f"자, 오늘은 '{title}'! 이거 한번 만들어 볼 거에요. 재료는 뭐가 필요하냐믄, {ingredients} 있으면 되고요. 만드는 방법은 아주 쉬워유. {steps}"
    
    #processed_recipe['combined_text'] = combined_text
    
    return processed_recipe

def main(input_filepath, output_filepath):
    """
    JSON 파일을 읽어 전처리를 수행하고, 새로운 JSON 파일로 저장합니다.
    """
    # 입력 파일이 존재하는지 확인
    if not os.path.exists(input_filepath):
        print(f"오류: '{input_filepath}' 파일을 찾을 수 없습니다. 파일 이름이나 경로를 확인해주세요.")
        return

    try:
        # JSON 파일 읽기
        with open(input_filepath, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        print(f"총 {len(recipes)}개의 레시피를 불러왔습니다. 데이터 ...")
        
        # 각 레시피 전처리
        processed_recipes = [preprocess_recipe(recipe) for recipe in recipes]
        
        # 처리된 결과를 새 JSON 파일로 저장
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_recipes, f, ensure_ascii=False, indent=4)
            
        print(f"\n데이터 손질 완료! 총 {len(processed_recipes)}개의 레시피를 '{output_filepath}' 파일에 저장했습니다.")

    except json.JSONDecodeError:
        print(f"오류: '{input_filepath}' 파일이 올바른 JSON 형식이 아님.")
    except Exception as e:
        print(f"작업 중 오류가 발생했습니다: {e}")


if __name__ == '__main__':
    # 여기에 사장님이 크롤링한 파일 이름과, 새로 저장할 파일 이름을 넣으세유.
    # 예시: baek_recipes_1-10pages.json -> baek_recipes_1-10pages_cleaned.json
    INPUT_FILE = 'baek_recipes_51-60pages.json'  # ◀◀◀ 크롤링한 원본 파일 이름
    OUTPUT_FILE = 'baek_recipes1_51_60_cleaned.json' # ◀◀◀ 깨끗하게 손질해서 저장할 파일 이름
    
    main(INPUT_FILE, OUTPUT_FILE)