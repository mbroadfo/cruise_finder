from datetime import datetime, timedelta, UTC
import json
import logging
import requests

class TripParser:
    ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
    ALGOLIA_APP_ID = "PRRU6FNC68"
    DATASTEAM_URL = "https://api.datasteam.io/v1/C/RawData/CA27E6C1BB02"

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
        url = f"{self.DATASTEAM_URL}?v=da03a7a4-448a-490a-a7df-1c7b530d6912&se=9269cc8e-9766-4e31-9a05-246568cb06ca&d={page_slug}"
        headers = {
            "Accept": "*/*",
            "Referer": "https://www.expeditions.com/",
            "Sec-Fetch-Mode": "no-cors"
        }

        self.logger.debug(f"Fetching departures from URL: {url}")

        try:
            response = requests.get(url, headers=headers)
            self.logger.debug(f"Response Status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            self.logger.debug(f"Departure Response Data: {data}")

            if data.get("Status") == "true":
                for dep in data.get("departures", []):
                    departures.append({
                        "start_date": dep.get("start_date", "Unknown"),
                        "end_date": dep.get("end_date", "Unknown"),
                        "ship": dep.get("ship", "Unknown"),
                        "booking_url": dep.get("booking_url", "Unknown")
                    })
            else:
                self.logger.warning(f"No departures found for {page_slug}")
        except Exception as e:
            self.logger.error(f"Failed to fetch departures for {page_slug}: {e}")

        return departures

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    for trip in trips:
        print(json.dumps(trip, indent=2))
