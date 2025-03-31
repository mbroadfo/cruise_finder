import logging
from datetime import datetime, timedelta

# Base URL constants
BASE_URL = "https://www.expeditions.com"

# Default date range for testing
START_DATE = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
END_DATE = (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d")

# Override date range for testing
#START_DATE = "2025-04-01"
#END_DATE = "2025-12-31"

# Function to convert date to timestamp
def date_to_timestamp(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

START_TIMESTAMP = date_to_timestamp(START_DATE)
END_TIMESTAMP = date_to_timestamp(END_DATE)

# Construct departures URL
DEPARTURES_URL = f"https://www.expeditions.com/book?dateRange={START_TIMESTAMP}%253A{END_TIMESTAMP}"

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
