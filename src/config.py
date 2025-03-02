import logging
from datetime import datetime

# Base URL constants
BASE_URL = "https://www.expeditions.com"

# Default date range for testing
DEFAULT_START_DATE = "2025-05-13"
DEFAULT_END_DATE = "2025-05-29"

# Function to convert date to timestamp
def date_to_timestamp(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

# Allow manual date input, fallback to defaults
START_DATE = input(f"Enter start date (YYYY-MM-DD) [default: {DEFAULT_START_DATE}]: ") or DEFAULT_START_DATE
END_DATE = input(f"Enter end date (YYYY-MM-DD) [default: {DEFAULT_END_DATE}]: ") or DEFAULT_END_DATE

START_TIMESTAMP = date_to_timestamp(START_DATE)
END_TIMESTAMP = date_to_timestamp(END_DATE)

# Construct departures URL
DEPARTURES_URL = f"https://www.expeditions.com/book?dateRange={START_TIMESTAMP}%253A{END_TIMESTAMP}"

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
