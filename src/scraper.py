from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
import re
import json

class TripParser:
    BASE_URL = "https://www.expeditions.com/book/_next/data/whsFWKFfoVddyXnk_vWAM/index.json"
    
    def fetch_trips(self, limit=10):
        trips = []

        # Calculate date range for filtering
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=(120 + 7))  # 4 months + 1 week
        start_timestamp = int(time.mktime(start_date.timetuple()))
        end_timestamp = int(time.mktime(end_date.timetuple()))
        date_range = f"{start_timestamp}%3A{end_timestamp}"
        
        url = f"{self.BASE_URL}?dateRange={date_range}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            
            # Extract JSON response
            response = page.evaluate("() => document.body.innerText")
            browser.close()
            
            try:
                print("\nRaw JSON Response:\n", response)  # Debugging: Print raw response
                data = json.loads(response)  # Convert string to dictionary safely
                
                # Check if 'serverState' exists
                server_state = data.get("pageProps", {}).get("serverState")
                if not server_state:
                    print("ERROR: 'serverState' is missing from response.")
                    return []
                
                print("\nExtracted serverState:\n", json.dumps(server_state, indent=2))  # Debug
                
                trip_cards = server_state.get("trips", [])
                print(f"\nFound {len(trip_cards)} trips in response.")  # Debug

                if not trip_cards:
                    print("ERROR: No trips found in 'serverState'.")
                    return []

            except Exception as e:
                print(f"ERROR: Failed to parse JSON response: {e}")
                return []
            
            for trip in trip_cards[:limit]:
                try:
                    trip_name = trip.get("name", "Unknown Trip")
                    duration = trip.get("duration", "Unknown Duration")
                    
                    destinations = trip.get("destinations", [])
                    top_level = destinations[0] if len(destinations) > 0 else None
                    sub_region = destinations[1] if len(destinations) > 1 else None
                    category = destinations[2] if len(destinations) > 2 else None
                    
                    departures = []
                    for dep in trip.get("departures", []):
                        try:
                            start_date = dep.get("startDate")
                            end_date = dep.get("endDate")
                            ship = dep.get("ship")
                            price = dep.get("price")
                            booking_url = dep.get("bookingUrl")
                            
                            # Extract year from booking URL
                            year = None
                            if booking_url:
                                match = re.search(r'-(\d{2})(\d{2})(\d{2})', booking_url)
                                if match:
                                    year = f"20{match.group(2)}"  # Extract correct 4-digit year
                            
                            departures.append({
                                "year": year,
                                "start_date": start_date,
                                "end_date": end_date,
                                "ship": ship,
                                "price": price,
                                "booking_url": booking_url
                            })
                        except Exception as e:
                            print(f"ERROR: Failed to parse departure for trip '{trip_name}': {e}")
                    
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
                    print(f"ERROR: Failed to parse trip '{trip.get('name', 'Unknown')}': {e}")
        
        return trips

# Manual test
if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=10)
    for trip in trips:
        print(json.dumps(trip, indent=2))
