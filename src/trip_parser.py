import logging
from typing import Any
import time
from category_parser import CategoryParser
from departure_parser import fetch_departures
from config import BASE_URL, DEPARTURES_URL, START_DATE, END_DATE
from playwright.sync_api import sync_playwright
from secret_event import handle_secret_trip

class TripParser:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        
    def fetch_trips(self, limit: int = 50) -> list[dict[str, Any]]: # Limit set to 50
        trips = []

        with sync_playwright() as p:
            logging.info("========== PHASE 1: Gathering Departures ==========")

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(DEPARTURES_URL, timeout=60000)
            
            logging.info(f"Loaded Departures page for {START_DATE} to {END_DATE}")

            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            
            # Forcefully dismiss the GDPR overlay if it exists
            try:
                page.evaluate("""
                    const wrapper = document.querySelector('div[type="GDPR"]#wrapper');
                    if (wrapper) {
                        wrapper.style.display = 'none';
                        wrapper.remove();
                        const removed = !document.contains(wrapper);
                        if (removed) {
                            console.log("GDPR blocker removed from DOM.");
                        }
                    }
                """)
                self.logger.info("Forced removal of GDPR blocker if present.")
                time.sleep(2)  # Give time for DOM update
            except Exception as e:
                self.logger.info(f"Could not remove GDPR blocker: {e}")

            trip_elements = page.locator("[class^='hit_container__']")
            total_loaded = trip_elements.count()
            logging.info(f"Initial load found {total_loaded} trips.")

            # Keep clicking "Show more" until we reach the limit or no more trips
            while total_loaded < limit:
                show_more_button = page.locator("div.infinitehits_showMore__IYt_q button")
                if show_more_button.count() > 0:
                    logging.info("Clicking 'Show More' to load more trips...")
                    show_more_button.click()
                    page.wait_for_timeout(3000)  # Wait for more trips to load
                    total_loaded = page.locator("[class^='hit_container__']").count()
                    logging.info(f"New total trips loaded: {total_loaded}")
                else:
                    logging.info("No more 'Show More' button found. Ending trip fetch.")
                    break  # Exit loop when no more "Show more" button is available

            # Adjust the trip count based on the new total_loaded
            trip_count = min(total_loaded, limit)
            logging.info(f"Processing {trip_count} trips.")

            for i in range(trip_count):
                trip_element = trip_elements.nth(i)
                trip_name_locator = trip_element.locator("[class^='card_name__']")
                if trip_name_locator.count() == 0:
                    continue

                trip_name_raw = trip_name_locator.text_content()
                trip_name = trip_name_raw.strip() if trip_name_raw else "Unnamed Trip"

                trip_url = trip_name_locator.get_attribute("href") or ""
                full_trip_url = f"{BASE_URL}{trip_url}" if trip_url else "No URL Available"


                logging.info(f"[Trip {i+1}/{trip_count}] - Processing \"{trip_name}\" (URL: {full_trip_url})")

                # Extract image URL
                image_locator = trip_element.locator("img[class^='card_image__']")
                image_url = image_locator.get_attribute("src") if image_locator.count() > 0 else ""

                # Extract destination tags
                dest_spans = trip_element.locator("div[class^='card_list__'] span[class^='card_destination__']")
                destinations = []
                for j in range(dest_spans.count()):
                    text = dest_spans.nth(j).text_content()
                    if text:
                        destinations.append(text.strip())
                destination_str = "|".join(destinations)

                # Detect hidden trips
                hidden_trip_locator = trip_element.locator("[class^='card_displayNone']")
                is_hidden_trip = hidden_trip_locator.count() > 0

                if is_hidden_trip:
                    logging.info(f"🚨 Detected hidden trip: {trip_name}, triggering secret event handler.")
                    departures = handle_secret_trip(page, full_trip_url)
                else:
                    departures = fetch_departures(page, trip_element)

                trips.append({
                    "trip_name": trip_name,
                    "url": full_trip_url,
                    "image_url": image_url,
                    "destinations": destination_str,
                    "departures": departures
                })

            logging.info("========== PHASE 2: Checking Cabin Availability ==========")

            for trip_index, trip in enumerate(trips, start=1):  # Track trip number
                trip_name = trip["trip_name"]
                valid_departures = []

                for dep_index, departure in enumerate(trip["departures"], start=1):  # Track departure number
                    booking_url = departure.get("booking_url", "No URL Available")
                    start_date = departure.get("start_date", "Unknown Start Date")
                    end_date = departure.get("end_date", "Unknown End Date")

                    logging.info(f"[Trip {trip_index}/{len(trips)} - Departure {dep_index}/{len(trip['departures'])}] "
                                f"Fetching cabin categories for \"{trip_name}\" ({start_date} to {end_date})")

                    # Fetch categories and remove departures with no available cabins
                    category_parser = CategoryParser(booking_url, page)
                    categories = category_parser.fetch_categories()
                    departure["categories"] = categories

                    # ✅ Remove the departure if ALL cabins are waitlisted or unavailable
                    if all(cat["status"] == "Waitlist" for cat in categories):
                        logging.info(f"🚫 Removing departure: {departure['start_date']} - No available cabins")
                        continue  # Skip adding this departure to the list

                    # ✅ Only add departures that have at least ONE available cabin
                    valid_departures.append(departure)

                trip["departures"] = valid_departures

            browser.close()

        return trips

