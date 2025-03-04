import logging
from config import BASE_URL

class CategoryParser:
    def __init__(self, booking_url, page):
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

            # Extract attributes using refined selectors
            deck_locator = category.locator("span").filter(has_text="Deck")
            category_name_locator = category.locator("h3")

            # Find the container holding the pax icons and count the number of <svg> icons inside
            pax_icons = category.locator("[class*='pax-icons_'] svg")

            # Find the span containing the cabin type, avoiding buttons
            cabin_type_locator = pax_icons.nth(pax_icons.count() - 1).locator("+ span")

            price_locator = category.locator("h2")

            deck = deck_locator.text_content().strip() if deck_locator.count() > 0 else "Unknown"
            category_name = category_name_locator.text_content().strip() if category_name_locator.count() > 0 else "Unknown"
            occupancy = f"{pax_icons.count()} Person(s)" if pax_icons.count() > 0 else "Unknown"
            cabin_type = cabin_type_locator.text_content().strip() if cabin_type_locator.count() > 0 else "Unknown"
            price = price_locator.text_content().strip() if price_locator.count() > 0 else "Unknown"

            # Detect availability
            see_available_button = category.locator("button").filter(has_text="See available cabins")
            join_waitlist_button = category.locator("button").filter(has_text="Join Waitlist")

            if see_available_button.count() > 0:
                category_status = "Available"
            elif join_waitlist_button.count() > 0:
                category_status = "Waitlist"
            else:
                category_status = "Unknown"

            is_available = category_status == "Available"
            
            # Count the number of cabins if available
            num_cabins = 0
            if is_available:
                see_available_button.first.click()
                self.page.wait_for_selector("[data-testid='cabin-card']", timeout=5000)
                num_cabins = self.page.locator("[data-testid='cabin-card']").count()
                self.logger.info(f"{category_name} - {deck}, {occupancy}, {cabin_type}, {price}, Status: {category_status}, Cabins: {num_cabins}")
                
                try:
                    close_button = self.page.locator("button[data-variant='text'][data-style='link']")
                    if close_button.count() > 0:
                        close_button.first.click()
                        self.page.wait_for_timeout(1000)  # Small delay to ensure the sidebar is closed
                except Exception as e:
                    self.logger.warning(f"Failed to close sidebar: {e}")
            
            self.categories.append({
                "category_name": category_name,
                "deck": deck,
                "occupancy": occupancy,
                "cabin_type": cabin_type,
                "price": price,
                "status": category_status,
                "available": is_available,
                "num_cabins": num_cabins
            })

        return self.categories
