import logging
from config import BASE_URL

import logging
from config import BASE_URL  # Ensure you import BASE_URL

class CategoryParser:
    def __init__(self, booking_url, page):
        # Ensure booking_url is absolute
        if not booking_url.startswith("http"):
            booking_url = BASE_URL + booking_url

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

            # Extract Category Name
            category_name_locator = category.locator("h3")
            if category_name_locator.count() == 0:
                self.logger.warning(f"Category {i} missing name. Skipping.")
                continue
            category_name = category_name_locator.text_content().strip()

            # Use text matching instead of class names
            see_available_button = category.locator("button").filter(has_text="See available cabins")
            join_waitlist_button = category.locator("button").filter(has_text="Join Waitlist")

            if see_available_button.count() > 0:
                category_status = "Available"
            elif join_waitlist_button.count() > 0:
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

