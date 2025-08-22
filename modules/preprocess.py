# preprocess.py
import json
import re
import os
import glob

class DataPreprocessor:
    """
    크롤링된 레시피 JSON 데이터를 불러와 전처리하고 새로운 파일로 저장하는 클래스.
    """
    def clean_title(self, title):
        stop_words = ['백종원', '레시피', '만들기', '만드는 법', '황금레시피', '꿀맛이네', '초간단', '밑반찬']
        for word in stop_words:
            title = title.replace(word, '')
        title = re.sub(r'\([^)]*\)', '', title)
        title = re.split(r'[#♡~]', title)[0]
        return title.strip()


    def clean_ingredients(self, ingredients):
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

    def run(self, input_dir, output_filepath):
        json_files = glob.glob(os.path.join(input_dir, '*.json'))
        if not json_files:
            print(f"WARNING: '{input_dir}' 폴더에 JSON 파일이 없어 전처리를 건너뜁니다.")
            return False
        
        print(f"INFO: 총 {len(json_files)}개의 JSON 파일에 대한 전처리를 시작합니다.")
        
        all_recipes = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_recipes.extend(data)
            except Exception as e:
                print(f"WARNING: '{file_path}' 파일을 읽는 중 오류 발생: {e}")
                continue
        
        print(f"INFO: 총 {len(all_recipes)}개의 레시피를 불러왔습니다. 데이터 전처리를 시작합니다.")
            
        print(f"INFO: 총 {len(all_recipes)}개의 레시피 데이터 전처리를 시작합니다.")
        
            # --- 👇 (중복 제거 로직) 👇 ---
        processed_recipes_dict = {}
        for recipe in all_recipes:
            if not isinstance(recipe, dict) or 'id' not in recipe:
                continue

            recipe_id = recipe['id']
            
            # 아직 추가되지 않은 레시피거나, 새로 들어온 레시피의 재료 정보가 더 풍부하면 덮어쓰기
            if recipe_id not in processed_recipes_dict or len(recipe.get('ingredients', '')) > len(processed_recipes_dict[recipe_id].get('ingredients', '')):
                processed_recipe = recipe.copy()
                #processed_recipe['title'] = self.clean_title(recipe.get('title', ''))
                processed_recipe['ingredients'] = self.clean_ingredients(recipe.get('ingredients', ''))
                
                title = processed_recipe['title']
                ingredients = processed_recipe['ingredients']
                steps = recipe.get('steps', '')
                
                combined_text = (f"요리 제목: {title}\n"
                                 f"필요한 재료: {ingredients}\n"
                                 f"만드는 법: {steps}")
                processed_recipe['combined_text'] = combined_text
                processed_recipes_dict[recipe_id] = processed_recipe

        # 딕셔너리의 값들만 리스트로 변환하여 최종 결과물 생성
        processed_recipes = list(processed_recipes_dict.values())
        print(f"INFO: 중복 제거 후 총 {len(processed_recipes)}개의 고유한 레시피가 남았습니다.")
        # -------------------------------------------------------------
            
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_recipes, f, ensure_ascii=False, indent=4)
            
        print(f"SUCCESS: 데이터 전처리 및 통합 완료! '{output_filepath}'에 저장했습니다.")
        return True
    
        # processed_recipes = []
        # for recipe in all_recipes:
        #     if not isinstance(recipe, dict): continue # 레시피가 딕셔너리 형태가 아니면 건너뛰기
                
        #     processed_recipe = recipe.copy()
        #     #processed_recipe['title'] = self.clean_title(recipe.get('title', ''))
        #     processed_recipe['ingredients'] = self.clean_ingredients(recipe.get('ingredients', ''))
            
        #     title = processed_recipe['title']
        #     ingredients = processed_recipe['ingredients']
        #     steps = recipe.get('steps', '')
            
        #     combined_text = (f"요리 제목: {title}\n"
        #                      f"필요한 재료: {ingredients}\n"
        #                      f"만드는 법: {steps}")
        #     processed_recipe['combined_text'] = combined_text
        #     processed_recipes.append(processed_recipe)
            
        # # 전처리된 모든 레시피를 하나의 파일로 저장
        # os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        # with open(output_filepath, 'w', encoding='utf-8') as f:
        #     json.dump(processed_recipes, f, ensure_ascii=False, indent=4)
            
        # print(f"SUCCESS: 데이터 전처리 및 통합 완료! '{output_filepath}'에 저장했습니다.")
        # return True # 성공했음을 알리기 위해 True 반환