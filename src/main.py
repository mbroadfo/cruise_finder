import logging
from trip_parser import TripParser
from save_trips import save_to_csv, save_to_json  # Updated import

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = TripParser()
    trips = parser.fetch_trips(limit=50)

    if trips:
        save_to_json(trips)  # Save JSON first
        save_to_csv(trips)   # Then save CSV
    else:
        logging.info("No trips with available departures found. Skipping CSV export.")

if __name__ == "__main__":
    main()
