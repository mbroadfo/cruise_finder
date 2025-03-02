from datetime import datetime, timedelta, UTC
import json
import logging
import requests
import re
from playwright.sync_api import sync_playwright

class TripParser:
    ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
    ALGOLIA_APP_ID = "PRRU6FNC68"
    BASE_URL = "https://www.expeditions.com"
    DEPARTURES_URL = "https://www.expeditions.com/book?dateRange=1747116000%253A1748498400"

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_trips(self, limit=2):
        trips = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.DEPARTURES_URL, timeout=60000)
            self.logger.debug("Navigated to departures page.")
            
            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            trip_elements = page.locator("[class^='hit_container__']")
            trip_count = trip_elements.count()
            self.logger.debug(f"Found {trip_count} trips on the page.")
            
            for i in range(trip_count):
                trip = trip_elements.nth(i)
                hit_container_id = trip.get_attribute("class")
                self.logger.debug(f"Processing trip container {i} with hit container ID: {hit_container_id}")
                
                trip_name_locator = trip.locator("[class^='card_name__']")
                if trip_name_locator.count() == 0:
                    self.logger.warning(f"No trip name found for trip index {i}")
                    continue
                
                trip_name = trip_name_locator.text_content().strip()
                trip_url = trip_name_locator.get_attribute("href")
                
                if trip_url:
                    full_trip_url = f"{self.BASE_URL}{trip_url}"
                    self.logger.debug(f"Extracted trip: {trip_name} - {full_trip_url}")
                    departures = self.fetch_departures(page, trip)
                    if departures:
                        trips.append({
                            "trip_name": trip_name,
                            "url": full_trip_url,
                            "departures": departures
                        })
                else:
                    self.logger.warning(f"No valid link found for trip: {trip_name}")
            browser.close()

        return trips

    def fetch_departures(self, page, trip):
        departures = []

        try:
            show_departures_button = trip.locator("button", has_text="See departure dates")
            button_count = show_departures_button.count()
            self.logger.debug(f"Found {button_count} 'See departure dates' buttons in trip container.")

            if button_count > 0:
                self.logger.debug("Clicking 'See departure dates' button for trip.")
                show_departures_button.first.click()
                page.wait_for_timeout(2000)  # Allow time for departures to load

                departure_container_locator = trip.locator("[class^='hits_departureHitsContainer__']")
                page.wait_for_selector("[class^='hits_departureHitsContainer__']", timeout=7000)
                
                container_count = departure_container_locator.count()
                self.logger.debug(f"Found {container_count} departure containers inside trip container after clicking button.")
                
                if container_count == 0:
                    self.logger.debug("No departures found for this trip.")
                    return departures
                
                elements = departure_container_locator.locator("li")
                element_count = elements.count()
                self.logger.debug(f"Found {element_count} departures.")

                for i in range(element_count):
                    departure = elements.nth(i)
                    start_date_locator = departure.locator("[data-testid='departure-hit-year']")
                    date_range_locator = departure.locator("p[class*='drDbhx']")
                    ship_name_locator = departure.locator("i")
                    booking_url_locator = departure.locator("a")
                    
                    if start_date_locator.count() == 0 or date_range_locator.count() < 2 or ship_name_locator.count() == 0 or booking_url_locator.count() == 0:
                        self.logger.warning(f"Skipping departure {i} due to missing data.")
                        continue
                    
                    start_date = start_date_locator.text_content().strip()
                    date_range = date_range_locator.all_text_contents()
                    ship_name = ship_name_locator.text_content().strip()
                    booking_url = booking_url_locator.get_attribute("href")
                    
                    self.logger.debug(f"Extracted departure {i}: {start_date} {date_range[0]} - {start_date} {date_range[1]}, Ship: {ship_name}, Booking URL: {booking_url}")
                    
                    departures.append({
                        "start_date": f"{start_date} {date_range[0]}",
                        "end_date": f"{start_date} {date_range[1]}",
                        "ship": ship_name,
                        "booking_url": f"{self.BASE_URL}{booking_url}"
                    })
        except Exception as e:
            self.logger.error(f"Failed to fetch departures: {e}")

        return departures

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    for trip in trips:
        print(json.dumps(trip, indent=2))
