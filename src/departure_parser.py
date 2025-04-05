import logging
from config import BASE_URL, END_DATE
from typing import Any
from datetime import datetime

def fetch_departures(page: Any, trip: Any) -> list[dict[str, str]]:
    departures: list[dict[str, str]] = []
    latest_year = None
    seen_urls = set()

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

            while True:
                elements = departure_container_locator.locator("li")
                element_count = elements.count()

                if element_count == 0:
                    logging.info("  No visible departures found for this trip. Skipping.")
                    break

                stop_due_to_date = False

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

                    booking_url = booking_url_locator.get_attribute("href")
                    if booking_url and not booking_url.startswith("http"):
                        booking_url = BASE_URL + booking_url

                    if not booking_url or booking_url in seen_urls:
                        continue  # Skip duplicates

                    start_date = f"{latest_year} {date_range[0].strip()}"
                    end_date = f"{latest_year} {date_range[1].strip()}"

                    try:
                        parsed_start = datetime.strptime(start_date, "%Y %b %d")
                        end_cutoff = datetime.strptime(END_DATE, "%Y-%m-%d")
                        if parsed_start > end_cutoff:
                            logging.info(f"🛑 Departure start date {start_date} exceeds END_DATE filter ({END_DATE}). Stopping.")
                            stop_due_to_date = True
                            break

                    except Exception as date_err:
                        logging.warning(f"Could not parse end_date '{end_date}': {date_err}")

                    logging.info(f"  Found departure: {start_date} to {end_date}, Ship: {ship_name}, URL: {booking_url}")

                    departures.append({
                        "start_date": start_date,
                        "end_date": end_date,
                        "ship": ship_name,
                        "booking_url": booking_url
                    })
                    seen_urls.add(booking_url)

                if stop_due_to_date:
                    break

                show_more = departure_container_locator.locator("span", has_text="Show more")
                if show_more.count() > 0:
                    logging.info("  🔽 Clicking 'Show more' to load more departures...")
                    try:
                        show_more.first.scroll_into_view_if_needed()
                        show_more.first.click()
                        page.wait_for_timeout(2000)
                    except Exception as e:
                        logging.warning(f"⚠️ Failed to click 'Show more': {e}")
                        break
                else:
                    break

    except Exception as e:
        logging.error(f"Error fetching departures: {e}")

    return departures
