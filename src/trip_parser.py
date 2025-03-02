from playwright.sync_api import sync_playwright
from config import BASE_URL, DEPARTURES_URL, logger
from departure_parser import fetch_departures

class TripParser:
    def fetch_trips(self, limit=2):
        trips = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(DEPARTURES_URL, timeout=60000)
            logger.info("Loaded departures page.")
            
            page.wait_for_selector("[class^='hit_container__']", timeout=10000)
            trip_elements = page.locator("[class^='hit_container__']")
            trip_count = trip_elements.count()
            logger.info(f"Found {trip_count} trips.")
            
            for i in range(trip_count):
                trip = trip_elements.nth(i)
                trip_name_locator = trip.locator("[class^='card_name__']")
                if trip_name_locator.count() == 0:
                    continue
                
                trip_name = trip_name_locator.text_content().strip()
                trip_url = trip_name_locator.get_attribute("href")
                full_trip_url = f"{BASE_URL}{trip_url}" if trip_url else None
                logger.info(f"{trip_name} - {full_trip_url}")
                
                departures = fetch_departures(page, trip)
                if departures:
                    trips.append({
                        "trip_name": trip_name,
                        "url": full_trip_url,
                        "departures": departures
                    })
            browser.close()

        return trips

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    for trip in trips:
        print(trip)
