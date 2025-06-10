"""
Simple roads API with basic POI counts
"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

@router.get("/api/roads")
async def get_roads(
    db,
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100)
):
    """
    Get roads with simple business count
    """
    
    # Build query - simple join to get POI count
    query = """
        SELECT 
            r.osm_id,
            r.name,
            r.state_code,
            r.county_fips,
            COUNT(b.osm_id) as business_count,
            STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
                FILTER (WHERE b.brand IS NOT NULL) as brands
        FROM osm_roads_main r
        LEFT JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
        WHERE 1=1
    """
    
    params = {}
    
    if state_code:
        query += " AND r.state_code = :state_code"
        params["state_code"] = state_code
        
    if county_fips:
        query += " AND r.county_fips = :county_fips"
        params["county_fips"] = county_fips
        
    if search:
        query += " AND r.name ILIKE :search"
        params["search"] = f"%{search}%"
        
    query += """
        GROUP BY r.osm_id, r.name, r.state_code, r.county_fips
        ORDER BY 
            CASE WHEN COUNT(b.osm_id) > 0 THEN 0 ELSE 1 END,
            COUNT(b.osm_id) DESC,
            r.name
        LIMIT :limit
    """
    
    params["limit"] = limit
    
    roads = await db.fetch_all(query, params)
    
    return {
        "roads": [
            {
                "id": road["osm_id"],
                "name": road["name"],
                "state_code": road["state_code"],
                "county_fips": road["county_fips"],
                "poi_stats": {
                    "count": road["business_count"],
                    "top_brands": road["brands"][:100] if road["brands"] else None
                } if road["business_count"] > 0 else None
            }
            for road in roads
        ]
    }