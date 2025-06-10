"""
PostgreSQL client and database operations (replacing Supabase)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from scripts.database_config import get_db_connection, execute_query

# Re-export for compatibility
get_connection = get_db_connection
from typing import List, Optional, Dict
import logging
from ..models import Road, Business, CrawlJob
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class PostgresClient:
    def __init__(self):
        # Test connection on init
        try:
            conn = get_db_connection()
            conn.close()
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    # Road operations
    def get_roads_with_names(self, state_code: str, limit: int = 100, offset: int = 0) -> List[Road]:
        """Get roads with names for a specific state"""
        try:
            query = """
                SELECT 
                    osm_id,
                    name,
                    highway,
                    ref,
                    county_fips,
                    state_code,
                    ST_AsText(geometry) as geom_text,
                    lanes,
                    maxspeed,
                    surface
                FROM osm_roads_main 
                WHERE state_code = %s AND name IS NOT NULL
                ORDER BY osm_id
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (state_code, limit, offset))
            return [Road(**road) for road in results]
        except Exception as e:
            logger.error(f"Error fetching roads: {e}")
            return []
    
    def get_unprocessed_roads(self, limit: int = 100, state_code: str = None, county_fips: str = None) -> List[Road]:
        """Get roads that haven't been crawled yet with optional filters"""
        try:
            query = """
                SELECT 
                    r.osm_id,
                    r.name,
                    r.highway,
                    r.ref,
                    r.county_fips,
                    r.state_code,
                    ST_AsText(r.geometry) as geom_text,
                    r.lanes,
                    r.maxspeed,
                    r.surface
                FROM osm_roads_main r
                LEFT JOIN (
                    SELECT DISTINCT road_osm_id::bigint as osm_id
                    FROM crawl_jobs 
                    WHERE status = 'completed'
                ) cj ON r.osm_id = cj.osm_id
                WHERE r.name IS NOT NULL 
                AND cj.osm_id IS NULL
            """
            params = []
            
            if state_code:
                query += " AND state_code = %s"
                params.append(state_code)
                
            if county_fips:
                query += " AND county_fips = %s"
                params.append(county_fips)
                
            query += " ORDER BY name LIMIT %s"
            params.append(limit)
            
            results = execute_query(query, params)
            return [Road(**road) for road in results]
        except Exception as e:
            logger.error(f"Error fetching unprocessed roads: {e}")
            return []
    
    # Business operations
    def save_business(self, business: Business) -> bool:
        """Save a business to database"""
        try:
            query = """
                INSERT INTO businesses (
                    place_id, name, formatted_address, lat, lng, rating,
                    user_ratings_total, types, phone_number, website, opening_hours,
                    price_level, road_osm_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (place_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    formatted_address = EXCLUDED.formatted_address,
                    rating = EXCLUDED.rating,
                    user_ratings_total = EXCLUDED.user_ratings_total,
                    updated_at = NOW()
            """
            business_dict = business.model_dump()
            params = (
                business_dict['place_id'],
                business_dict['name'],
                business_dict.get('formatted_address'),
                business_dict.get('lat'),
                business_dict.get('lng'),
                business_dict.get('rating'),
                business_dict.get('user_ratings_total'),
                business_dict.get('types'),
                business_dict.get('phone_number'),
                business_dict.get('website'),
                json.dumps(business_dict.get('opening_hours')) if business_dict.get('opening_hours') else None,
                business_dict.get('price_level'),
                business_dict.get('road_osm_id')
            )
            execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Error saving business: {e}")
            return False
    
    def save_businesses_batch(self, businesses: List[Business]) -> int:
        """Save multiple businesses"""
        if not businesses:
            return 0
        
        saved_count = 0
        for business in businesses:
            if self.save_business(business):
                saved_count += 1
        
        return saved_count
    
    # Crawl job operations
    def create_crawl_job(self, road: Road) -> Optional[str]:
        """Create a new crawl job"""
        try:
            query = """
                INSERT INTO crawl_jobs (
                    road_osm_id, road_name, county_fips, state_code, status
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING job_id
            """
            result = execute_query(
                query, 
                (road.osm_id, road.name, road.county_fips, road.state_code, 'pending'),
                fetch_one=True
            )
            return str(result['job_id']) if result else None
        except Exception as e:
            logger.error(f"Error creating crawl job: {e}")
            return None
    
    def update_crawl_job(self, job_id: str, status: str, businesses_found: int = 0, error: str = None):
        """Update crawl job status"""
        try:
            update_parts = ["status = %s", "businesses_found = %s"]
            params = [status, businesses_found]
            
            if status == 'processing':
                update_parts.append("started_at = NOW()")
            elif status in ['completed', 'failed']:
                update_parts.append("completed_at = NOW()")
                if error:
                    update_parts.append("error_message = %s")
                    params.append(error)
            
            params.append(int(job_id))
            
            query = f"UPDATE crawl_jobs SET {', '.join(update_parts)} WHERE job_id = %s"
            execute_query(query, params)
        except Exception as e:
            logger.error(f"Error updating crawl job: {e}")
    
    def get_unique_road_names(self, limit: int = 100, state_code: str = None, county_fips: str = None, city_name: str = None) -> List[Dict]:
        """Get unique road names from OSM data ordered by business potential"""
        try:
            # If city_name is provided, filter by city
            if city_name and state_code:
                query = """
                    SELECT 
                        r.osm_id,
                        r.name,
                        r.highway,
                        r.county_fips,
                        rcm.state_code,
                        rcm.city_name as city_names,
                        COUNT(*) OVER (PARTITION BY r.name, r.county_fips) as segment_count,
                        ST_Length(r.geometry::geography) / 1000 as total_length_km,
                        ST_Y(ST_Centroid(r.geometry)) as center_lat,
                        ST_X(ST_Centroid(r.geometry)) as center_lon,
                        CASE 
                            WHEN r.highway IN ('primary', 'secondary', 'tertiary') THEN 80
                            WHEN r.highway IN ('residential', 'living_street') THEN 60
                            WHEN r.highway IN ('unclassified', 'service') THEN 40
                            ELSE 20
                        END as business_potential_score,
                        CASE 
                            WHEN r.highway IN ('primary', 'secondary', 'tertiary') THEN 'major'
                            WHEN r.highway IN ('residential', 'living_street') THEN 'local'
                            ELSE 'other'
                        END as business_category
                    FROM osm_roads_main r
                    INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
                    WHERE rcm.city_name = %s AND rcm.state_code = %s
                        AND r.name IS NOT NULL
                    ORDER BY business_potential_score DESC, r.name
                    LIMIT %s
                """
                params = [city_name, state_code, limit]
                results = execute_query(query, params)
            else:
                # Original logic for state/county filtering
                query = "SELECT * FROM get_top_business_roads(%s, %s, %s)"
                params = [state_code, county_fips, limit]
                results = execute_query(query, params)
            
            # Map fields to match frontend expectations
            formatted_results = []
            for row in results:
                city_names = row.get('city_names', '')
                formatted_results.append({
                    'osm_id': row['osm_id'],
                    'name': row['name'],
                    'highway': row['highway'],
                    'road_category': row['business_category'],
                    'county_fips': row['county_fips'],
                    'state_code': row['state_code'],
                    'segment_count': row['segment_count'],
                    'total_length_km': float(row['total_length_km']) if row['total_length_km'] else 0,
                    'center_lat': row['center_lat'],
                    'center_lon': row['center_lon'],
                    'business_potential_score': row['business_potential_score'],
                    'estimated_city': city_names,
                    'city_names': city_names,  # Include full city list
                    'display_name': f"{row['name']} ({city_names})" if city_names else row['name'],
                    'feature_class': row['highway'],  # Use highway type as feature class
                    'business_likelihood': 'high' if row['business_potential_score'] >= 70 else 'medium' if row['business_potential_score'] >= 40 else 'low'
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error fetching unique road names: {e}")
            return []
    
    # County operations
    def get_counties_by_state(self, state_code: str) -> List[Dict]:
        """Get all counties for a specific state"""
        try:
            query = """
                SELECT county_fips, county_name 
                FROM counties 
                WHERE state_code = %s 
                ORDER BY county_name
            """
            return execute_query(query, (state_code,))
        except Exception as e:
            logger.error(f"Error fetching counties: {e}")
            return []
    
    def get_states_summary(self) -> Dict:
        """Get summary of all states"""
        try:
            # Get states
            states_query = """
                SELECT state_code, state_name, total_roads 
                FROM states 
                ORDER BY state_name
            """
            states = execute_query(states_query)
            
            # Get county counts
            county_query = """
                SELECT state_code, COUNT(*) as county_count 
                FROM counties 
                GROUP BY state_code
            """
            county_counts = {row['state_code']: row['county_count'] 
                           for row in execute_query(county_query)}
            
            # Combine data
            for state in states:
                state['county_count'] = county_counts.get(state['state_code'], 0)
            
            return {
                'states': states,
                'total_states': len(states),
                'total_counties': sum(county_counts.values())
            }
        except Exception as e:
            logger.error(f"Error fetching states summary: {e}")
            return {'states': [], 'total_states': 0, 'total_counties': 0}
    
    # Crawl Status Operations
    def get_crawl_status(self, state_code: str = None, county_fips: str = None, keyword: str = None) -> List[Dict]:
        """Get crawl status for roads"""
        try:
            query = "SELECT * FROM crawl_status WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND keyword = %s"
                params.append(keyword)
            
            if state_code or county_fips:
                road_query = "SELECT osm_id FROM osm_roads_main WHERE 1=1"
                road_params = []
                
                if state_code:
                    road_query += " AND state_code = %s"
                    road_params.append(state_code)
                if county_fips:
                    road_query += " AND county_fips = %s"
                    road_params.append(county_fips)
                
                road_ids = [r['osm_id'] for r in execute_query(road_query, road_params)]
                if road_ids:
                    placeholders = ','.join(['%s'] * len(road_ids))
                    query += f" AND road_osm_id IN ({placeholders})"
                    params.extend(road_ids)
            
            return execute_query(query, params if params else None)
        except Exception as e:
            logger.error(f"Error fetching crawl status: {e}")
            return []
    
    def update_crawl_status(self, road_osm_id: str, keyword: str, status: str, 
                           businesses_found: int = 0, error_message: str = None) -> bool:
        """Update or create crawl status for a road-keyword combination"""
        try:
            query = """
                INSERT INTO crawl_status (
                    road_osm_id, keyword, status, businesses_found, error_message
                ) VALUES (%s::bigint, %s, %s, %s, %s)
                ON CONFLICT (road_osm_id, keyword) DO UPDATE SET
                    status = EXCLUDED.status,
                    businesses_found = EXCLUDED.businesses_found,
                    error_message = EXCLUDED.error_message,
                    updated_at = NOW()
            """
            execute_query(query, (road_osm_id, keyword, status, businesses_found, error_message))
            return True
        except Exception as e:
            logger.error(f"Error updating crawl status: {e}")
            return False
    
    
    # Statistics
    def get_crawl_stats(self) -> Dict:
        """Get crawling statistics"""
        try:
            stats = {}
            
            # Roads processed - count unique roads crawled from crawl_sessions
            try:
                query = "SELECT COUNT(DISTINCT road_osm_id) as count FROM crawl_sessions WHERE status = 'completed'"
                result = execute_query(query, fetch_one=True)
                stats['roads_processed'] = result['count'] if result else 0
            except Exception as e:
                logger.error(f"Error getting roads processed: {e}")
                stats['roads_processed'] = 0
            
            # Total businesses from crawl sessions
            try:
                query = """
                    SELECT 
                        SUM(businesses_found) as total_businesses,
                        COUNT(DISTINCT road_osm_id) as roads_with_businesses
                    FROM crawl_sessions 
                    WHERE status = 'completed' AND businesses_found > 0
                """
                result = execute_query(query, fetch_one=True)
                stats['businesses_found'] = int(result['total_businesses']) if result and result['total_businesses'] else 0
            except Exception as e:
                logger.error(f"Error getting businesses found: {e}")
                # Fallback to businesses table count
                try:
                    query = "SELECT COUNT(*) as count FROM businesses"
                    result = execute_query(query, fetch_one=True)
                    stats['businesses_found'] = result['count'] if result else 0
                except:
                    stats['businesses_found'] = 0
            
            stats['avg_businesses_per_road'] = (
                stats['businesses_found'] / stats['roads_processed'] 
                if stats['roads_processed'] > 0 else 0
            )
            
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def initialize_api_tracking(self):
        """Create API tracking table if it doesn't exist"""
        try:
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
            
            # Create indexes
            execute_query("CREATE INDEX IF NOT EXISTS idx_api_calls_created_at ON api_calls(created_at)")
            execute_query("CREATE INDEX IF NOT EXISTS idx_api_calls_api_type ON api_calls(api_type)")
            
            logger.info("API tracking table initialized")
        except Exception as e:
            logger.error(f"Error initializing API tracking: {e}")

# Create a default instance
postgres_client = PostgresClient()

# Initialize API tracking on startup
postgres_client.initialize_api_tracking()

# Export execute_query for direct use
from scripts.database_config import execute_query
__all__ = ['PostgresClient', 'postgres_client', 'execute_query']