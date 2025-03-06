import csv
import logging
import os
from datetime import datetime

def save_to_csv(trips, output_folder="output"):
    """
    Saves trip data to a CSV file, only including departures that have available cabins.
    The file name includes a timestamp to retain history.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")  # Format YYYY-MM-DD for sorting
    filename = f"{output_folder}/trips_with_availability_{date_str}.csv"
    
    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # If the file already exists, delete it before opening
    if os.path.exists(filename):
        os.remove(filename)
    
    logging.info(f"Saving available trips to {filename}...")
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Trip Name", "Start Date", "End Date", "Ship", "Booking URL",
                             "Category Name", "Deck", "Occupancy", "Cabin Type", "Price", "Status", "Available Cabins"])
            
            for trip in trips:
                for departure in trip["departures"]:
                    available_categories = [cat for cat in departure["categories"] if cat["status"] == "Available"]
                    
                    if available_categories:  # Only save trips with available cabins
                        full_booking_url = departure.get("booking_url", "")
                        if full_booking_url and not full_booking_url.startswith("http"):
                            full_booking_url = "https://www.expeditions.com" + full_booking_url
                        
                        for category in available_categories:
                            writer.writerow([
                                trip["trip_name"], departure["start_date"], departure["end_date"], departure["ship"], full_booking_url,
                                category["category_name"], category["deck"], category["occupancy"], category["cabin_type"], category["price"],
                                category["status"], category["num_cabins"]
                            ])
    except PermissionError as e:
        logging.error(f"Permission error when trying to write to {filename}: {e}")
    
    logging.info(f"CSV export complete. Saved to {filename}")
