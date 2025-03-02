# Lindblad Expeditions Trip Scraper

## Overview
This scraper retrieves trip and departure information from Lindblad Expeditions' website using two different methods:

1. **Trip Data** - Retrieved from Algolia's API using `requests`.
2. **Departure Data** - Extracted from the website using `Playwright`.

The scraper integrates these sources to provide detailed trip information, including departure dates, ship names, and booking links.

## Technologies Used
- **Requests**: Used to interact with Algolia's API and fetch trip details.
- **Playwright**: Used to automate browsing and extract departure information dynamically from the website.
- **Logging**: Provides error handling and debugging support.

## How It Works

### 1. Fetching Trips from Algolia
The `fetch_trips` method sends a request to Algolia’s API with filters for trip dates and destinations. The API returns a JSON response with:
- Trip name
- Duration
- Destinations
- Page slug (used to construct the trip URL for further scraping)

### 2. Extracting Departures using Playwright
Once trip data is retrieved, `fetch_departures` navigates to the trip’s page and:
- Clicks the "Show Departures" button (if necessary)
- Waits for the list of departures to load
- Extracts:
  - Departure dates
  - Ship names
  - Booking URLs

### 3. Combining Data
Each trip is enriched with its departure details and returned as a structured JSON object.

## Running the Scraper
Ensure dependencies are installed:
```sh
pip install requests playwright
playwright install
```
Run the script:
```sh
python trip_scraper.py
```

## Notes
- The scraper runs headless by default but can be configured to run with a visible browser for debugging.
- The structure of the website may change over time, requiring updates to the Playwright selectors.
- Rate limiting and API key restrictions may impact frequent requests to Algolia.

