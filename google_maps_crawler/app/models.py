"""
Data models
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class Business(BaseModel):
    """Business entity from Google Maps"""
    place_id: str
    name: str
    formatted_address: Optional[str]
    lat: float
    lng: float
    types: List[str]
    rating: Optional[float]
    user_ratings_total: Optional[int]
    price_level: Optional[int]
    phone_number: Optional[str]
    website: Optional[str]
    opening_hours: Optional[Dict]
    
    # Road association
    road_linearid: str
    road_name: Optional[str]
    distance_to_road: float
    
    # Metadata
    crawled_at: datetime
    data_source: str = "google_maps"

class Road(BaseModel):
    """Road from Supabase"""
    linearid: str
    fullname: Optional[str]
    road_category: str
    county_fips: str
    state_code: str

class CrawlJob(BaseModel):
    """Crawl job for a road or area"""
    job_id: str
    road_linearid: str
    road_name: Optional[str]
    county_fips: str
    state_code: str
    status: str  # pending, processing, completed, failed
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    businesses_found: int = 0
    error_message: Optional[str]

class CrawlStats(BaseModel):
    """Statistics for crawling progress"""
    total_roads: int
    roads_with_names: int
    roads_processed: int
    businesses_found: int
    avg_businesses_per_road: float
    top_business_types: List[Dict]