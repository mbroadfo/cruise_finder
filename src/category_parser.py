import logging
import time
import traceback
from playwright.sync_api import sync_playwright

def fetch_categories():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        logger = logging.getLogger(__name__)

        try:
            page.goto("https://www.expeditions.com/book")

            # Remove GDPR and CCPA blockers if present
            try:
                page.evaluate("""
                    // GDPR blocker
                    const gdpr = document.querySelector('div[type="GDPR"]#wrapper');
                    gdpr?.remove();

                    // CCPA cookie blocker
                    const ccpa = document.querySelector('div[type="CCPA"]#wrapper');
                    ccpa?.remove();

                    console.log("Removed known blocker elements.");
                """)
                print("Forced removal of blockers if present.")
                time.sleep(2)  # Let DOM settle
            except Exception as e:
                print(f"Could not remove blockers: {e}")

            # Locate the 'See available cabins' button
            see_available_button = page.locator("[data-testid='category-card']").nth(4).locator("button").filter(has_text="See available cabins")

            try:
                see_available_button.first.click(timeout=30000)
            except Exception as click_error:
                page.screenshot(path="click_failure_debug.png", full_page=True)
                print("Click failed, screenshot saved as click_failure_debug.png")
                raise click_error

        except Exception:
            logger.exception("Exception in fetch_categories:")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    fetch_categories()
