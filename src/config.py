import logging

# API and URL constants
ALGOLIA_URL = "https://prru6fnc68-dsn.algolia.net/1/indexes/*/queries"
ALGOLIA_API_KEY = "a226920ace4729832564b5c9babef20c"
ALGOLIA_APP_ID = "PRRU6FNC68"
BASE_URL = "https://www.expeditions.com"
DEPARTURES_URL = "https://www.expeditions.com/book?dateRange=1747116000%253A1748498400"

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
