from playwright.sync_api import sync_playwright

class TripParser:
    BASE_URL = "https://www.expeditions.com/book"
    
    def fetch_trips(self, limit=10):
        trips = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.BASE_URL, timeout=60000)
            
            # Wait for trips to load
            page.wait_for_selector("div[class^='card_cardContent']", timeout=40000)

            trip_cards = page.locator("div[class^='card_cardContent']").all()[:limit]
            for card in trip_cards:
                try:
                    trip_name = card.locator("a[class^='card_name']").inner_text().strip()
                    duration = card.locator("span[data-testid='expeditionCard-days']").inner_text().strip()
                    
                    # Extract destination details
                    destinations = card.locator("span[class^='card_destination']").all_inner_texts()
                    top_level = destinations[0].strip() if len(destinations) > 0 else None
                    sub_region = destinations[1].strip() if len(destinations) > 1 else None
                    category = destinations[2].strip() if len(destinations) > 2 else None
                    
                    # Click to reveal departures
                    departure_button = card.locator("button:has-text('See departure dates')")
                    departures = []
                    if departure_button.count() > 0:
                        departure_button.first.click(force=True)
                        page.wait_for_selector("div[class^='hits_departureHitsContainer']", timeout=5000)
                        
                        # Extract departures
                        departure_rows = page.locator("div[data-testid='departure-hit']").all()
                        year_elements = page.locator("span[data-testid='departure-hit-year']").all()
                        latest_year = None  # Track the most recent year
                        
                        year_index = 0
                        for row in departure_rows:
                            try:
                                # Check if a new year is found
                                year_element = row.locator("span[data-testid='departure-hit-year']")
                                if year_element.count() > 0:
                                    latest_year = year_element.inner_text().strip()
                                
                                dates = [d.strip() for d in row.locator("p.sc-88e156bd-9").all_inner_texts()]
                                ship_element = row.locator("div.sc-88e156bd-8 i")
                                ship = ship_element.inner_text().strip() if ship_element.count() > 0 else None
                                price_element = row.locator("span.sc-631fca56-2")
                                price = price_element.inner_text().strip() if price_element.count() > 0 else None
                                booking_url_element = row.locator("a.sc-88e156bd-3")
                                booking_url = booking_url_element.get_attribute("href") if booking_url_element.count() > 0 else None
                                
                                if len(dates) == 2:
                                    departures.append({
                                        "year": latest_year,
                                        "start_date": dates[0],
                                        "end_date": dates[1],
                                        "ship": ship,
                                        "price": price,
                                        "booking_url": booking_url
                                    })
                            except Exception as e:
                                print(f"Error extracting departure: {e}")
                    
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
                    print(f"Error extracting trip: {e}")
            
            browser.close()
        return trips

# Manual test
if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=10)
    for trip in trips:
        print(trip)
