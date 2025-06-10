"""
Enhanced roads API with POI statistics
"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

@router.get("/api/roads/search-with-stats")
async def search_roads_with_poi_stats(
    db,
    state_code: Optional[str] = None,
    county_fips: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100)
):
    """
    Search roads with POI statistics included
    """
    
    # Build query
    query = """
        WITH road_poi_stats AS (
            SELECT 
                r.osm_id,
                r.name,
                r.state_code,
                r.county_fips,
                COUNT(b.osm_id) as poi_count,
                COUNT(b.phone) as poi_with_phone,
                COUNT(b.website) as poi_with_website,
                COUNT(b.opening_hours) as poi_with_hours,
                COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL) as brand_count,
                STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
                    FILTER (WHERE b.brand IS NOT NULL) as top_brands
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
        )
        SELECT 
            osm_id,
            name,
            state_code,
            county_fips,
            poi_count,
            poi_with_phone,
            poi_with_website,
            poi_with_hours,
            brand_count,
            CASE 
                WHEN LENGTH(top_brands) > 50 
                THEN SUBSTRING(top_brands, 1, 47) || '...'
                ELSE top_brands
            END as top_brands,
            CASE
                WHEN poi_count = 0 THEN 'No Data'
                WHEN poi_with_phone::float / NULLIF(poi_count, 0) > 0.7 THEN 'Good'
                WHEN poi_with_phone::float / NULLIF(poi_count, 0) > 0.3 THEN 'Fair'
                ELSE 'Poor'
            END as data_quality
        FROM road_poi_stats
        ORDER BY 
            CASE WHEN poi_count > 0 THEN 0 ELSE 1 END,
            poi_count DESC,
            name
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
                    "count": road["poi_count"],
                    "with_phone": road["poi_with_phone"],
                    "with_website": road["poi_with_website"],
                    "with_hours": road["poi_with_hours"],
                    "brands": road["brand_count"],
                    "top_brands": road["top_brands"],
                    "quality": road["data_quality"],
                    "phone_coverage": f"{road['poi_with_phone']/road['poi_count']*100:.0f}%" 
                        if road['poi_count'] > 0 else "N/A"
                }
            }
            for road in roads
        ],
        "total": len(roads)
    }