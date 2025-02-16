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
    
    def get_reviews(self, place_url, max_reviews=1000, max_scrolls=1000):
        """Thu thập reviews từ Google Maps với giới hạn số lần cuộn"""
        self.driver.get(place_url)
        
        # Click vào tab reviews
        reviews_tab = self.wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button[role="tab"][aria-label*="Reviews"]'
        )))
        reviews_tab.click()
        time.sleep(2)
        
        collected_reviews = []
        last_review_count = 0
        no_new_reviews_count = 0
        scroll_count = 0  # Biến đếm số lần cuộn
        
        while len(collected_reviews) < max_reviews and scroll_count < max_scrolls:
            try:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.MyEned')
            except:
                break
                
            # Kiểm tra xem có review mới không
            if len(review_elements) == last_review_count:
                no_new_reviews_count += 1
                if no_new_reviews_count >= 3:
                    break
            else:
                no_new_reviews_count = 0
                
            for review in review_elements[last_review_count:]:
                try:
                    # Cuộn review vào tầm nhìn
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
                        review
                    )
                    time.sleep(0.5)
                    
                    # Lấy nội dung review
                    try:
                        text = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text
                    except:
                        continue
                    
                    # Lấy số sao
                    try:
                        rating_element = self.driver.find_element(By.CSS_SELECTOR, 'span.kvMYJc')
                        rating_text = rating_element.get_attribute("aria-label")
                        rating = int(rating_text.split(" ")[0]) if rating_text else 0
                    except:
                        rating = None
                    
                    # Lấy thời gian
                    try:
                        time_element = review.find_element(By.CSS_SELECTOR, '.rsqaWe').text
                    except:
                        time_element = None
                    
                    review_data = {
                        'rating': rating,
                        'text': text,
                        'time': time_element
                    }
                    
                    # Chỉ thêm review mới và có nội dung
                    if review_data not in collected_reviews and review_data['text'].strip():
                        collected_reviews.append(review_data)
                        print(f"Đã thu thập review {len(collected_reviews)}/{max_reviews}")
                        
                    if len(collected_reviews) >= max_reviews:
                        break
                        
                except Exception as e:
                    print(f"Lỗi khi thu thập review: {e}")
                    continue
            
            last_review_count = len(review_elements)
            
            # Scroll để tải thêm review
            try:
                sidebar = self.driver.find_element(By.CLASS_NAME, 'm6QErb')
                self.driver.execute_script("arguments[0].scrollBy(0, arguments[0].clientHeight);", sidebar)
                time.sleep(2)
                scroll_count += 1  # Tăng số lần cuộn
            except Exception as e:
                print(f"Lỗi khi scroll: {e}")
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
            location="Thành phố Hồ Chí Minh",
            max_places=10,
            max_reviews_per_place=1000
        )
        
        # Lưu kết quả
        crawler.save_to_csv(reviews, 'spa_reviews_sg.csv')
        
        print(f"Đã thu thập được {len(reviews)} reviews")
        
    finally:
        crawler.close()

if __name__ == "__main__":
    main()