import csv
import json
import logging
import os
from datetime import datetime
from typing import Any
import os
import boto3

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
S3_BUCKET_NAME = "mytripdata8675309"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

OUTPUT_FOLDER = "output"
JSON_FILENAME = f"{OUTPUT_FOLDER}/trip_list.json"

def save_to_json(trips: list[dict[str, Any]]) -> str:
    """
    Saves the trip data to a JSON file without a date stamp.
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    logging.info(f"Saving trips to JSON: {JSON_FILENAME}")

    try:
        with open(JSON_FILENAME, "w", encoding="utf-8") as f:
            json.dump(trips, f, indent=4)

        logging.info("✅ JSON file saved successfully.")
        upload_to_s3(JSON_FILENAME)
    except PermissionError as e:
        logging.error(f"❌ Permission error writing to {JSON_FILENAME}: {e}")

    return JSON_FILENAME

def upload_to_s3(file_path: str) -> None:
    """
    Uploads the JSON file to the AWS S3 bucket as `trip_list.json`.
    """
    s3_key = "trip_list.json"  # Keep a single, consistent filename in S3

    try:
        s3.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        logging.info(f"✅ Successfully uploaded to s3://{S3_BUCKET_NAME}/{s3_key}")
    except Exception as e:
        logging.error(f"❌ Failed to upload to S3: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    if os.path.exists(JSON_FILENAME):
        logging.info("✅ JSON file already exists. Uploading to S3.")
        upload_to_s3(JSON_FILENAME)  # This will also upload to S3
    else:
        logging.info("No JSON file found. Skipping upload.")
        