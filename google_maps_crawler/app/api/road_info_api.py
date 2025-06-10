"""
Simple API to show POI info for roads
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/api/roads/{road_id}/poi-info")
async def get_road_poi_info(road_id: int, db):
    """
    Get POI statistics for a road - just for display
    """
    
    # Get road basic info
    road = await db.fetch_one("""
        SELECT osm_id, name, state_code
        FROM osm_roads_main
        WHERE osm_id = :road_id
    """, {"road_id": road_id})
    
    if not road:
        raise HTTPException(404, "Road not found")
    
    # Get POI stats
    stats = await db.fetch_one("""
        SELECT 
            COUNT(*) as total_pois,
            COUNT(phone) as with_phone,
            COUNT(website) as with_website,
            COUNT(opening_hours) as with_hours,
            COUNT(DISTINCT brand) FILTER (WHERE brand IS NOT NULL) as brands
        FROM osm_businesses
        WHERE nearest_road_id = :road_id
    """, {"road_id": road_id})
    
    # Get top businesses
    top_businesses = await db.fetch_all("""
        SELECT name, brand, business_subtype,
               CASE WHEN phone IS NOT NULL THEN 'Yes' ELSE 'No' END as has_phone,
               CASE WHEN opening_hours IS NOT NULL THEN 'Yes' ELSE 'No' END as has_hours
        FROM osm_businesses
        WHERE nearest_road_id = :road_id
        ORDER BY business_score DESC
        LIMIT 10
    """, {"road_id": road_id})
    
    return {
        "road": {
            "id": road["osm_id"],
            "name": road["name"],
            "state": road["state_code"]
        },
        "poi_stats": {
            "total": stats["total_pois"],
            "with_phone": stats["with_phone"],
            "with_website": stats["with_website"],
            "with_hours": stats["with_hours"],
            "unique_brands": stats["brands"],
            "phone_coverage": f"{stats['with_phone']/stats['total_pois']*100:.0f}%" if stats['total_pois'] > 0 else "0%",
            "data_quality": "Good" if stats['with_phone']/stats['total_pois'] > 0.7 else "Needs Update" if stats['total_pois'] > 0 else "No Data"
        },
        "top_businesses": [
            {
                "name": b["name"],
                "brand": b["brand"],
                "type": b["business_subtype"],
                "has_phone": b["has_phone"],
                "has_hours": b["has_hours"]
            }
            for b in top_businesses
        ]
    }