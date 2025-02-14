import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoogleMapsReviewCrawler:
    def __init__(self):
        # Khởi tạo webdriver với ngôn ngữ tiếng Việt
        chrome_options = Options()
        chrome_options.add_argument("--lang=vi")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("prefs", {"intl.accept_languages": "vi,vi-VN"})

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def search_places(self, query, location="Hà Nội"):
        """Tìm kiếm các địa điểm trên Google Maps và cuộn đến khi hết danh sách"""
        self.driver.get("https://www.google.com/maps")

        # Nhập từ khóa tìm kiếm
        search_box = self.wait.until(EC.presence_of_element_located(
            (By.ID, "searchboxinput")))
        search_box.clear()
        search_box.send_keys(f"{query} {location}")
        search_box.send_keys(Keys.RETURN)

        # Đợi kết quả xuất hiện
        time.sleep(3)

        # Lấy danh sách chứa các địa điểm (thanh cuộn bên trái)
        try:
            scrollable_div = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='feed']")))
        except:
            print("Không tìm thấy danh sách địa điểm.")
            return []

        # Cuộn đến khi thấy thông báo "Bạn đã xem hết danh sách này."
        last_height = -1
        while True:
            self.driver.execute_script("arguments[0].scrollTop += 500;", scrollable_div)
            time.sleep(1)  # Đợi tải dữ liệu

            # Kiểm tra nếu có dòng chữ "Bạn đã xem hết danh sách này."
            try:
                end_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Bạn đã xem hết danh sách này.')]")
                if end_text.is_displayed():
                    print("Đã cuộn hết danh sách.")
                    break
            except:
                pass  # Nếu chưa thấy dòng chữ, tiếp tục cuộn


        # Thu thập links của các địa điểm
        place_links = []
        places = self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")  # Selector cho link địa điểm
        for place in places:
            link = place.get_attribute("href")
            if link and "google.com/maps/place" in link:
                place_links.append(link)

        return place_links
    
    def get_reviews(self, place_url, max_reviews=1000):
        self.driver.get(place_url)
        
        # Đợi và click vào tab review
        reviews_tab = self.wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button[role="tab"][aria-label*="Bài đánh giá"]'
        )))
        reviews_tab.click()
        time.sleep(2)

        collected_reviews = []
        processed_reviews = set()
        last_height = 0
        same_height_count = 0
        max_same_height = 3  # Số lần chiều cao không đổi tối đa

        while len(collected_reviews) < max_reviews:
            try:
                # Tìm container chính chứa reviews
                reviews_container = self.wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'
                )))
                
                # Lấy chiều cao hiện tại của container
                current_height = self.driver.execute_script(
                    'return arguments[0].scrollHeight', reviews_container
                )

                # Kiểm tra nếu chiều cao không thay đổi
                if current_height == last_height:
                    print("Chiều cao không thay đổi")
                    same_height_count += 1
                    if same_height_count >= max_same_height:
                        print("Đã đạt đến cuối danh sách reviews")
                        break
                else:
                    same_height_count = 0
                    last_height = current_height

                # Lấy danh sách reviews hiện tại
                review_elements = reviews_container.find_elements(By.CSS_SELECTOR, 'div.MyEned')
                
                for review in review_elements:
                    try:
                        # Cuộn đến review hiện tại
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
                            review
                        )
                        time.sleep(0.3)

                        # Lấy nội dung review
                        review_text = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd').text
                        review_key = hash(review_text)

                        if review_key in processed_reviews:
                            continue

                        # Lấy rating
                        try:
                            rating_element = self.driver.find_element(By.CSS_SELECTOR, 'span.kvMYJc')
                            rating_text = rating_element.get_attribute("aria-label")
                            rating = int(rating_text.split(" ")[0]) if rating_text else 0
                        except:
                            rating = None

                        if review_text.strip():
                            review_data = {
                                "rating": rating,
                                "text": review_text
                            }
                            collected_reviews.append(review_data)
                            processed_reviews.add(review_key)
                            print(f"Đã lấy được {len(collected_reviews)} đánh giá.")

                        if len(collected_reviews) >= max_reviews:
                            return collected_reviews

                    except Exception as e:
                        print(f"Lỗi khi xử lý review: {e}")
                        continue

                # Cuộn container xuống
                self.driver.execute_script("""
                    arguments[0].scrollTo({
                        top: arguments[0].scrollHeight,
                        behavior: 'smooth'
                    });
                    
                    // Thêm cuộn phụ để đảm bảo trigger load more
                    setTimeout(() => {
                        arguments[0].scrollTo({
                            top: arguments[0].scrollHeight + 100,
                            behavior: 'smooth'
                        });
                    }, 500);
                """, reviews_container)
                
                # Đợi để content load
                time.sleep(2)

            except Exception as e:
                print(f"Lỗi khi cuộn: {e}")
                break
        
        if 

        print(f"Đã hoàn thành, tổng cộng {len(collected_reviews)} đánh giá")
        return collected_reviews
    
    def crawl_multiple_places(self, query, location="Hà Nội", max_places=1000, max_reviews_per_place=1000):
        """Thu thập reviews từ nhiều địa điểm"""
        # Tìm kiếm địa điểm
        place_links = self.search_places(query, location)
        
        # Thu thập reviews từ mỗi địa điểm
        if max_places > len(place_links):
            max_places = len(place_links)
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


if __name__ == "__main__":
    # get = GoogleMapsReviewCrawler()
    # place_links = get.search_places("spa chăm sóc da", "Hà Nội")
    # print("Tìm thấy", len(place_links), "địa điểm.")
    # for place_url in place_links:
    #     print("Đang lấy dữ liệu từ", place_url)
    #     reviews = get.get_reviews(place_url)
    #     print("Đã lấy được", len(reviews), "đánh giá.")
    #     print(reviews)
    #     break

    crawler = GoogleMapsReviewCrawler()
    try:
        reviews = crawler.crawl_multiple_places(
            query="spa chăm sóc da",
            location="Hà Nội",
            max_places=100,
            max_reviews_per_place=1000
        )
        
        crawler.save_to_csv(reviews, 'spa_reviews.csv')
        
        print(f"Đã thu thập được {len(reviews)} reviews")
        
    finally:
        crawler.close()