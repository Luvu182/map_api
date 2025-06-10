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
from .crawler.enhanced_search_optimized import search_roads_enhanced
from .api.analyze_location import router as analyze_router
from .api.businesses_api import router as businesses_router
from .api.crawl_sessions_api import router as sessions_router
from .api.roads_api import router as roads_router
from .api.auth_api import router as auth_router
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Google Maps Business Crawler",
    description="Crawl business data along US roads",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(analyze_router)
app.include_router(businesses_router)
app.include_router(sessions_router)
app.include_router(roads_router)

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

# Initialize API tracking table on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        from .database.postgres_client import execute_query
        # Create API tracking table
        execute_query("""
            CREATE TABLE IF NOT EXISTS api_calls (
                id SERIAL PRIMARY KEY,
                api_type VARCHAR(50) NOT NULL,
                endpoint VARCHAR(255),
                request_count INTEGER DEFAULT 1,
                session_id VARCHAR(255),
                road_osm_id BIGINT,
                keyword VARCHAR(255),
                response_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        execute_query("CREATE INDEX IF NOT EXISTS idx_api_calls_created_at ON api_calls(created_at)")
        execute_query("CREATE INDEX IF NOT EXISTS idx_api_calls_api_type ON api_calls(api_type)")
        logger.info("API tracking table initialized")
    except Exception as e:
        logger.error(f"Failed to initialize API tracking: {e}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Google Maps Business Crawler",
        "status": "active",
        "endpoints": {
            "stats": "/stats",
            "roads_by_city": "/api/roads/by-city",
            "target_cities": "/api/roads/target-cities",
            "city_stats": "/api/roads/city-stats",
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

@app.get("/api/usage")
async def get_api_usage():
    """Get API usage statistics from crawl sessions"""
    from .database.postgres_client import execute_query
    
    try:
        # Get total crawls (each crawl uses API calls)
        total_crawls = execute_query("""
            SELECT 
                COUNT(*) as total_crawls,
                SUM(businesses_found) as total_results,
                COUNT(DISTINCT DATE(started_at)) as days_active
            FROM crawl_sessions
            WHERE status = 'completed'
        """, fetch_one=True)
        
        # Estimate API requests (each crawl with 60 results = 3 requests)
        estimated_requests = (total_crawls['total_crawls'] or 0) * 3
        
        # Get crawls by keyword
        by_keyword = execute_query("""
            SELECT 
                keyword,
                COUNT(*) as crawl_count,
                SUM(businesses_found) as total_results,
                AVG(businesses_found) as avg_results
            FROM crawl_sessions
            WHERE status = 'completed'
            GROUP BY keyword
            ORDER BY crawl_count DESC
            LIMIT 10
        """)
        
        # Get today's usage
        today_usage = execute_query("""
            SELECT 
                COUNT(*) as crawl_count,
                SUM(businesses_found) as total_results
            FROM crawl_sessions
            WHERE DATE(started_at) = CURRENT_DATE
            AND status = 'completed'
        """, fetch_one=True)
        
        # Get daily usage for last 7 days
        daily_usage = execute_query("""
            SELECT 
                DATE(started_at) as date,
                COUNT(*) as crawl_count,
                SUM(businesses_found) as total_results
            FROM crawl_sessions
            WHERE started_at >= CURRENT_DATE - INTERVAL '7 days'
            AND status = 'completed'
            GROUP BY DATE(started_at)
            ORDER BY date DESC
        """)
        
        # Get recent crawls
        recent_crawls = execute_query("""
            SELECT 
                road_name,
                keyword,
                businesses_found,
                started_at,
                EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
            FROM crawl_sessions
            WHERE status = 'completed'
            ORDER BY started_at DESC
            LIMIT 10
        """)
        
        # Calculate estimated API calls
        today_api_calls = (today_usage['crawl_count'] or 0) * 3
        
        return {
            "total_requests": estimated_requests,
            "total_crawls": total_crawls['total_crawls'] or 0,
            "total_results": total_crawls['total_results'] or 0,
            "by_keyword": by_keyword,
            "today": {
                "crawls": today_usage['crawl_count'] or 0,
                "estimated_api_calls": today_api_calls,
                "results": today_usage['total_results'] or 0
            },
            "daily_usage": daily_usage,
            "recent_crawls": recent_crawls,
            "notes": {
                "text_search_60_results": "Each search for 60 results counts as 3 API requests",
                "pricing": {
                    "text_search": {
                        "cost_per_request": "$32.00 per 1,000 requests",
                        "unit_price": 0.032
                    },
                    "place_details": {
                        "cost_per_request": "$17.00 per 1,000 requests", 
                        "unit_price": 0.017
                    },
                    "basic_data": {
                        "cost_per_request": "$5.00 per 1,000 requests",
                        "unit_price": 0.005
                    }
                },
                "estimated_cost": f"${estimated_requests * 0.032:.2f}",
                "monthly_estimate": f"${estimated_requests * 0.032 * 30:.2f}/month at current rate"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting API usage: {e}")
        return {
            "total_requests": 0,
            "error": str(e)
        }

@app.get("/roads/unprocessed")
async def get_unprocessed_roads(
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    limit: int = 50
):
    """Get list of unprocessed roads for crawling"""
    roads = db.get_unprocessed_roads(state_code, county_fips, limit)
    return {"roads": roads, "count": len(roads)}

@app.get("/crawl/status")
async def get_crawl_status(
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    keyword: Optional[str] = None
):
    """Get crawl status for roads"""
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
    keyword: str = "all"
):
    """Crawl a single road - synchronous with real-time updates"""
    from .database.postgres_client import execute_query
    import uuid
    
    # Get road details
    road_data = execute_query(
        """
        SELECT 
            r.osm_id,
            r.name,
            r.highway,
            r.ref,
            r.county_fips,
            r.state_code,
            ST_X(ST_Centroid(r.geometry)) as center_lon,
            ST_Y(ST_Centroid(r.geometry)) as center_lat,
            rcm.city_name
        FROM osm_roads_main r
        LEFT JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE r.osm_id = %s
        LIMIT 1
        """, 
        (int(road_id),), 
        fetch_one=True
    )
    
    if not road_data:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Create crawl session
    session_id = str(uuid.uuid4())
    execute_query(
        """
        INSERT INTO crawl_sessions (
            id, road_osm_id, road_name, city_name, state_code, keyword, status
        ) VALUES (%s, %s, %s, %s, %s, %s, 'crawling')
        """,
        (session_id, road_data['osm_id'], road_data['name'], 
         road_data.get('city_name'), road_data['state_code'], keyword)
    )
    
    try:
        # Perform crawl synchronously
        businesses = await crawl_road_now(road_data, keyword, session_id)
        
        # Ensure businesses is not None
        if businesses is None:
            businesses = []
        
        # Update session as completed
        execute_query(
            """
            UPDATE crawl_sessions 
            SET status = 'completed', 
                businesses_found = %s,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (len(businesses), session_id)
        )
        
        return {
            "session_id": session_id,
            "status": "completed",
            "businesses_found": len(businesses),
            "road_name": road_data.get('name'),
            "message": f"Successfully crawled {len(businesses)} businesses"
        }
        
    except Exception as e:
        # Update session as failed
        execute_query(
            """
            UPDATE crawl_sessions 
            SET status = 'failed', 
                error_message = %s,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (str(e), session_id)
        )
        
        raise HTTPException(status_code=500, detail=str(e))

async def crawl_road_now(road_data: dict, keyword: str, session_id: str):
    """Crawl businesses along a road using new Text Search API"""
    from .database.postgres_client import execute_query
    
    road_id = road_data['osm_id']
    road_name = road_data.get('name', '')
    state_code = road_data.get('state_code', '')
    county_fips = road_data.get('county_fips', '')
    center_lat = road_data.get('center_lat')
    center_lon = road_data.get('center_lon')
    
    logger.info(f"Crawling road {road_name} for keyword: {keyword}")
    
    try:
        # Get city name for better search
        city_result = execute_query(
            """
            SELECT DISTINCT city_name 
            FROM road_city_mapping 
            WHERE road_id = (SELECT id FROM osm_roads_main WHERE osm_id = %s LIMIT 1)
            LIMIT 1
            """,
            (road_id,),
            fetch_one=True
        )
        city_name = city_result['city_name'] if city_result else ''
        
        # Use new Text Search API - much more efficient!
        # Search directly for businesses on this road
        businesses = []
        
        # If we have keyword, search for specific type
        if keyword and keyword != 'all':
            query = f"{keyword} on {road_name}, {city_name}, {state_code}"
        else:
            query = f"businesses on {road_name}, {city_name}, {state_code}"
        
        logger.info(f"Text search query: {query}")
        
        # Call new API method
        results = gmaps.search_businesses_on_road(
            road_name=road_name,
            city_name=city_name,
            state_code=state_code,
            center_lat=center_lat,
            center_lng=center_lon,
            business_type=keyword if keyword != 'all' else None
        )
        
        # Check if results is None or empty
        if results is None:
            logger.warning(f"No results returned for {road_name}")
            results = []
        
        # Process results
        for place_data in results:
            business = gmaps.parse_business(place_data, road_id, road_name)
            # No need to filter by keyword anymore since API already filtered
            businesses.append(business)
        
        # Handle case where businesses might be None
        if businesses is None:
            businesses = []
            
        total_businesses = len(businesses)
        
        # Save businesses to database with session_id
        if businesses:
            saved_businesses = []
            for business in businesses:
                # Save to businesses table with session_id
                result = execute_query(
                    """
                    INSERT INTO businesses (
                        place_id, name, formatted_address, lat, lng,
                        types, rating, user_ratings_total, price_level,
                        phone_number, website, opening_hours,
                        road_osm_id, road_name, distance_to_road,
                        crawled_at, crawl_session_id, city
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (place_id) DO UPDATE SET
                        crawl_session_id = EXCLUDED.crawl_session_id,
                        crawled_at = EXCLUDED.crawled_at
                    RETURNING place_id
                    """,
                    (
                        business.place_id, business.name, business.formatted_address,
                        business.lat, business.lng, business.types, business.rating,
                        business.user_ratings_total, business.price_level,
                        business.phone_number, business.website, 
                        json.dumps(business.opening_hours) if business.opening_hours else None,
                        business.road_osm_id, business.road_name, business.distance_to_road,
                        business.crawled_at, session_id, city_name
                    ),
                    fetch_one=True
                )
                if result:
                    saved_businesses.append(business)
            
            logger.info(f"Saved {len(saved_businesses)} businesses for {road_name}")
            return saved_businesses
        else:
            logger.info(f"No businesses found for {road_name}")
        
        return []
        
    except Exception as e:
        logger.error(f"Error crawling road {road_id}: {e}")
        # Don't call db.update_crawl_status as db might not be initialized
        raise e

async def crawl_road(road, job_id: str):
    """Crawl businesses along a single road"""
    logger.info(f"Starting crawl for road: {road.name or road.osm_id}")
    
    # Update job status
    db.update_crawl_job(job_id, "processing")
    
    try:
        # NEW: Use Text Search API instead of sampling points
        # Get city info for the road
        city_result = execute_query(
            """
            SELECT DISTINCT city_name, state_code
            FROM road_city_mapping rcm
            JOIN osm_roads_main r ON r.id = rcm.road_id 
            WHERE r.osm_id = %s
            LIMIT 1
            """,
            (road.osm_id,),
            fetch_one=True
        )
        
        if city_result:
            # Single API call per road instead of multiple points!
            places = gmaps.search_businesses_on_road(
                road_name=road.name,
                city_name=city_result['city_name'],
                state_code=city_result['state_code']
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
                
                # Get detailed info for each place
                for place in places:
                    if 'place_id' in place:
                        details = gmaps.get_place_details(place['place_id'])
                        if details:
                            business = gmaps.parse_business(details, road.osm_id)
                            all_businesses.append(business)
                
                # Respect rate limits
                time.sleep(CRAWLER_DELAY_SECONDS)
        
        # Save businesses
        for business in all_businesses:
            db.save_business(business)
        
        # Mark road as processed
        db.mark_road_processed(road.osm_id, len(all_businesses))
        
        # Update job status
        db.update_crawl_job(job_id, "completed", len(all_businesses))
        
        logger.info(f"Completed crawl for road: {road.name}, found {len(all_businesses)} businesses")
        
    except Exception as e:
        logger.error(f"Error crawling road {road.osm_id}: {e}")
        db.update_crawl_job(job_id, "failed", error=str(e))

@app.post("/crawl/start")
async def start_crawl(
    background_tasks: BackgroundTasks,
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    limit: int = 10
):
    """Start crawling unprocessed roads"""
    # Get unprocessed roads
    roads = db.get_unprocessed_roads(state_code, county_fips, limit)
    
    if not roads:
        return {"message": "No unprocessed roads found"}
    
    # Create crawl job
    job_id = db.create_crawl_job(len(roads))
    
    # Add roads to background tasks
    for road in roads:
        background_tasks.add_task(crawl_road, road, job_id)
    
    return {
        "job_id": job_id,
        "roads_to_process": len(roads),
        "message": f"Started crawling {len(roads)} roads"
    }

@app.get("/api/roads/by-city")
async def get_roads_by_city(
    state_code: str,
    city_name: str,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 200
):
    """Get roads for a specific city"""
    try:
        from .database.postgres_client import execute_query
        # Use fast materialized view
        roads = execute_query(
            """
            SELECT 
                osm_id,
                road_name,
                city_name,
                state_code,
                highway,
                county_fips
            FROM city_roads_simple
            WHERE state_code = %s 
            AND city_name = %s
            ORDER BY road_name
            LIMIT %s OFFSET %s
            """,
            (state_code, city_name, limit, skip)
        )
        
        # Get crawl status if keyword specified
        if keyword and roads:
            road_ids = [r['osm_id'] for r in roads]
            status_results = execute_query(
                """
                SELECT road_linearid, status
                FROM crawl_status
                WHERE road_linearid = ANY(%s) AND keyword = %s
                """,
                (road_ids, keyword)
            )
            
            # Convert to dict for easy lookup
            status_map = {str(s['road_linearid']): s['status'] for s in status_results}
            
            # Add status to roads
            for road in roads:
                road['crawl_status'] = status_map.get(str(road['osm_id']), 'not_crawled')
        
        # Add business potential scores
        if roads:
            road_ids = [r['osm_id'] for r in roads]
            scores = execute_query(
                """
                SELECT osm_id, poi_count, business_potential_score
                FROM road_business_stats
                WHERE osm_id = ANY(%s)
                """,
                (road_ids,)
            )
            
            score_map = {s['osm_id']: s for s in scores}
            for road in roads:
                score_data = score_map.get(road['osm_id'], {})
                road['poi_count'] = score_data.get('poi_count', 0)
                road['business_potential_score'] = score_data.get('business_potential_score', 0)
        
        return {
            "state_code": state_code,
            "city_name": city_name,
            "total": len(roads),
            "roads": roads
        }
    except Exception as e:
        logger.error(f"Error getting roads by city: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Target cities endpoint moved to roads_api.py

@app.get("/api/roads/city-stats")
async def get_city_stats(state_code: str, city_name: str):
    """Get statistics for a specific city"""
    try:
        from .database.postgres_client import execute_query
        
        # Get road type distribution
        road_types = execute_query(
            """
            SELECT 
                r.highway,
                COUNT(*) as count,
                SUM(rbs.poi_count) as total_pois
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            LEFT JOIN road_business_stats rbs ON r.osm_id = rbs.osm_id
            WHERE rcm.state_code = %s AND rcm.city_name = %s
            GROUP BY r.highway
            ORDER BY count DESC
            """,
            (state_code, city_name)
        )
        
        # Get crawl status summary
        crawl_status = execute_query(
            """
            SELECT 
                cs.status,
                COUNT(DISTINCT cs.road_linearid) as count
            FROM crawl_status cs
            JOIN osm_roads_main r ON r.osm_id = cs.road_linearid::bigint
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.state_code = %s AND rcm.city_name = %s
            GROUP BY cs.status
            """,
            (state_code, city_name)
        )
        
        # Get business potential summary
        potential_summary = execute_query(
            """
            SELECT 
                CASE 
                    WHEN business_potential_score >= 8 THEN 'high'
                    WHEN business_potential_score >= 5 THEN 'medium'
                    WHEN business_potential_score >= 3 THEN 'low'
                    ELSE 'very_low'
                END as potential_level,
                COUNT(*) as count,
                SUM(poi_count) as total_pois
            FROM road_business_stats rbs
            JOIN osm_roads_main r ON r.osm_id = rbs.osm_id
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.state_code = %s AND rcm.city_name = %s
            GROUP BY potential_level
            ORDER BY 
                CASE potential_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END
            """,
            (state_code, city_name)
        )
        
        return {
            "city_name": city_name,
            "state_code": state_code,
            "road_types": road_types,
            "crawl_status": crawl_status,
            "business_potential": potential_summary
        }
    except Exception as e:
        logger.error(f"Error getting city stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include analyze location router
app.include_router(analyze_router)

# Run with uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)