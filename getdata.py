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
        """Thu thập reviews từ Google Maps"""
        print(f"Fetching reviews from: {place_url}")
        self.driver.get(place_url)
        
        # Click vào tab reviews
        try:
            reviews_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reviews for')]")))
            self.driver.execute_script("arguments[0].click();", reviews_button)
            time.sleep(2)
        except Exception as e:
            print(f"Error clicking reviews tab: {e}")
            return []
        time.sleep(2)
        
        collected_reviews = []
        last_review_count = 0
        no_new_reviews_count = 0
        
        while len(collected_reviews) < max_reviews:
            # Tìm tất cả reviews hiện tại
            try:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.MyEned')
            except:
                break
                
            # Kiểm tra xem có reviews mới không
            if len(review_elements) == last_review_count:
                no_new_reviews_count += 1
                if no_new_reviews_count >= 3:  # Nếu scroll 3 lần không có reviews mới
                    break
            else:
                no_new_reviews_count = 0
                
            # Xử lý các reviews mới
            for review in review_elements[last_review_count:]:
                try:
                    # Scroll để review hiện tại nằm trong tầm nhìn
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
                        review
                    )
                    time.sleep(0.5)
                    
                    # Mở rộng review nếu có
                    try:
                        more_button = review.find_element(
                            By.CSS_SELECTOR, 'button[jsaction="pane.review.expandReview"]'
                        )
                        self.driver.execute_script("arguments[0].click();", more_button)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Thu thập thông tin
                    rating_element = review.find_element(By.CSS_SELECTOR, 'span.kvMYJc')
                    rating = int(rating_element.get_attribute("aria-label").split(" ")[0]) if rating_element else 0
                    
                    text_element = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd')
                    text = text_element.text if text_element else ""
                    
                    time_element = review.find_element(
                        By.CSS_SELECTOR, '.rsqaWe'
                    ).text
                    
                    review_data = {
                        'rating': rating,
                        'text': text,
                        'time': time_element
                    }
                    
                    if review_data not in collected_reviews:
                        collected_reviews.append(review_data)
                        
                    if len(collected_reviews) >= max_reviews:
                        break
                        
                except Exception as e:
                    print(f"Error extracting review: {e}")
                    continue
            
            last_review_count = len(review_elements)
            
            # Scroll để load thêm reviews
            if not self.scroll_reviews():
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