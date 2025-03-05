import logging
from category_parser import CategoryParser
from departure_parser import fetch_departures
from config import BASE_URL, DEPARTURES_URL, START_DATE, END_DATE
from playwright.sync_api import sync_playwright

class TripParser:
    def fetch_trips(self, limit=50):  # Increased limit to 50
        trips = []

        with sync_playwright() as p:
            logging.info("========== PHASE 1: Gathering Departures ==========")

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(DEPARTURES_URL, timeout=60000)
            logging.info(f"Loaded Departures page for {START_DATE} to {END_DATE}")
            
            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            trip_elements = page.locator("[class^='hit_container__']")
            trip_count = min(trip_elements.count(), limit)
            logging.info(f"Found {trip_count} trips.")

            for i in range(trip_count):
                trip = trip_elements.nth(i)
                trip_name_locator = trip.locator("[class^='card_name__']")
                if trip_name_locator.count() == 0:
                    continue
                
                trip_name = trip_name_locator.text_content().strip()
                trip_url = trip_name_locator.get_attribute("href")
                full_trip_url = f"{BASE_URL}{trip_url}" if trip_url else "No URL Available"

                logging.info(f"[Trip {i+1}/{trip_count}] - Processing \"{trip_name}\" (URL: {full_trip_url})")
                
                departures = fetch_departures(page, trip)
                
                trips.append({
                    "trip_name": trip_name,
                    "url": full_trip_url,
                    "departures": departures
                })

            logging.info("========== PHASE 2: Checking Cabin Availability ==========")

            for trip in trips:
                trip_name = trip["trip_name"]
                for departure in trip["departures"]:
                    booking_url = departure.get("booking_url", "No URL Available")
                    start_date = departure.get("start_date", "Unknown Start Date")
                    end_date = departure.get("end_date", "Unknown End Date")

                    logging.info(f"Fetching cabin categories for \"{trip_name}\" ({start_date} to {end_date}) - {booking_url}")
                    category_parser = CategoryParser(booking_url, page)
                    departure["categories"] = category_parser.fetch_categories()
            
            browser.close()
        
        return trips
