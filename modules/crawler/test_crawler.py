from crawler import RecipeCrawler

if __name__ == "__main__":
    crawler = RecipeCrawler()
    

    # 크롤링 시작할 페이지 번호
    START_PAGE = 51
    # 크롤링 끝낼 페이지 번호
    END_PAGE = 60
    
    # 파일 이름도 구별하기 쉽게 바꿔봅시다.
    output_file = f"baek_recipes_{START_PAGE}-{END_PAGE}pages.json"

    crawler.run(
        start_page=START_PAGE, 
        end_page=END_PAGE,
        output_filename=output_file
    )