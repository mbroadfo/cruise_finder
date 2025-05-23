import logging
import time
from config import BASE_URL
from typing import Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

class CategoryParser:
    def __init__(self, booking_url: str, page: Any) -> None:
        if not booking_url.startswith("http"):
            booking_url = BASE_URL + booking_url

        self.booking_url = booking_url
        self.page = page
        self.categories: list[dict[str, Any]] = []

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def _dismiss_cookie_banner(self) -> None:
        try:
            ok_button = self.page.locator("button[data-style='button']").filter(has_text="OK")
            if ok_button.count() > 0:
                ok_button.first.click(timeout=5000)
                self.logger.info("Dismissed cookie consent banner.")
                time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Cookie banner dismissal failed: {e}")

    def extract_available_cabins_from_drawer(self, page: Page) -> list[str]:
        seen = set()
        cabin_cards = page.locator("[data-testid='cabin-card']")
        cabin_numbers = []

        for i in range(cabin_cards.count()):
            card = cabin_cards.nth(i)
            candidate = card.locator("p")
            for j in range(candidate.count()):
                text_raw = candidate.nth(j).text_content()
                text = text_raw.strip() if text_raw else ""
                if text.isdigit() and text not in seen:
                    seen.add(text)
                    cabin_numbers.append(text)
                    # break removed to allow collection of multiple cabin numbers per card

        return cabin_numbers

    def fetch_categories(self) -> list[dict[str, Any]]:
        self.logger.info(f"  Navigating to booking page: {self.booking_url}")
        MAX_RETRIES = 3
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.page.goto(self.booking_url, timeout=60000)
                break  # success
            except PlaywrightTimeoutError as e:
                self.logger.warning(f"⏳ Timeout loading {self.booking_url} (attempt {attempt}/{MAX_RETRIES})")
                if attempt == MAX_RETRIES:
                    self.logger.error(f"❌ Failed after {MAX_RETRIES} attempts: {self.booking_url}")
                    raise e
                backoff = 2 ** attempt
                self.logger.info(f"🔁 Retrying in {backoff}s...")
                time.sleep(backoff)

        try:
            self.page.wait_for_selector("[data-testid='category-card']", timeout=10000)
        except Exception as e:
            self.logger.warning(f"No category cards found: {e}")
            return []

        try:
            self.page.evaluate("""
                const gdpr = document.querySelector('div[type="GDPR"]#wrapper');
                if (gdpr) gdpr.remove();

                const ccpa = document.querySelector('div[type="CCPA"]#wrapper');
                if (ccpa) ccpa.remove();

                console.log("Removed known blocker elements.");
            """)
            self.logger.info("Forced removal of blockers if present.")
            time.sleep(2)
        except Exception as e:
            self.logger.info(f"Could not remove blockers: {e}")

        self._dismiss_cookie_banner()

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

            deck_raw = deck_locator.text_content() if deck_locator.count() > 0 else None
            deck = deck_raw.strip() if deck_raw else "Unknown"
            category_name_raw = category_name_locator.text_content() if category_name_locator.count() > 0 else None
            category_name = category_name_raw.strip() if category_name_raw else "Unknown"
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
            cabin_numbers: list[str] = []

            if category_status == "Available":
                see_available_button.first.scroll_into_view_if_needed()
                see_available_button.first.click()
                self.page.wait_for_timeout(6000)
                self.logger.info(f"Clicked to open drawer for {category_name}.")

                try:
                    self.page.wait_for_selector("[data-testid='cabin-card']", timeout=20000)
                    cabin_numbers = self.extract_available_cabins_from_drawer(self.page)
                    num_cabins = len(cabin_numbers)
                    self.logger.info(f"    {category_name}: {num_cabins} available cabins ({', '.join(cabin_numbers)})")
                except Exception as e:
                    self.logger.warning(f"Error fetching available cabins for {category_name}: {e}")

                try:
                    close_button = self.page.locator("button[data-variant='text'][data-style='link']")
                    if close_button.count() > 0:
                        close_button.first.click()
                        self.page.wait_for_timeout(6000)
                except Exception as click_error:
                    self.logger.warning(f"Fallback close button failed: {click_error}")

            if category_status != "Waitlist":
                self.categories.append({
                    "category_name": category_name,
                    "deck": deck,
                    "occupancy": occupancy,
                    "cabin_type": cabin_type,
                    "price": price,
                    "status": category_status,
                    "cabinNumbers": "|".join(cabin_numbers),
                    "num_cabins": num_cabins
                })
            else:
                self.logger.info(f"    🚫 Excluding waitlisted category: {category_name} on {deck}")

        return self.categories
