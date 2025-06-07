"""
FastAPI application for Google Maps crawler
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from .database.postgres_client import PostgresClient
from .crawler.google_maps import GoogleMapsClient
from .crawler.road_sampler import RoadSampler
from .models import CrawlStats
from .config import BUSINESS_TYPES, CRAWLER_DELAY_SECONDS
from .crawler.enhanced_search import search_roads_enhanced
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
db = PostgresClient()
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
    """Get crawling statistics - fast version with OSM data counts"""
    # Query OSM data stats
    from .database.postgres_client import execute_query
    
    # Get stats from cache table (INSTANT!)
    stats_result = execute_query("""
        SELECT 
            total_segments as total_roads,
            unique_roads_with_names as roads_with_names,
            last_updated
        FROM osm_stats_cache
        WHERE id = 1
    """, fetch_one=True)
    
    result = stats_result if stats_result else {
        'total_roads': 0,
        'roads_with_names': 0
    }
    
    # Get dynamic crawl stats
    crawl_stats = db.get_crawl_stats()
    
    stats = {
        'total_roads': result['total_roads'] if result else 0,
        'roads_with_names': result['roads_with_names'] if result else 0,
        'roads_processed': crawl_stats.get('roads_processed', 0),
        'businesses_found': crawl_stats.get('businesses_found', 0),
        'avg_businesses_per_road': crawl_stats.get('avg_businesses_per_road', 0.0),
        'top_business_types': []
    }
    
    return CrawlStats(**stats)

@app.get("/stats/live", response_model=CrawlStats)
async def get_live_stats():
    """Get real-time crawling statistics - same as /stats for OSM"""
    return await get_stats()

@app.get("/roads/unprocessed")
async def get_unprocessed_roads(
    limit: int = 100,
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None
):
    """Get list of unique road names with optional filters"""
    roads = db.get_unique_road_names(limit=limit, state_code=state_code, county_fips=county_fips)
    return {
        "count": len(roads),
        "roads": roads
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

@app.get("/roads/search")
async def search_roads(
    q: str,
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    limit: int = 50
):
    """Enhanced road search with name normalization (handles OSM vs Google differences)"""
    from .database.postgres_client import get_connection
    
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    try:
        conn = get_connection()
        results = search_roads_enhanced(conn, q, state_code, county_fips, limit)
        
        return {
            "query": q,
            "normalized_search": True,
            "count": len(results),
            "results": results,
            "note": "Results include normalized variations (e.g., '10th Avenue' also searches for '10th Ave', '10th Street', 'W 10th St')"
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/crawl/road/{road_id}")
async def crawl_single_road(
    road_id: str,
    keyword: str,
    background_tasks: BackgroundTasks
):
    """Crawl a single road with specific keyword"""
    # Get road details
    # Get road details using PostgreSQL
    from .database.postgres_client import execute_query
    road_data = execute_query(
        """
        SELECT 
            osm_id,
            name,
            highway,
            ref,
            county_fips,
            state_code,
            ST_AsText(geometry) as geom_text,
            ST_X(ST_Centroid(geometry)) as center_lon,
            ST_Y(ST_Centroid(geometry)) as center_lat,
            lanes,
            maxspeed,
            surface
        FROM osm_roads_main 
        WHERE osm_id = %s
        """, 
        (int(road_id),), 
        fetch_one=True
    )
    if not road_data:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # road_data is already a dict from execute_query
    
    # Update status to processing
    db.update_crawl_status(road_id, keyword, 'processing')
    
    # Add to background task
    background_tasks.add_task(
        crawl_road_with_keyword, 
        road_data, 
        keyword
    )
    
    return {
        "message": f"Started crawling {road_data.get('name', road_id)} for '{keyword}'",
        "road_id": road_id,
        "keyword": keyword
    }

async def crawl_road_with_keyword(road_data: dict, keyword: str):
    """Crawl businesses along a road using enhanced search strategy"""
    from .crawler.enhanced_search import EnhancedRoadSearch
    
    road_id = road_data['osm_id']
    road_name = road_data.get('name', '')
    
    logger.info(f"Crawling road {road_name} for keyword: {keyword}")
    
    try:
        # Get enhanced search information
        searcher = EnhancedRoadSearch()
        search_info = searcher.get_search_info(road_id)
        
        if not search_info:
            raise Exception(f"Could not get search info for road {road_id}")
        
        logger.info(f"Using name: {road_name} for search")
        
        # Try multiple search strategies
        total_businesses = 0
        
        # Strategy 1: Search by coordinates (most reliable)
        if search_info['center_point'][0] and search_info['center_point'][1]:
            search_params = searcher.build_search_query(keyword, search_info, 'coordinates')
            logger.info(f"Searching by coordinates: {search_params['location']} with radius {search_params['radius']}m")
            # TODO: Call Google Maps API with coordinates
            # results = gmaps.nearby_search(**search_params)
            # total_businesses += len(results)
        
        # Strategy 2: Search by text with proper name
        search_params = searcher.build_search_query(keyword, search_info, 'text_search')
        logger.info(f"Text search query: {search_params['query']}")
        # TODO: Call Google Maps API with text search
        # results = gmaps.text_search(search_params['query'])
        # total_businesses += len(results)
        
        # Get all segments to mark as complete
        all_segments = execute_query(
            "SELECT osm_id FROM osm_roads_main WHERE name = %s AND county_fips = %s",
            (road_name, road_data.get('county_fips'))
        )
        
        # Update crawl status for all segments
        for segment in all_segments:
            db.update_crawl_status(
                str(segment['osm_id']), 
                keyword, 
                'completed',
                businesses_found=total_businesses
            )
        
        logger.info(f"Completed crawl for {road_name} ({len(all_segments)} segments, {total_businesses} businesses)")
        
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
    logger.info(f"Starting crawl for road: {road.name or road.osm_id}")
    
    # Update job status
    db.update_crawl_job(job_id, "processing")
    
    try:
        # Generate sample points along the road
        sample_points = sampler.generate_sample_points_by_name(
            road.name or "",
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
                        road.osm_id,
                        road.name
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
        logger.info(f"Completed crawl for road: {road.name}, found {saved_count} businesses")
        
    except Exception as e:
        logger.error(f"Error crawling road {road.osm_id}: {e}")
        db.update_crawl_job(job_id, "failed", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)