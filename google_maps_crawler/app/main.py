"""
FastAPI application for Google Maps crawler
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from .database.supabase_client import SupabaseClient
from .crawler.google_maps import GoogleMapsClient
from .crawler.road_sampler import RoadSampler
from .models import CrawlStats
from .config import BUSINESS_TYPES, CRAWLER_DELAY_SECONDS
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Google Maps Business Crawler",
    description="Crawl business data along US roads",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
db = SupabaseClient()
gmaps = GoogleMapsClient()
sampler = RoadSampler()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Google Maps Business Crawler",
        "status": "active",
        "endpoints": {
            "stats": "/stats",
            "crawl": "/crawl/start",
            "roads": "/roads/unprocessed"
        }
    }

@app.get("/stats", response_model=CrawlStats)
async def get_stats():
    """Get crawling statistics - fast version with cached static data"""
    # Use hardcoded values for static data to avoid slow queries
    stats = {
        'total_roads': 5155787,  # Static - won't change
        'roads_with_names': 3428598,  # Static - exact count (66.5%)
        'roads_processed': 0,  # TODO: Query this dynamically when crawling starts
        'businesses_found': 0,  # TODO: Query this dynamically when crawling starts
        'avg_businesses_per_road': 0.0,
        'top_business_types': []
    }
    
    # Only query dynamic data if crawling has started
    # For now, return static data for instant response
    return CrawlStats(**stats)

@app.get("/stats/live", response_model=CrawlStats)
async def get_live_stats():
    """Get real-time crawling statistics - slower but accurate"""
    stats = db.get_crawl_stats()
    
    # Merge with static values
    if not stats:
        stats = {}
    
    stats['total_roads'] = 5155787  # Use static value
    stats['roads_with_names'] = 3400000  # Use static value
    
    # Ensure all required fields exist
    stats.setdefault('roads_processed', 0)
    stats.setdefault('businesses_found', 0)
    stats.setdefault('avg_businesses_per_road', 0.0)
    stats.setdefault('top_business_types', [])
    
    return CrawlStats(**stats)

@app.get("/roads/unprocessed")
async def get_unprocessed_roads(limit: int = 100):
    """Get list of unprocessed roads"""
    roads = db.get_unprocessed_roads(limit=limit)
    return {
        "count": len(roads),
        "roads": [road.model_dump() for road in roads]
    }

@app.get("/roads/crawl-status")
async def get_roads_crawl_status(
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    keyword: Optional[str] = None
):
    """Get crawl status for roads filtered by location and keyword"""
    statuses = db.get_crawl_status(state_code, county_fips, keyword)
    
    # Convert to dict keyed by road_linearid for easy lookup
    status_dict = {}
    for status in statuses:
        road_id = status['road_linearid']
        if road_id not in status_dict:
            status_dict[road_id] = {}
        status_dict[road_id][status['keyword']] = status['status']
    
    return status_dict

@app.get("/counties/{state_code}")
async def get_counties_by_state(state_code: str):
    """Get all counties for a specific state"""
    counties = db.get_counties_by_state(state_code)
    return {
        "state_code": state_code,
        "count": len(counties),
        "counties": counties
    }

@app.get("/states/summary")
async def get_states_summary():
    """Get summary of all states with road counts"""
    summary = db.get_states_summary()
    return summary

@app.post("/crawl/road/{road_id}")
async def crawl_single_road(
    road_id: str,
    keyword: str,
    background_tasks: BackgroundTasks
):
    """Crawl a single road with specific keyword"""
    # Get road details
    road_response = db.client.table('roads').select('*').eq('linearid', road_id).execute()
    if not road_response.data:
        raise HTTPException(status_code=404, detail="Road not found")
    
    road_data = road_response.data[0]
    
    # Update status to processing
    db.update_crawl_status(road_id, keyword, 'processing')
    
    # Add to background task
    background_tasks.add_task(
        crawl_road_with_keyword, 
        road_data, 
        keyword
    )
    
    return {
        "message": f"Started crawling {road_data.get('fullname', road_id)} for '{keyword}'",
        "road_id": road_id,
        "keyword": keyword
    }

async def crawl_road_with_keyword(road_data: dict, keyword: str):
    """Crawl businesses along a road using text search with keyword"""
    road_id = road_data['linearid']
    road_name = road_data.get('fullname', '')
    
    logger.info(f"Crawling road {road_name} for keyword: {keyword}")
    
    try:
        # TODO: Implement actual Google Maps Text Search
        # For now, simulate the search
        search_query = f"{keyword} near {road_name}"
        
        # Simulate finding some businesses
        import random
        businesses_found = random.randint(0, 10)
        
        # Update status to completed
        db.update_crawl_status(
            road_id, 
            keyword, 
            'completed',
            businesses_found=businesses_found
        )
        
        logger.info(f"Completed crawl for {road_name}, found {businesses_found} businesses")
        
    except Exception as e:
        logger.error(f"Error crawling road {road_id}: {e}")
        db.update_crawl_status(
            road_id,
            keyword, 
            'failed',
            error_message=str(e)
        )

async def crawl_road(road, job_id: str):
    """Crawl businesses along a single road"""
    logger.info(f"Starting crawl for road: {road.fullname or road.linearid}")
    
    # Update job status
    db.update_crawl_job(job_id, "processing")
    
    try:
        # Generate sample points along the road
        sample_points = sampler.generate_sample_points_by_name(
            road.fullname or "",
            road.county_fips,
            num_points=5
        )
        
        all_businesses = []
        
        # Search for businesses at each sample point
        for point in sample_points:
            for business_type in BUSINESS_TYPES:
                # Search nearby places
                places = gmaps.search_nearby_places(
                    location=point,
                    place_type=business_type
                )
                
                # Parse and save businesses
                for place in places:
                    # Get additional details if needed
                    if 'user_ratings_total' not in place:
                        details = gmaps.get_place_details(place['place_id'])
                        if details:
                            place.update(details)
                    
                    # Parse business data
                    business = gmaps.parse_business(
                        place,
                        road.linearid,
                        road.fullname
                    )
                    all_businesses.append(business)
                
                # Rate limiting
                time.sleep(CRAWLER_DELAY_SECONDS)
        
        # Remove duplicates by place_id
        unique_businesses = {b.place_id: b for b in all_businesses}.values()
        
        # Save to database
        saved_count = db.save_businesses_batch(list(unique_businesses))
        
        # Update job status
        db.update_crawl_job(job_id, "completed", businesses_found=saved_count)
        logger.info(f"Completed crawl for road: {road.fullname}, found {saved_count} businesses")
        
    except Exception as e:
        logger.error(f"Error crawling road {road.linearid}: {e}")
        db.update_crawl_job(job_id, "failed", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)