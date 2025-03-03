import logging
from playwright.sync_api import sync_playwright

class CategoryParser:
    def __init__(self, booking_url):
        self.booking_url = booking_url
        self.categories = []
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def fetch_categories(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.booking_url, timeout=60000)
            self.logger.info(f"Loaded booking page: {self.booking_url}")
            
            page.wait_for_selector("[data-testid='category-card']", timeout=10000)
            category_elements = page.locator("[data-testid='category-card']")
            category_count = category_elements.count()
            self.logger.info(f"Found {category_count} cabin categories.")
            
            for i in range(category_count):
                category = category_elements.nth(i)
                
                category_name_locator = category.locator("h3")
                category_status_locator = category.locator("button")
                
                if category_name_locator.count() == 0:
                    continue
                
                category_name = category_name_locator.text_content().strip()
                category_status = category_status_locator.text_content().strip() if category_status_locator.count() > 0 else "Unknown"
                
                is_available = "See available cabins" in category_status
                
                self.categories.append({
                    "category_name": category_name,
                    "status": category_status,
                    "available": is_available
                })
            
            browser.close()
        
        return self.categories
    
if __name__ == "__main__":
    test_url = "https://www.expeditions.com/book/some-booking-url"  # Replace with an actual booking URL
    parser = CategoryParser(test_url)
    categories = parser.fetch_categories()
    for category in categories:
        print(category)
