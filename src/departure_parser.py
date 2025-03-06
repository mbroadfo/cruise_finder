import logging
from config import BASE_URL  # Import BASE_URL instead of hardcoding

def fetch_departures(page, trip):
    departures = []
    latest_year = None  # Reset latest_year at the start of each trip's departures
    
    try:
        show_departures_button = trip.locator("button", has_text="See departure dates")
        if show_departures_button.count() > 0:
            try:
                show_departures_button.first.scroll_into_view_if_needed()
                page.wait_for_timeout(1000)  
                show_departures_button.first.click(timeout=15000)  
            except Exception as e:
                logging.warning(f"Failed to click 'See departure dates': {e}")
                return departures
            
            departure_container_locator = trip.locator("[class^='hits_departureHitsContainer__']")
            page.wait_for_timeout(2000)  
            if departure_container_locator.count() == 0:
                logging.warning("Departure list did not appear.")
                return departures

            elements = departure_container_locator.locator("li")
            element_count = elements.count()

            if element_count == 0:
                logging.info("  No visible departures found for this trip. Skipping.")
                return departures

            for i in range(element_count):
                departure = elements.nth(i)

                year_locator = departure.locator("[data-testid='departure-hit-year']")
                date_range_locator = departure.locator("p[class*='drDbhx']")
                ship_name_locator = departure.locator("i")
                booking_url_locator = departure.locator("a")
                land_expedition_locator = departure.locator("div[data-land-expedition='true']")

                if year_locator.count() > 0:
                    latest_year = year_locator.text_content().strip()
                    logging.info(f"  Processing Departures for: {latest_year}")

                missing_fields = []
                if latest_year is None:
                    missing_fields.append("year")
                if date_range_locator.count() < 2:
                    missing_fields.append("date range")
                if booking_url_locator.count() == 0:
                    missing_fields.append("booking URL")

                if missing_fields:
                    logging.warning(f"Skipping departure {i} due to missing fields: {', '.join(missing_fields)}")
                    continue

                date_range = date_range_locator.all_text_contents()
                ship_name = "Land Expedition" if land_expedition_locator.count() > 0 else ship_name_locator.text_content().strip()
                
                # Ensure the booking URL has the full domain using BASE_URL
                booking_url = booking_url_locator.get_attribute("href")
                if booking_url and not booking_url.startswith("http"):
                    booking_url = BASE_URL + booking_url  # Now using config.py

                start_date = f"{latest_year} {date_range[0].strip()}"
                end_date = f"{latest_year} {date_range[1].strip()}"

                logging.info(f"  Found departure: {start_date} to {end_date}, Ship: {ship_name}, URL: {booking_url}")

                departures.append({
                    "start_date": start_date,
                    "end_date": end_date,
                    "ship": ship_name,
                    "booking_url": booking_url
                })
    except Exception as e:
        logging.error(f"Error fetching departures: {e}")

    return departures
