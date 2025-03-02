from datetime import datetime, timedelta, UTC
import json
import logging
import requests

class TripParser:
    ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
    ALGOLIA_APP_ID = "PRRU6FNC68"

    def __init__(self):
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fetch_trips(self, limit=1):
        trips = []

        # Set a tighter date range for testing
        start_date = datetime(2025, 3, 2, tzinfo=UTC)
        end_date = datetime(2025, 3, 5, tzinfo=UTC)
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Algolia query payload using "filters" instead of "numericFilters"
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

                        departures = []
                        for dep in hit.get("departureDates", []):
                            try:
                                departure_timestamp = dep.get("dateFromTimestamp")
                                return_timestamp = dep.get("dateToTimestamp")

                                if departure_timestamp:
                                    start_date = datetime.fromtimestamp(departure_timestamp, UTC).strftime('%Y-%m-%d')
                                else:
                                    start_date = "Unknown Start Date"

                                if return_timestamp:
                                    end_date = datetime.fromtimestamp(return_timestamp, UTC).strftime('%Y-%m-%d')
                                elif duration > 0 and departure_timestamp:
                                    calculated_end = departure_timestamp + (duration * 86400)
                                    end_date = datetime.fromtimestamp(calculated_end, UTC).strftime('%Y-%m-%d')
                                else:
                                    end_date = "Unknown End Date"

                                ship = hit.get("ships", [{}])[0].get("name", "Unknown Ship")
                                booking_url = f"https://www.expeditions.com/trips/{hit.get('pageSlug', '')}"

                                departures.append({
                                    "start_date": start_date,
                                    "end_date": end_date,
                                    "ship": ship,
                                    "booking_url": booking_url
                                })
                            except Exception as e:
                                self.logger.warning(f"Failed to parse departure for trip '{trip_name}': {e}")

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

if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=1)
    for trip in trips:
        print(json.dumps(trip, indent=2))
