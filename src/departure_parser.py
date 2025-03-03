from config import BASE_URL, logger
from category_parser import CategoryParser
import asyncio

async def fetch_departures(page, trip):
    departures = []
    latest_year = None  # Reset latest_year at the start of each trip's departures
    
    try:
        show_departures_button = trip.locator("button", has_text="See departure dates")
        if show_departures_button.count() > 0:
            await show_departures_button.first.click()
            await page.wait_for_timeout(200)
            
            departure_container_locator = trip.locator("[class^='hits_departureHitsContainer__']")
            if departure_container_locator.count() == 0:
                return departures
            
            elements = departure_container_locator.locator("li")
            element_count = elements.count()
            
            if element_count == 0:
                logger.info("No visible departures found for this trip. Skipping.")
                return departures
            
            for i in range(element_count):
                departure = elements.nth(i)
                
                year_locator = departure.locator("[data-testid='departure-hit-year']")
                date_range_locator = departure.locator("p[class*='drDbhx']")
                ship_name_locator = departure.locator("i")
                booking_url_locator = departure.locator("a")
                land_expedition_locator = departure.locator("div[data-land-expedition='true']")
                
                if year_locator.count() > 0:
                    latest_year = await year_locator.text_content()
                    logger.info(f"Found year line item: {latest_year}")
                
                missing_fields = []
                if latest_year is None:
                    missing_fields.append("year")
                if date_range_locator.count() < 2:
                    missing_fields.append("date range")
                if booking_url_locator.count() == 0:
                    missing_fields.append("booking URL")
                
                if missing_fields:
                    logger.warning(f"Skipping departure {i} due to missing fields: {', '.join(missing_fields)}")
                    continue
                
                date_range = await date_range_locator.all_text_contents()
                ship_name = "Land Expedition" if land_expedition_locator.count() > 0 else await ship_name_locator.text_content()
                ship_name = ship_name.strip()
                booking_url = await booking_url_locator.get_attribute("href")
                
                start_date = f"{latest_year} {date_range[0].strip()}"
                end_date = f"{latest_year} {date_range[1].strip()}"
                
                full_booking_url = f"{BASE_URL}{booking_url}"
                logger.info(f"Fetching categories for departure: {start_date} to {end_date}, Ship: {ship_name}")
                
                try:
                    category_parser = CategoryParser(full_booking_url)
                    categories = await category_parser.fetch_categories()
                except Exception as e:
                    logger.error(f"Error fetching categories for {full_booking_url}: {e}")
                    categories = []
                
                departures.append({
                    "start_date": start_date,
                    "end_date": end_date,
                    "ship": ship_name,
                    "booking_url": full_booking_url,
                    "categories": categories
                })
    except Exception as e:
        logger.error(f"Error fetching departures: {e}")

    return departures
