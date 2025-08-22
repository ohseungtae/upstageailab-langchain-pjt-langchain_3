# preprocess.py
import json
import re
import os
import glob # --- 추가된 부분 ---

class DataPreprocessor:
    """
    지정된 폴더의 모든 레시피 JSON을 읽어 전처리하고, 하나의 파일로 저장하는 클래스.
    """
    def clean_title(self, title):
        # (이전과 동일)
        stop_words = ['백종원', '레시피', '만들기', '만드는 법', '황금레시피', '꿀맛이네', '초간단', '밑반찬']
        for word in stop_words:
            title = title.replace(word, '')
        title = re.sub(r'\([^)]*\)', '', title)
        title = re.split(r'[#♡~]', title)[0]
        return title.strip()

    def clean_ingredients(self, ingredients):
        # (이전과 동일)
        cleaned = ingredients.replace('\n', ',')
        cleaned = re.sub(r',+', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'(\s*,\s*)+', ', ', cleaned)
        return cleaned.strip(' ,')

    # --- 수정된 부분: 파일 하나가 아닌 폴더 전체를 처리하도록 변경 ---
    def run(self, input_dir, output_filepath):
        # 입력 폴더 안에 있는 모든 .json 파일을 찾습니다.
        json_files = glob.glob(os.path.join(input_dir, '*.json'))
        
        if not json_files:
            print(f"WARNING: '{input_dir}' 폴더에 JSON 파일이 없어 전처리를 건너뜁니다.")
            return False
        
        print(f"INFO: 총 {len(json_files)}개의 JSON 파일에 대한 전처리를 시작합니다.")
        
        all_recipes = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 각 파일의 레시피 리스트를 불러와서 전체 리스트에 추가
                    all_recipes.extend(json.load(f))
            except Exception as e:
                print(f"WARNING: '{file_path}' 파일을 읽는 중 오류 발생: {e}")
                continue
        
        print(f"INFO: 총 {len(all_recipes)}개의 레시피 데이터 전처리를 시작합니다.")
        
        processed_recipes = []
        for recipe in all_recipes:
            processed_recipe = recipe.copy()
            processed_recipe['title'] = self.clean_title(recipe.get('title', ''))
            processed_recipe['ingredients'] = self.clean_ingredients(recipe.get('ingredients', ''))
            
            title = processed_recipe['title']
            ingredients = processed_recipe['ingredients']
            steps = recipe.get('steps', '')
            
            combined_text = (f"요리 제목: {title}\n"
                             f"필요한 재료: {ingredients}\n"
                             f"만드는 법: {steps}")
            processed_recipe['combined_text'] = combined_text
            processed_recipes.append(processed_recipe)
            
        # 전처리된 모든 레시피를 하나의 파일로 저장
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True) # 출력 폴더가 없으면 생성
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_recipes, f, ensure_ascii=False, indent=4)
            
        print(f"SUCCESS: 데이터 전처리 및 통합 완료! '{output_filepath}'에 저장했습니다.")
        return True