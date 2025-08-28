# modules/preprocess.py
import json
import re
import os
import glob
from difflib import SequenceMatcher # --- 추가된 부분 ---

from src.core import config

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

class DataPreprocessor:
    """
    폴더의 모든 JSON을 읽어 전처리하고, 제목 유사도를 기반으로 중복을 제거한 뒤 
    하나의 파일로 저장하는 클래스.
    """
    def clean_title(self, title):
        stop_words = ['백종원', '레시피', '만들기', '만드는 법', '황금레시피', '꿀맛이네', 
                      '초간단', '밑반찬', '백파더', '골목식당']
        for word in stop_words:
            title = title.replace(word, '')
        title = re.sub(r'\([^)]*\)', '', title) # 괄호와 내용 제거
        title = re.sub(r'\[[^)]*\]', '', title) # 대괄호와 내용 제거
        title = re.split(r'[#♡~]', title)[0]
        return title.strip()

    def clean_ingredients(self, ingredients):
        cleaned = ingredients.replace('\n', ',')
        cleaned = re.sub(r',+', ',', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'(\s*,\s*)+', ', ', cleaned)
        return cleaned.strip(' ,')

    # --- 👇 여기가 핵심 수정 부분입니다! (run 메서드 전체 수정) 👇 ---
    def run(self, input_dir, output_filepath, threshold=config.SIMILARITY_THRESHOLD):
        # 1. 모든 JSON 파일 로드 및 병합
        json_files = glob.glob(os.path.join(input_dir, '*.json'))
        if not json_files:
            print(f"WARNING: '{input_dir}' 폴더에 JSON 파일이 없어 전처리를 건너뜁니다.")
            return False
        
        all_recipes = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_recipes.extend(json.load(f))
            except Exception as e:
                print(f"WARNING: '{file_path}' 파일을 읽는 중 오류 발생: {e}")
        
        print(f"INFO: 총 {len(all_recipes)}개의 레시피를 불러왔습니다. 이제 중복 제거를 시작합니다.")

        # 2. 제목 유사도 기반 중복 제거
        unique_recipes = []
        removed_count = 0
        
        # 먼저 모든 레시피의 제목을 깨끗하게 정리
        for recipe in all_recipes:
            recipe['cleaned_title'] = self.clean_title(recipe.get('title', ''))

        for recipe in all_recipes:
            is_duplicate = False
            for unique_recipe in unique_recipes:
                # 깨끗한 제목끼리 비교
                sim_score = similarity(recipe['cleaned_title'], unique_recipe['cleaned_title'])
                if sim_score > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_recipes.append(recipe)
        
        removed_count = len(all_recipes) - len(unique_recipes)
        print(f"INFO: 중복 제거 완료! {removed_count}개의 중복 레시피를 제거했습니다.")
        print(f"INFO: 최종 {len(unique_recipes)}개의 고유한 레시피가 남았습니다.")

        # 3. 살아남은 고유 레시피들만 최종 손질 및 저장
        final_processed_recipes = []
        for recipe in unique_recipes:
            # 재료 손질
            recipe['ingredients'] = self.clean_ingredients(recipe.get('ingredients', ''))
            
            # 최종 제목은 원본 제목이 아닌 깨끗한 제목으로 저장
            recipe['title'] = recipe['cleaned_title']

            # combined_text 생성
            combined_text = (f"요리 제목: {recipe['title']}\n"
                             f"필요한 재료: {recipe['ingredients']}\n"
                             f"만드는 법: {recipe.get('steps', '')}")
            recipe['combined_text'] = combined_text

            # 임시로 사용한 'cleaned_title' 키는 제거
            del recipe['cleaned_title']
            final_processed_recipes.append(recipe)
            
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(final_processed_recipes, f, ensure_ascii=False, indent=4)
            
        print(f"SUCCESS: 최종 데이터 처리 완료! '{output_filepath}'에 저장했습니다.")
        return True