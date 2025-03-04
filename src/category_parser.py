import logging

class CategoryParser:
    def __init__(self, booking_url, page):
        self.booking_url = booking_url
        self.page = page
        self.categories = []
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def fetch_categories(self):
        self.logger.info(f"Navigating to booking page: {self.booking_url}")
        self.page.goto(self.booking_url, timeout=60000)
        
        self.logger.info(f"Loaded booking page: {self.booking_url}")
        
        try:
            self.page.wait_for_selector("[data-testid='category-card']", timeout=10000)
        except Exception as e:
            self.logger.warning(f"No category cards found: {e}")
            return []
        
        category_elements = self.page.locator("[data-testid='category-card']")
        category_count = category_elements.count()
        self.logger.info(f"Found {category_count} cabin categories.")
        
        for i in range(category_count):
            category = category_elements.nth(i)
            
            category_name_locator = category.locator("h3")
            see_available_locator = category.locator("button:text('See available cabins')")
            join_waitlist_locator = category.locator("button:text('Join Waitlist')")
            
            if category_name_locator.count() == 0:
                self.logger.warning(f"Category {i} missing name. Skipping.")
                continue
            
            category_name = category_name_locator.text_content().strip()
            
            if see_available_locator.count() > 0:
                category_status = "Available"
            elif join_waitlist_locator.count() > 0:
                category_status = "Waitlist"
            else:
                category_status = "Unknown"
            
            is_available = category_status == "Available"
            self.logger.info(f"Category {i}: {category_name} - Status: {category_status}")
            
            self.categories.append({
                "category_name": category_name,
                "status": category_status,
                "available": is_available
            })
        
        return self.categories
