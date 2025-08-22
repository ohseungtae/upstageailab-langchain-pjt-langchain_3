import requests
from bs4 import BeautifulSoup
import time
import json
import random

class RecipeCrawler:
    """
    재료 추출 로직을 대폭 강화하여 모든 재료를 정확하게 크롤링하는 버전.
    """
    def __init__(self):
        self.base_url = "https://www.10000recipe.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
        }

    # 페이지 구간을 정해서 백종원 레시피 URL을 가져오는 기능은 그대로 유지합니다.
    def get_baek_recipe_urls(self, start_page=1, end_page=5):
        recipe_urls = []
        print(f"'백종원' 검색 결과 {start_page}페이지부터 {end_page}페이지까지 URL 수집을 시작합니다.")
        
        for page in range(start_page, end_page + 1):
            search_url = f"{self.base_url}/recipe/list.html?q=%EB%B0%B1%EC%A2%85%EC%9B%90&page={page}"
            try:
                response = requests.get(search_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.select('li.common_sp_list_li a.common_sp_link')
                
                if not links:
                    print(f"{page} 페이지에서 더 이상 레시피를 찾을 수 없어 수집을 중단합니다.")
                    break

                for link in links:
                    recipe_urls.append(link['href'])
                
                print(f"  > {page} 페이지에서 {len(links)}개의 URL 수집 완료.")
                time.sleep(random.uniform(1, 2))

            except requests.exceptions.RequestException as e:
                print(f"  > {page} 페이지 요청 중 오류 발생: {e}")
                continue
        
        unique_urls = list(set(recipe_urls))
        print(f"\n총 {len(unique_urls)}개의 고유한 레시피 URL을 수집했습니다.")
        return unique_urls

    # --- 👇 여기가 핵심 수정 부분입니다! 👇 ---
    def scrape_recipe_details(self, recipe_url):
        """개별 레시피 URL로 접속해 상세 정보를 추출합니다. (재료 추출 로직 강화)"""
        full_url = self.base_url + recipe_url
        try:
            response = requests.get(full_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 제목 추출 (기존과 동일)
            title_element = soup.select_one('div.view2_summary h3, div.view2_summary h2')
            title = title_element.get_text(strip=True) if title_element else ""

            # 🎯 재료 추출 로직 개선
            ingredients = []
            ingredient_area = soup.select_one('div#divConfirmedMaterialArea')
            if ingredient_area:
                # <ul> 태그를 모두 찾아서 순회
                ingredient_uls = ingredient_area.find_all('ul')
                for ul in ingredient_uls:
                    # 각 <ul> 안에 있는 <li> 태그들을 순회
                    items = ul.find_all('li')
                    for item in items:
                        # <li> 태그 전체 텍스트를 가져온 후, 불필요한 '구매' 버튼 텍스트와 공백 제거
                        full_text = item.get_text(separator=' ').strip()
                        # '구매' 라는 단어가 포함되어 있으면 그 앞까지만 사용
                        if '구매' in full_text:
                            clean_text = full_text.split('구매')[0].strip()
                        else:
                            clean_text = full_text
                        
                        # 텍스트가 비어있지 않고, 재료 그룹 제목('[재료]', '[양념]' 등)이 아니면 추가
                        if clean_text and not clean_text.startswith('['):
                            ingredients.append(clean_text)

            # 조리 순서 추출 (기존과 동일)
            step_elements = soup.select('div.view_step_cont.media div.media-body')
            steps = []
            if step_elements:
                for i, elem in enumerate(step_elements):
                    step_text = elem.get_text(strip=True)
                    if step_text:
                        steps.append(f"단계 {i+1}: {step_text}")

            if not title or not ingredients or not steps:
                return None

            recipe_id = recipe_url.split('/')[-1]
            return {
                'id': recipe_id,
                'title': title,
                'ingredients': ', '.join(ingredients), # 리스트를 하나의 문자열로 합침
                'steps': ' '.join(steps),
                'url': full_url
            }
        except Exception as e:
            print(f"  > '{recipe_url}' 파싱 중 오류 발생: {e}")
            return None

    def run(self, start_page=1, end_page=5, output_filename='baek_recipes.json'):
        """'백종원' 레시피 크롤링 전체 과정을 실행하고 결과를 JSON으로 저장합니다."""
        recipe_urls = self.get_baek_recipe_urls(start_page, end_page)
        
        if not recipe_urls:
            print("수집된 URL이 없어 크롤링을 종료합니다.")
            return

        all_recipes = []
        total_count = len(recipe_urls)
        print(f"\n총 {total_count}개의 레시피 상세 정보 수집을 시작합니다.")

        for i, url in enumerate(recipe_urls):
            print(f"({i+1}/{total_count}) '{url}' 크롤링 중...")
            details = self.scrape_recipe_details(url)
            
            if details:
                all_recipes.append(details)
            
            time.sleep(random.uniform(1, 1.5))

        if not all_recipes:
            print("\n크롤링 결과, 유효한 레시피가 없습니다.")
            return
            
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, ensure_ascii=False, indent=4)
        print(f"\n크롤링 완료! 총 {len(all_recipes)}개의 백종원 레시피를 '{output_filename}' 파일에 저장했습니다.")