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
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_trips(self, limit=2):
        trips = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.DEPARTURES_URL, timeout=60000)
            self.logger.info("Loaded departures page.")
            
            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            trip_elements = page.locator("[class^='hit_container__']")
            trip_count = trip_elements.count()
            self.logger.info(f"Found {trip_count} trips.")
            
            for i in range(trip_count):
                trip = trip_elements.nth(i)
                trip_name_locator = trip.locator("[class^='card_name__']")
                if trip_name_locator.count() == 0:
                    continue
                
                trip_name = trip_name_locator.text_content().strip()
                trip_url = trip_name_locator.get_attribute("href")
                full_trip_url = f"{self.BASE_URL}{trip_url}" if trip_url else None
                self.logger.info(f"{trip_name} - {full_trip_url}")
                
                departures = self.fetch_departures(page, trip)
                if departures:
                    trips.append({
                        "trip_name": trip_name,
                        "url": full_trip_url,
                        "departures": departures
                    })
            browser.close()

        return trips

    def fetch_departures(self, page, trip):
        departures = []
        latest_year = None  # Reset latest_year at the start of each trip's departures
        
        try:
            show_departures_button = trip.locator("button", has_text="See departure dates")
            if show_departures_button.count() > 0:
                show_departures_button.first.click()
                page.wait_for_timeout(200)
                
                departure_container_locator = trip.locator("[class^='hits_departureHitsContainer__']")
                if departure_container_locator.count() == 0:
                    return departures
                
                elements = departure_container_locator.locator("li")
                element_count = elements.count()
                
                if element_count == 0:
                    self.logger.info("No visible departures found for this trip. Skipping.")
                    return departures
                
                for i in range(element_count):
                    departure = elements.nth(i)
                    
                    year_locator = departure.locator("[data-testid='departure-hit-year']")
                    date_range_locator = departure.locator("p[class*='drDbhx']")
                    ship_name_locator = departure.locator("i")
                    booking_url_locator = departure.locator("a")
                    land_expedition_locator = departure.locator("div[data-land-expedition='true']")
                    
                    # If the year span is present, update latest_year
                    if year_locator.count() > 0:
                        latest_year = year_locator.text_content().strip()
                        self.logger.info(f"Found year line item: {latest_year}")
                    
                    missing_fields = []
                    if latest_year is None:
                        missing_fields.append("year")
                    if date_range_locator.count() < 2:
                        missing_fields.append("date range")
                    if booking_url_locator.count() == 0:
                        missing_fields.append("booking URL")
                    
                    if missing_fields:
                        self.logger.warning(f"Skipping departure {i} due to missing fields: {', '.join(missing_fields)}")
                        continue
                    
                    # Extract details
                    date_range = date_range_locator.all_text_contents()
                    ship_name = "Land Expedition" if land_expedition_locator.count() > 0 else ship_name_locator.text_content().strip()
                    booking_url = booking_url_locator.get_attribute("href")
                    
                    # Apply latest_year to start and end dates
                    start_date = f"{latest_year} {date_range[0].strip()}"
                    end_date = f"{latest_year} {date_range[1].strip()}"
                    
                    self.logger.info(f"Found departure: {start_date} to {end_date}, Ship: {ship_name}")
                    
                    departures.append({
                        "start_date": start_date,
                        "end_date": end_date,
                        "ship": ship_name,
                        "booking_url": f"{self.BASE_URL}{booking_url}"
                    })
        except Exception as e:
            self.logger.error(f"Error fetching departures: {e}")

        return departures

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    for trip in trips:
        print(json.dumps(trip, indent=2))
