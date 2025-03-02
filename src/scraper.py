from datetime import datetime, timedelta, UTC
import json
import logging
import requests
from playwright.sync_api import sync_playwright

class TripParser:
    ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
    ALGOLIA_APP_ID = "PRRU6FNC68"
    BASE_URL = "https://www.expeditions.com"

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_trips(self, limit=2):
        trips = []

        start_date = datetime(2025, 5, 13, tzinfo=UTC)
        end_date = datetime(2025, 5, 29, tzinfo=UTC)
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        payload = {
            "requests": [
                {
                    "indexName": "prod_seaware_EXPEDITIONS",
                    "params": f"analytics=true&clickAnalytics=true&enablePersonalization=true"
                              f"&facets=%5B%22departureDates.dateFromTimestamp%22%2C%22destinations.name%22%2C%22productType%22%2C%22ships.name%22%5D"
                              f"&filters=(departureDates.dateFromTimestamp >= {start_timestamp}) AND (departureDates.dateFromTimestamp <= {end_timestamp})"
                              f"&page=0&query=&tagFilters=&hitsPerPage={limit}"
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
            "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
            "X-Algolia-Agent": "Algolia for JavaScript (4.23.3); Browser (lite);"
        }

        try:
            response = requests.post(self.ALGOLIA_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            for result in data.get("results", []):
                for hit in result.get("hits", []):
                    try:
                        trip_name = hit.get("name", "Unknown Trip")
                        duration = hit.get("duration", 0)
                        destinations = hit.get("destinations", [])
                        page_slug = hit.get("pageSlug", "")

                        departures = self.fetch_departures(page_slug)

                        if departures:
                            trips.append({
                                "trip_name": trip_name,
                                "destination": {
                                    "top_level": destinations[0].get("name") if len(destinations) > 0 else None,
                                    "sub_region": destinations[1].get("name") if len(destinations) > 1 else None,
                                    "category": destinations[2].get("name") if len(destinations) > 2 else None
                                },
                                "duration": duration,
                                "departures": departures
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to parse trip '{hit.get('name', 'Unknown')}': {e}")
        except Exception as e:
            self.logger.error(f"Failed to fetch trips from Algolia API: {e}")
            return []

        return trips

    def fetch_departures(self, page_slug):
        departures = []
        trip_url = f"{self.BASE_URL}/{page_slug}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            self.logger.debug(f"Navigating to trip page: {trip_url}")
            page.goto(trip_url, timeout=60000)

            try:
                show_departures_button = page.locator("text=Show Departures")
                if show_departures_button.count() > 0:
                    show_departures_button.click()
                    self.logger.debug("Clicked 'Show Departures' button.")

                page.wait_for_selector(".hits_departureHitsContainer__5zVjx", timeout=10000)
                departure_elements = page.locator(".hits_departureHitsContainer__5zVjx li")

                for i in range(departure_elements.count()):
                    departure = departure_elements.nth(i)
                    start_date = departure.locator("[data-testid='departure-hit-year']").text_content().strip()
                    date_range = departure.locator(".sc-88e156bd-9").all_text_contents()
                    ship_name = departure.locator(".sc-88e156bd-8 i").text_content().strip()
                    booking_url = departure.locator("a").get_attribute("href")
                    
                    if len(date_range) >= 2:
                        departures.append({
                            "start_date": f"{start_date} {date_range[0]}",
                            "end_date": f"{start_date} {date_range[1]}",
                            "ship": ship_name,
                            "booking_url": f"{self.BASE_URL}{booking_url}"
                        })
            except Exception as e:
                self.logger.error(f"Failed to fetch departures for {page_slug}: {e}")
            finally:
                browser.close()

        return departures

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    for trip in trips:
        print(json.dumps(trip, indent=2))
