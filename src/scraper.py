from datetime import datetime, timedelta
import json
import requests

class TripParser:
    ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
    ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
    ALGOLIA_APP_ID = "PRRU6FNC68"

    def fetch_trips(self, limit=10):
        trips = []

        # Calculate date range for filtering
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=(4 * 30) + 7)  # 4 months + 1 week
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Algolia query payload
        payload = {
            "requests": [
                {
                    "indexName": "prod_seaware_EXPEDITIONS",
                    "params": f"analytics=true&clickAnalytics=true&enablePersonalization=true&facets=%5B%22departureDates.dateFromTimestamp%22%2C%22destinations.name%22%2C%22productType%22%2C%22ships.name%22%5D&filters=%28nrDepartures%20%3E%200%29%20AND%20%28departureDates.dateFromTimestamp%20%3E%20{start_timestamp}%29&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&maxValuesPerFacet=40&numericFilters=%5B%22departureDates.dateFromTimestamp%3E%3D{start_timestamp}%22%2C%22departureDates.dateFromTimestamp%3C%3D{end_timestamp}%22%5D&page=0&query=&tagFilters=&userToken=24d3ed59-a6b2-478f-b789-549b7598c7b1&hitsPerPage={limit}"
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
            "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
            "X-Algolia-Agent": "Algolia for JavaScript (4.23.3); Browser (lite); instantsearch.js (4.68.1); react (18.3.1); react-instantsearch (7.8.1); react-instantsearch-core (7.8.1); next.js (14.2.3); JS Helper (3.19.0)"
        }

        try:
            # Send POST request to Algolia API
            response = requests.post(self.ALGOLIA_URL, headers=headers, json=payload)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()

            print("\nRaw Algolia Response:\n", json.dumps(data, indent=2))  # Debugging

            # Extract trips from the response
            for result in data.get("results", []):
                hits = result.get("hits", [])
                for hit in hits:
                    try:
                        trip_name = hit.get("name", "Unknown Trip")
                        duration = hit.get("duration", "Unknown Duration")
                        destinations = hit.get("destinations", [])
                        top_level = destinations[0] if len(destinations) > 0 else None
                        sub_region = destinations[1] if len(destinations) > 1 else None
                        category = destinations[2] if len(destinations) > 2 else None

                        departures = []
                        for dep in hit.get("departureDates", []):
                            try:
                                departure_timestamp = dep.get("dateFromTimestamp")
                                if start_timestamp <= departure_timestamp <= end_timestamp:
                                    start_date = dep.get("dateFrom")
                                    end_date = dep.get("dateTo")
                                    ship = hit.get("ships", [{}])[0].get("name", "Unknown Ship")
                                    price = hit.get("lowestDiscountedPrice", "Unknown Price")
                                    booking_url = hit.get("pageSlug", "Unknown URL")

                                    departures.append({
                                        "start_date": start_date,
                                        "end_date": end_date,
                                        "ship": ship,
                                        "price": price,
                                        "booking_url": booking_url
                                    })
                            except Exception as e:
                                print(f"ERROR: Failed to parse departure for trip '{trip_name}': {e}")

                        # Only include trips with valid departures
                        if departures:
                            trips.append({
                                "trip_name": trip_name,
                                "destination": {
                                    "top_level": top_level,
                                    "sub_region": sub_region,
                                    "category": category
                                },
                                "duration": duration,
                                "departures": departures
                            })
                    except Exception as e:
                        print(f"ERROR: Failed to parse trip '{hit.get('name', 'Unknown')}': {e}")

        except Exception as e:
            print(f"ERROR: Failed to fetch trips from Algolia API: {e}")
            return []

        return trips

# Manual test
if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=10)
    for trip in trips:
        print(json.dumps(trip, indent=2))