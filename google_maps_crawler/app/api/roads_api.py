"""
Roads API endpoints for frontend
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict
import logging
from ..database.postgres_client import postgres_client, execute_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roads", tags=["roads"])

@router.get("/by-city")
async def get_roads_by_city(
    city_name: str = Query(..., description="City name"),
    state_code: str = Query(..., description="State code (2 letters)"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination"),
    highway_type: Optional[str] = Query(None, description="Filter by highway type")
):
    """Get roads for a specific target city"""
    try:
        # Use materialized view for much faster performance
        query = """
            WITH road_aggregates AS (
                SELECT 
                    road_name,
                    MIN(osm_id) as osm_id,
                    STRING_AGG(DISTINCT highway, ', ') as highway_types,
                    -- Get most common highway type
                    (SELECT highway FROM city_roads_simple r2 
                     WHERE r2.road_name = r.road_name 
                     AND r2.city_name = r.city_name
                     GROUP BY highway 
                     ORDER BY COUNT(*) DESC 
                     LIMIT 1) as highway,
                    STRING_AGG(DISTINCT ref, ', ') as ref,
                    COUNT(*) as segment_count,
                    SUM(COALESCE(
                        CASE 
                            WHEN highway IN ('primary', 'secondary') THEN 80
                            WHEN highway = 'tertiary' THEN 70
                            WHEN highway IN ('residential', 'unclassified') THEN 60
                            WHEN highway = 'living_street' THEN 50
                            WHEN highway IN ('motorway', 'trunk') THEN 30
                            ELSE 20
                        END, 20
                    )) / COUNT(*) as business_potential_score
                FROM city_roads_simple r
                WHERE r.city_name = %s AND r.state_code = %s
                    AND r.road_name IS NOT NULL
        """
        params = [city_name, state_code]
        
        if highway_type:
            query += " AND r.highway = %s"
            params.append(highway_type)
            
        query += """
                GROUP BY road_name, city_name
            )
            SELECT 
                ra.osm_id,
                ra.road_name,
                ra.highway,
                ra.highway_types,
                ra.ref,
                %s as city_name,
                %s as state_code,
                ra.segment_count,
                ra.business_potential_score,
                COALESCE(poi.poi_count, 0) as poi_count,
                cs.last_crawl_info
            FROM road_aggregates ra
            LEFT JOIN (
                SELECT nearest_road_id, COUNT(*) as poi_count
                FROM osm_businesses
                WHERE state_code = %s
                GROUP BY nearest_road_id
            ) poi ON ra.osm_id = poi.nearest_road_id
            LEFT JOIN LATERAL (
                SELECT json_build_object(
                    'last_crawled_at', MAX(started_at),
                    'total_crawls', COUNT(*),
                    'total_businesses', SUM(businesses_found),
                    'keywords_crawled', array_agg(DISTINCT keyword)
                ) as last_crawl_info
                FROM crawl_sessions
                WHERE road_osm_id = ra.osm_id
                AND status = 'completed'
            ) cs ON true
            ORDER BY 
                CASE 
                    WHEN highway IN ('primary', 'secondary', 'tertiary') THEN 1
                    WHEN highway IN ('residential', 'living_street') THEN 2
                    ELSE 3
                END,
                road_name
            LIMIT %s OFFSET %s
        """
        params.extend([city_name, state_code, state_code, limit, offset])
        
        results = execute_query(query, params)
        
        # Format results to match frontend expectations
        formatted_results = []
        for row in results:
            # Create display name with segment info
            segments_info = f" ({row['segment_count']} segments)" if row['segment_count'] > 1 else ""
            formatted_results.append({
                **row,
                'name': row['road_name'],  # Add 'name' field for frontend
                'display_name': f"{row['road_name']}{segments_info}",
                'total_segments': row['segment_count']
            })
        
        # Get total count of unique road names from materialized view
        count_query = """
            SELECT COUNT(DISTINCT road_name) as total
            FROM city_roads_simple
            WHERE city_name = %s AND state_code = %s
                AND road_name IS NOT NULL
        """
        count_params = [city_name, state_code]
        if highway_type:
            count_query += " AND highway = %s"
            count_params.append(highway_type)
            
        count_result = execute_query(count_query, count_params, fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        return {
            "roads": formatted_results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "city": city_name,
            "state": state_code
        }
        
    except Exception as e:
        logger.error(f"Error fetching roads by city: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/target-cities")
async def get_target_cities(
    state_code: Optional[str] = Query(None, description="Filter by state"),
    with_roads_only: bool = Query(True, description="Only show cities with mapped roads")
):
    """Get list of target cities with road counts"""
    try:
        query = """
            SELECT 
                tc.city_name,
                tc.state_code,
                COUNT(DISTINCT rcm.road_id) as road_count,
                COUNT(DISTINCT r.osm_id) as unique_roads
            FROM target_cities_346 tc
        """
        
        if with_roads_only:
            query += """
                INNER JOIN road_city_mapping rcm 
                    ON tc.city_name = rcm.city_name 
                    AND tc.state_code = rcm.state_code
                INNER JOIN osm_roads_main r ON rcm.road_id = r.id
            """
        else:
            query += """
                LEFT JOIN road_city_mapping rcm 
                    ON tc.city_name = rcm.city_name 
                    AND tc.state_code = rcm.state_code
                LEFT JOIN osm_roads_main r ON rcm.road_id = r.id
            """
        
        query += " WHERE 1=1"
        params = []
        
        if state_code:
            query += " AND tc.state_code = %s"
            params.append(state_code)
            
        query += """
            GROUP BY tc.city_name, tc.state_code
            ORDER BY road_count DESC, tc.city_name
        """
        
        results = execute_query(query, params)
        
        # Get summary stats
        total_cities = len(results)
        cities_with_roads = sum(1 for r in results if r['road_count'] > 0)
        
        return {
            "cities": results,
            "total_cities": total_cities,
            "cities_with_roads": cities_with_roads,
            "coverage_percentage": round((cities_with_roads / total_cities * 100) if total_cities > 0 else 0, 1)
        }
        
    except Exception as e:
        logger.error(f"Error fetching target cities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/city-stats")
async def get_city_stats(
    city_name: str = Query(..., description="City name"),
    state_code: str = Query(..., description="State code")
):
    """Get detailed statistics for a specific city"""
    try:
        # Get road statistics by type
        query = """
            SELECT 
                r.highway,
                COUNT(*) as count,
                SUM(ST_Length(r.geometry::geography)) / 1000 as total_length_km
            FROM osm_roads_main r
            INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.city_name = %s AND rcm.state_code = %s
            GROUP BY r.highway
            ORDER BY count DESC
        """
        
        road_stats = execute_query(query, [city_name, state_code])
        
        # Get overall stats
        total_query = """
            SELECT 
                COUNT(DISTINCT r.id) as total_roads,
                COUNT(DISTINCT r.osm_id) as unique_osm_ids,
                COUNT(DISTINCT CASE WHEN r.name IS NOT NULL THEN r.id END) as roads_with_names,
                SUM(ST_Length(r.geometry::geography)) / 1000 as total_length_km
            FROM osm_roads_main r
            INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.city_name = %s AND rcm.state_code = %s
        """
        
        totals = execute_query(total_query, [city_name, state_code], fetch_one=True)
        
        return {
            "city": city_name,
            "state": state_code,
            "totals": totals,
            "by_type": road_stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching city stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unprocessed")
async def get_unprocessed_roads_for_city(
    city_name: str = Query(..., description="City name (required)"),
    state_code: str = Query(..., description="State code (required)"),
    limit: int = Query(100, description="Maximum results"),
    keyword: Optional[str] = Query(None, description="Business keyword to check crawl status")
):
    """Get unprocessed roads for a specific city"""
    try:
        # Modified to use city-based filtering
        query = """
            SELECT 
                r.osm_id,
                r.name,
                r.highway,
                r.ref,
                r.county_fips,
                rcm.city_name,
                rcm.state_code,
                ST_Length(r.geometry::geography) / 1000 as total_length_km,
                ST_Y(ST_Centroid(r.geometry)) as center_lat,
                ST_X(ST_Centroid(r.geometry)) as center_lon,
                CASE 
                    WHEN r.highway IN ('primary', 'secondary', 'tertiary') THEN 80
                    WHEN r.highway IN ('residential', 'living_street') THEN 60
                    WHEN r.highway IN ('unclassified', 'service') THEN 40
                    ELSE 20
                END as business_potential_score
            FROM osm_roads_main r
            INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
            LEFT JOIN crawl_status cs ON r.osm_id = cs.road_osm_id AND cs.keyword = %s
            WHERE rcm.city_name = %s 
                AND rcm.state_code = %s 
                AND r.name IS NOT NULL
                AND (cs.status IS NULL OR cs.status = 'failed')
            ORDER BY business_potential_score DESC, r.name
            LIMIT %s
        """
        
        params = [keyword or 'restaurant', city_name, state_code, limit]
        results = execute_query(query, params)
        
        # Format results to match frontend expectations
        formatted_results = []
        for row in results:
            formatted_results.append({
                'osm_id': row['osm_id'],
                'name': row['name'],
                'highway': row['highway'],
                'ref': row.get('ref'),
                'county_fips': row['county_fips'],
                'state_code': row['state_code'],
                'city_name': row['city_name'],
                'total_length_km': float(row['total_length_km']) if row['total_length_km'] else 0,
                'center_lat': row['center_lat'],
                'center_lon': row['center_lon'],
                'business_potential_score': row['business_potential_score'],
                'display_name': f"{row['name']} ({row['city_name']})"
            })
        
        return {
            "roads": formatted_results,
            "city": city_name,
            "state": state_code,
            "total": len(results),
            "message": f"Found {len(results)} unprocessed roads in {city_name}, {state_code}"
        }
        
    except Exception as e:
        logger.error(f"Error fetching unprocessed roads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-with-coords")
async def search_roads_with_coordinates(
    q: str = Query(..., description="Search query for road name"),
    state_code: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(50, description="Maximum results")
):
    """Search roads by name with coordinates for map display"""
    try:
        # Normalize search query
        search_term = q.strip().lower()
        
        # Build query with coordinates
        query = """
            WITH road_matches AS (
                SELECT DISTINCT ON (r.osm_id)
                    r.osm_id,
                    r.name,
                    r.highway,
                    r.ref,
                    rcm.city_name,
                    rcm.state_code,
                    r.county_fips,
                    ST_Y(ST_Centroid(r.geometry)) as center_lat,
                    ST_X(ST_Centroid(r.geometry)) as center_lon,
                    ST_Length(r.geometry::geography) / 1000 as total_length_km,
                    COALESCE(poi.poi_count, 0) as poi_count,
                    CASE 
                        WHEN r.highway IN ('primary', 'secondary') THEN 80
                        WHEN r.highway = 'tertiary' THEN 70
                        WHEN r.highway IN ('residential', 'unclassified') THEN 60
                        WHEN r.highway = 'living_street' THEN 50
                        WHEN r.highway IN ('motorway', 'trunk') THEN 30
                        ELSE 20
                    END as business_potential_score
                FROM osm_roads_main r
                INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
                LEFT JOIN (
                    SELECT nearest_road_id, COUNT(*) as poi_count
                    FROM osm_businesses
                    GROUP BY nearest_road_id
                ) poi ON r.osm_id = poi.nearest_road_id
                WHERE r.name IS NOT NULL 
                    AND LOWER(r.name) LIKE %s
        """
        
        params = [f'%{search_term}%']
        
        if state_code:
            query += " AND rcm.state_code = %s"
            params.append(state_code)
            
        query += """
                ORDER BY r.osm_id, rcm.city_name
            )
            SELECT * FROM road_matches
            ORDER BY 
                CASE WHEN LOWER(name) = %s THEN 0 ELSE 1 END,
                poi_count DESC,
                business_potential_score DESC,
                name
            LIMIT %s
        """
        
        params.extend([search_term, limit])
        
        results = execute_query(query, params)
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                'osm_id': row['osm_id'],
                'name': row['name'],
                'highway': row['highway'],
                'ref': row.get('ref'),
                'city_name': row['city_name'],
                'state_code': row['state_code'],
                'county_fips': row['county_fips'],
                'center_lat': float(row['center_lat']) if row['center_lat'] else None,
                'center_lon': float(row['center_lon']) if row['center_lon'] else None,
                'total_length_km': float(row['total_length_km']) if row['total_length_km'] else 0,
                'poi_count': row['poi_count'],
                'business_potential_score': row['business_potential_score']
            })
        
        return {
            "query": q,
            "results": formatted_results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching roads with coordinates: {e}")
        raise HTTPException(status_code=500, detail=str(e))