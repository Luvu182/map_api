"""
Configuration settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Google Maps
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Crawler settings
CRAWLER_BATCH_SIZE = int(os.getenv("CRAWLER_BATCH_SIZE", "50"))
CRAWLER_DELAY_SECONDS = float(os.getenv("CRAWLER_DELAY_SECONDS", "1"))
MAX_RESULTS_PER_LOCATION = int(os.getenv("MAX_RESULTS_PER_LOCATION", "20"))
SEARCH_RADIUS_METERS = int(os.getenv("SEARCH_RADIUS_METERS", "50"))

# Rate limiting
GOOGLE_MAPS_REQUESTS_PER_SECOND = 10
GOOGLE_MAPS_DAILY_LIMIT = 25000  # Free tier

# Business types to search
BUSINESS_TYPES = [
    "restaurant",
    "store", 
    "shopping_mall",
    "gas_station",
    "bank",
    "pharmacy",
    "hospital",
    "school",
    "gym",
    "cafe",
    "bar",
    "hotel",
    "supermarket",
    "convenience_store",
    "hair_care",
    "car_repair"
]