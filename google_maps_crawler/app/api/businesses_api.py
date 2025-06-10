"""
API endpoints for business data management
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import csv
import json
import io
from datetime import datetime
from ..database.postgres_client import execute_query, get_connection

router = APIRouter(prefix="/api/businesses", tags=["businesses"])

@router.get("")
async def get_businesses(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    city: Optional[str] = None,
    road: Optional[str] = None,
    type: Optional[str] = None,
    rating: float = Query(0, ge=0, le=5),
    hasPhone: bool = False
):
    """Get paginated list of businesses with filters"""
    offset = (page - 1) * limit
    
    # Build WHERE conditions
    conditions = []
    params = []
    param_count = 0
    
    if city:
        param_count += 1
        conditions.append(f"b.city ILIKE %s")
        params.append(f"%{city}%")
    
    if road:
        param_count += 1
        conditions.append(f"r.name ILIKE %s")
        params.append(f"%{road}%")
    
    if type:
        param_count += 1
        conditions.append(f"%s = ANY(b.types)")
        params.append(type)
    
    if rating > 0:
        param_count += 1
        conditions.append(f"b.rating >= %s")
        params.append(rating)
    
    if hasPhone:
        conditions.append("b.phone_number IS NOT NULL")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Get businesses
    query = f"""
        SELECT 
            b.place_id,
            b.name,
            b.formatted_address,
            b.lat,
            b.lng,
            b.types,
            b.rating,
            b.user_ratings_total,
            b.phone_number,
            b.website,
            b.crawled_at,
            r.name as road_name,
            b.city
        FROM businesses b
        LEFT JOIN osm_roads_main r ON b.road_osm_id = r.osm_id
        {where_clause}
        ORDER BY b.crawled_at DESC
        LIMIT %s OFFSET %s
    """
    
    businesses = execute_query(query, params + [limit, offset])
    
    # Get stats
    stats_query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT(b.phone_number) as with_phone,
            COUNT(b.website) as with_website,
            AVG(b.rating) as avg_rating
        FROM businesses b
        LEFT JOIN osm_roads_main r ON b.road_osm_id = r.osm_id
        {where_clause}
    """
    
    stats = execute_query(stats_query, params, fetch_one=True)
    
    return {
        "businesses": businesses,
        "total": stats['total'] if stats else 0,
        "page": page,
        "limit": limit,
        "stats": {
            "total": stats['total'] if stats else 0,
            "withPhone": stats['with_phone'] if stats else 0,
            "withWebsite": stats['with_website'] if stats else 0,
            "avgRating": float(stats['avg_rating']) if stats and stats['avg_rating'] else 0
        }
    }

@router.get("/export")
async def export_businesses(
    format: str = Query("csv", regex="^(csv|json)$"),
    city: Optional[str] = None,
    road: Optional[str] = None,
    type: Optional[str] = None,
    rating: float = Query(0, ge=0, le=5),
    hasPhone: bool = False
):
    """Export businesses to CSV or JSON"""
    # Build WHERE conditions (same as above)
    conditions = []
    params = []
    
    if city:
        conditions.append(f"b.city ILIKE %s")
        params.append(f"%{city}%")
    
    if road:
        conditions.append(f"r.name ILIKE %s")
        params.append(f"%{road}%")
    
    if type:
        conditions.append(f"%s = ANY(b.types)")
        params.append(type)
    
    if rating > 0:
        conditions.append(f"b.rating >= %s")
        params.append(rating)
    
    if hasPhone:
        conditions.append("b.phone_number IS NOT NULL")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Get all businesses (no pagination for export)
    query = f"""
        SELECT 
            b.place_id,
            b.name,
            b.formatted_address,
            b.phone_number,
            b.website,
            b.rating,
            b.user_ratings_total,
            b.types[1] as primary_type,
            r.name as road_name,
            b.city,
            b.crawled_at
        FROM businesses b
        LEFT JOIN osm_roads_main r ON b.road_osm_id = r.osm_id
        {where_clause}
        ORDER BY b.crawled_at DESC
    """
    
    businesses = execute_query(query, params)
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'place_id', 'name', 'formatted_address', 'phone_number', 
            'website', 'rating', 'user_ratings_total', 'primary_type',
            'road_name', 'city', 'crawled_at'
        ])
        writer.writeheader()
        writer.writerows(businesses)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=businesses_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    else:
        # Return JSON
        return StreamingResponse(
            io.BytesIO(json.dumps(businesses, indent=2, default=str).encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=businesses_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )

@router.delete("/{place_id}")
async def delete_business(place_id: str):
    """Delete a business by place_id"""
    try:
        result = execute_query(
            "DELETE FROM businesses WHERE place_id = %s RETURNING place_id",
            (place_id,),
            fetch_one=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return {"message": "Business deleted successfully", "place_id": place_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/by-city")
async def get_stats_by_city():
    """Get business statistics grouped by city"""
    stats = execute_query("""
        SELECT 
            city,
            COUNT(*) as total,
            COUNT(phone_number) as with_phone,
            COUNT(website) as with_website,
            AVG(rating) as avg_rating,
            COUNT(DISTINCT road_osm_id) as roads_crawled
        FROM businesses
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY total DESC
        LIMIT 20
    """)
    
    return {"cities": stats}

@router.get("/stats/by-type")
async def get_stats_by_type():
    """Get business statistics grouped by type"""
    stats = execute_query("""
        SELECT 
            unnest(types) as business_type,
            COUNT(*) as count
        FROM businesses
        GROUP BY business_type
        ORDER BY count DESC
        LIMIT 20
    """)
    
    return {"types": stats}