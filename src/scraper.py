from playwright.sync_api import sync_playwright
import re

class TripParser:
    BASE_URL = "https://www.expeditions.com/book"

    def fetch_trips(self, limit=10):
        """Uses Playwright to load up to `limit` trips and extract departures."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.BASE_URL, timeout=60000)

            # Wait for trips to load
            page.wait_for_selector("div[class^='card_cardContent']", timeout=40000)

            trips = []
            trip_elements = page.locator("div[class^='card_cardContent']").all()[:limit]  # Limit trips

            for trip in trip_elements:
                try:
                    title = trip.locator("a[rel='noreferrer']").first.inner_text().strip()

                    # Normalize destinations: Remove newlines, extra spaces
                    destinations = " ".join(
                        [re.sub(r"\s+", " ", d.inner_text().strip()) for d in trip.locator("span[class^='card_destination']").all()]
                    )

                    # Normalize duration: Remove extra spaces and newlines
                    duration = re.sub(r"\s+", " ", trip.locator("span[data-testid='expeditionCard-days']").inner_text().strip())

                    trip_data = {
                        "trip_name": title,
                        "destination": destinations,
                        "duration": duration,
                        "departures": []
                    }

                    # Click "See Departure Dates" button if available
                    departure_button = trip.locator("button:text('See departure dates')")
                    if departure_button.is_visible():
                        departure_button.click()
                        page.wait_for_timeout(2000)  # Wait for departures to load

                        # Extract departure dates & ship names
                        departure_elements = page.locator("div.departure_dates_selector")  # Adjust selector
                        for departure in departure_elements.all():
                            try:
                                date = re.sub(r"\s+", " ", departure.locator(".date").inner_text().strip())
                                ship = re.sub(r"\s+", " ", departure.locator(".ship").inner_text().strip())
                                trip_data["departures"].append({"date": date, "ship": ship})
                            except:
                                pass  # Ignore if parsing fails

                    trips.append(trip_data)

                except Exception as e:
                    print("Error extracting trip:", e)

            browser.close()
            return trips

# Manual test
if __name__ == "__main__":
    parser = TripParser()
    trips = parser.fetch_trips(limit=10)
    for trip in trips:
        print(trip)
