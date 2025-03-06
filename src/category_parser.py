import logging
from config import BASE_URL

class CategoryParser:
    def __init__(self, booking_url, page):
        if not booking_url.startswith("http"):
            booking_url = BASE_URL + booking_url

        self.booking_url = booking_url
        self.page = page
        self.categories = []

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def fetch_categories(self):
        self.logger.info(f"  Navigating to booking page: {self.booking_url}")
        self.page.goto(self.booking_url, timeout=60000)

        try:
            self.page.wait_for_selector("[data-testid='category-card']", timeout=10000)
        except Exception as e:
            self.logger.warning(f"No category cards found: {e}")
            return []

        category_elements = self.page.locator("[data-testid='category-card']")
        category_count = category_elements.count()
        self.logger.info(f"  Found {category_count} cabin categories.")

        for i in range(category_count):
            category = category_elements.nth(i)

            deck_locator = category.locator("span").filter(has_text="Deck")
            category_name_locator = category.locator("h3")
            pax_icons = category.locator("[class*='pax-icons_'] svg")
            cabin_type_locator = pax_icons.nth(pax_icons.count() - 1).locator("+ span")
            price_locator = category.locator("h2")

            deck = deck_locator.text_content().strip() if deck_locator.count() > 0 else "Unknown"
            category_name = category_name_locator.text_content().strip() if category_name_locator.count() > 0 else "Unknown"
            occupancy = f"{pax_icons.count()} Person(s)" if pax_icons.count() > 0 else "Unknown"
            cabin_type = cabin_type_locator.text_content().strip() if cabin_type_locator.count() > 0 else "Unknown"
            price = price_locator.text_content().strip() if price_locator.count() > 0 else "Unknown"

            see_available_button = category.locator("button").filter(has_text="See available cabins")
            join_waitlist_button = category.locator("button").filter(has_text="Join Waitlist")

            if see_available_button.count() > 0:
                category_status = "Available"
            elif join_waitlist_button.count() > 0:
                category_status = "Waitlist"
            else:
                category_status = "Unknown"

            num_cabins = 0

            if category_status == "Available":
                see_available_button.first.click()
                self.page.wait_for_timeout(2000)  # Ensure modal loads

                try:
                    self.page.wait_for_selector("[data-testid='cabin-card']", timeout=5000)

                    # Count direct children (cabins), ignoring the first div (header)
                    cabin_card = self.page.locator("[data-testid='cabin-card']").first
                    direct_children = cabin_card.locator("> div")
                    num_cabins = max(0, direct_children.count() - 1)

                    self.logger.info(f"    {category_name}: {num_cabins} available cabins")

                except Exception as e:
                    self.logger.warning(f"Error fetching available cabins for {category_name}: {e}")

                # Close Modal Before Moving to Next Category
                try:
                    close_button = self.page.locator("button[data-variant='text'][data-style='link']")
                    if close_button.count() > 0:
                        close_button.first.click()
                        self.page.wait_for_timeout(1000)  # Allow time for modal to close
                except Exception as e:
                    self.logger.warning(f"Failed to close sidebar: {e}")

            # Store the category availability data
            self.categories.append({
                "category_name": category_name,
                "deck": deck,
                "occupancy": occupancy,
                "cabin_type": cabin_type,
                "price": price,
                "status": category_status,
                "num_cabins": num_cabins
            })

        return self.categories
