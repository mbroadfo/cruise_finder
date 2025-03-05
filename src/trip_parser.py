import logging
from category_parser import CategoryParser
from departure_parser import fetch_departures
from config import BASE_URL, DEPARTURES_URL
from playwright.sync_api import sync_playwright

class TripParser:
    def fetch_trips(self, limit=50):  # Increased limit to 50
        trips = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(DEPARTURES_URL, timeout=60000)
            logging.info("Loaded departures page.")
            
            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            trip_elements = page.locator("[class^='hit_container__']")
            trip_count = min(trip_elements.count(), limit)
            logging.info(f"Found {trip_count} trips.")

            logging.info("========== PHASE 1: Gathering Departures ==========")

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
                for departure in trip["departures"]:
                    booking_url = departure["booking_url"]
                    if booking_url:
                        logging.info(f"Fetching categories for booking: {booking_url}")
                        category_parser = CategoryParser(booking_url, page)
                        departure["categories"] = category_parser.fetch_categories()
            
            browser.close()
        
        return trips
