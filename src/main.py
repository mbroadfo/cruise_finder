import logging
from trip_parser import TripParser
from csv_export_module import save_to_csv

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = TripParser()
    trips = parser.fetch_trips(limit=50)
    
    if trips:
        save_to_csv(trips)  # Call the CSV export function
    else:
        logging.info("No trips with available departures found. Skipping CSV export.")

if __name__ == "__main__":
    main()
