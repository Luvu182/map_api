"""
Simplified Roads API - no spatial calculations
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging
from ..database.postgres_client import execute_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roads", tags=["roads"])

@router.get("/search")
async def search_roads(
    search: str = Query(..., description="Search term"),
    state_code: Optional[str] = Query(None, description="State code filter"),
    limit: int = Query(20, description="Maximum results")
):
    """Simple road search without spatial calculations"""
    try:
        # Use materialized view for better performance
        query = """
            SELECT DISTINCT ON (road_name, city_name, state_code)
                osm_id,
                road_name as name,
                highway,
                ref,
                city_name,
                state_code,
                county_fips
            FROM city_roads_simple
            WHERE road_name ILIKE %s
        """
        params = [f"%{search}%"]
        
        if state_code:
            query += " AND state_code = %s"
            params.append(state_code)
            
        query += " ORDER BY road_name, city_name, state_code LIMIT %s"
        params.append(limit)
        
        results = execute_query(query, params)
        
        return {
            "roads": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching roads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-city-simple")
async def get_roads_by_city_simple(
    city_name: str = Query(..., description="City name"),
    state_code: str = Query(..., description="State code"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Offset")
):
    """Get roads for a city without spatial calculations"""
    try:
        # Use materialized view for fast performance
        query = """
            SELECT DISTINCT ON (road_name)
                osm_id,
                road_name as name,
                highway,
                ref,
                city_name,
                state_code
            FROM city_roads_simple
            WHERE city_name = %s 
                AND state_code = %s
            ORDER BY road_name, osm_id
            LIMIT %s OFFSET %s
        """
        
        results = execute_query(query, [city_name, state_code, limit, offset])
        
        # Get total count from materialized view
        count_query = """
            SELECT COUNT(DISTINCT road_name) as total
            FROM city_roads_simple
            WHERE city_name = %s 
                AND state_code = %s
        """
        
        count_result = execute_query(count_query, [city_name, state_code], fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        return {
            "roads": results,
            "total": total,
            "city": city_name,
            "state": state_code
        }
        
    except Exception as e:
        logger.error(f"Error fetching roads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/states")
async def get_states_with_roads():
    """Get all states that have roads"""
    try:
        query = """
            SELECT DISTINCT state_code, COUNT(*) as road_count
            FROM osm_roads_main
            WHERE state_code IS NOT NULL
            GROUP BY state_code
            ORDER BY state_code
        """
        
        results = execute_query(query)
        
        return {
            "states": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error fetching states: {e}")
        raise HTTPException(status_code=500, detail=str(e))