import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import re

class GoogleReviewsCrawler:
    def __init__(self):
        # Khởi tạo webdriver
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
    
    def search_places(self, query, location="Hà Nội"):
        """Tìm kiếm các địa điểm trên Google Maps"""
        self.driver.get("https://www.google.com/maps")
        
        # Nhập query tìm kiếm
        search_box = self.wait.until(EC.presence_of_element_located(
            (By.ID, "searchboxinput")))
        search_box.clear()
        search_box.send_keys(f"{query} {location}")
        search_box.send_keys(Keys.RETURN)
        
        # Đợi kết quả hiện ra
        time.sleep(3)
        
        # Thu thập links của các địa điểm
        place_links = []
        places = self.driver.find_elements(By.CLASS_NAME, "hfpxzc")
        for place in places:
            link = place.get_attribute("href")
            if link:
                place_links.append(link)
                
        return place_links
    
    def get_reviews(self, place_url, max_reviews=100):
        """Thu thập reviews với scroll tối ưu"""
        self.driver.get(place_url)
        
        # Click vào tab reviews
        reviews_tab = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[jsaction="pane.rating.moreReviews"]')))
        reviews_tab.click()
        time.sleep(2)
        
        # Tìm panel chứa reviews
        reviews_panel = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[role="feed"]')))
        
        # Thực hiện scroll
        collected_reviews = []
        while len(collected_reviews) < max_reviews:
            # Scroll để load thêm reviews
            self.scroll_reviews(reviews_panel)
            
            # Thu thập reviews mới
            review_elements = reviews_panel.find_elements(
                By.CSS_SELECTOR, 'div[jsaction^="pane.review"]'
            )
            
            for review in review_elements[len(collected_reviews):]:
                try:
                    # Mở rộng review nếu có nút "More"
                    try:
                        more_button = review.find_element(
                            By.CSS_SELECTOR, 'button[jsaction="pane.review.expandReview"]'
                        )
                        self.driver.execute_script("arguments[0].click();", more_button)
                    except:
                        pass
                    
                    # Thu thập thông tin
                    rating = len(review.find_elements(
                        By.CSS_SELECTOR, 'img[src$="star-full"]'
                    ))
                    
                    # Thu thập text với xử lý ngoại lệ
                    try:
                        text = review.find_element(
                            By.CSS_SELECTOR, 'span[jsaction="pane.review.expandReview"]'
                        ).text
                    except:
                        text = review.find_element(
                            By.CSS_SELECTOR, '.wiI7pd'
                        ).text
                    
                    # Thu thập thời gian
                    time_element = review.find_element(
                        By.CSS_SELECTOR, '.rsqaWe'
                    ).text
                    
                    collected_reviews.append({
                        'rating': rating,
                        'text': text,
                        'time': time_element
                    })
                    
                    if len(collected_reviews) >= max_reviews:
                        break
                        
                except Exception as e:
                    print(f"Error extracting review: {e}")
                    continue
            
            # Kiểm tra xem có thêm reviews mới không
            if len(collected_reviews) == len(review_elements):
                break
                
        return collected_reviews

    
    def crawl_multiple_places(self, query, location="Hà Nội", max_places=10, max_reviews_per_place=50):
        """Thu thập reviews từ nhiều địa điểm"""
        # Tìm kiếm địa điểm
        place_links = self.search_places(query, location)
        
        # Thu thập reviews từ mỗi địa điểm
        all_reviews = []
        for i, link in enumerate(place_links[:max_places]):
            print(f"Crawling place {i+1}/{min(len(place_links), max_places)}")
            try:
                place_reviews = self.get_reviews(link, max_reviews_per_place)
                all_reviews.extend(place_reviews)
            except Exception as e:
                print(f"Error crawling place: {e}")
                continue
        
        return all_reviews
    
    def save_to_csv(self, reviews, filename):
        """Lưu reviews vào file CSV"""
        df = pd.DataFrame(reviews)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    def close(self):
        """Đóng browser"""
        self.driver.quit()

def main():
    # Khởi tạo crawler
    crawler = GoogleReviewsCrawler()
    
    try:
        # Thu thập reviews
        reviews = crawler.crawl_multiple_places(
            query="spa chăm sóc da",
            location="Hà Nội",
            max_places=5,
            max_reviews_per_place=20
        )
        
        # Lưu kết quả
        crawler.save_to_csv(reviews, 'spa_reviews.csv')
        
        print(f"Đã thu thập được {len(reviews)} reviews")
        
    finally:
        crawler.close()

if __name__ == "__main__":
    main()