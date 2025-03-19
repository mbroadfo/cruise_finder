import csv
import json
import logging
import os
from datetime import datetime
from typing import Any

def save_to_json(trips: list[dict[str, Any]], output_folder: str = "output") -> None:
    """
    Saves the trip data to a JSON file before conversion to CSV.
    The file name includes a timestamp to retain history.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{output_folder}/trips_{date_str}.json"

    os.makedirs(output_folder, exist_ok=True)

    logging.info(f"Saving trips to JSON: {filename}")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(trips, f, indent=4)
    except PermissionError as e:
        logging.error(f"Permission error when trying to write to {filename}: {e}")

def save_to_csv(trips: list[dict[str, Any]], output_folder: str = "output") -> None:
    """
    Saves trip data to a CSV file, only including departures that have available cabins.
    The file name includes a timestamp to retain history.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{output_folder}/trips_with_availability_{date_str}.csv"

    os.makedirs(output_folder, exist_ok=True)

    # Save JSON before processing CSV
    save_to_json(trips, output_folder)

    logging.info(f"Saving available trips to CSV: {filename}")

    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Trip Name", "Start Date", "End Date", "Ship", "Booking URL",
                             "Category Name", "Deck", "Occupancy", "Cabin Type", "Price", "Status", "Available Cabins"])

            for trip in trips:
                for departure in trip["departures"]:
                    available_categories = [cat for cat in departure["categories"] if cat["status"] == "Available"]

                    if available_categories:
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
