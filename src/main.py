# File: ./src/main.py

import logging
from trip_parser import TripParser

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = TripParser()
    trips = parser.fetch_trips(limit=2)
    
    for trip in trips:
        print(trip)

if __name__ == "__main__":
    main()
