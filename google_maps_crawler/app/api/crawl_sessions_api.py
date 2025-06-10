"""
API endpoints for crawl sessions
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from ..database.postgres_client import execute_query

router = APIRouter(prefix="/api/crawl-sessions", tags=["crawl-sessions"])

@router.get("/{session_id}")
async def get_session_details(session_id: str):
    """Get crawl session details with all businesses"""
    
    # Get session info
    session = execute_query(
        """
        SELECT 
            id,
            road_osm_id,
            road_name,
            city_name,
            state_code,
            keyword,
            status,
            businesses_found,
            started_at,
            completed_at,
            error_message,
            EXTRACT(EPOCH FROM (COALESCE(completed_at, CURRENT_TIMESTAMP) - started_at)) as duration_seconds
        FROM crawl_sessions
        WHERE id = %s
        """,
        (session_id,),
        fetch_one=True
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all businesses from this session (no pagination - show all 60)
    businesses = execute_query(
        """
        SELECT 
            place_id,
            name,
            formatted_address,
            lat,
            lng,
            types,
            rating,
            user_ratings_total,
            price_level,
            phone_number,
            website,
            opening_hours,
            distance_to_road,
            crawled_at
        FROM businesses
        WHERE crawl_session_id = %s
        ORDER BY rating DESC NULLS LAST, user_ratings_total DESC NULLS LAST
        """,
        (session_id,)
    )
    
    # Business stats for this session
    stats = execute_query(
        """
        SELECT 
            COUNT(*) as total,
            COUNT(phone_number) as with_phone,
            COUNT(website) as with_website,
            AVG(rating) as avg_rating,
            COUNT(DISTINCT types[1]) as unique_types
        FROM businesses
        WHERE crawl_session_id = %s
        """,
        (session_id,),
        fetch_one=True
    )
    
    return {
        "session": session,
        "businesses": businesses,
        "stats": stats
    }

@router.get("/")
async def get_recent_sessions(
    road_osm_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 20
):
    """Get recent crawl sessions"""
    
    conditions = []
    params = []
    
    if road_osm_id:
        conditions.append("road_osm_id = %s")
        params.append(road_osm_id)
    
    if status:
        conditions.append("status = %s")
        params.append(status)
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    sessions = execute_query(
        f"""
        SELECT 
            id,
            road_osm_id,
            road_name,
            city_name,
            state_code,
            keyword,
            status,
            businesses_found,
            started_at,
            completed_at,
            EXTRACT(EPOCH FROM (COALESCE(completed_at, CURRENT_TIMESTAMP) - started_at)) as duration_seconds
        FROM crawl_sessions
        {where_clause}
        ORDER BY started_at DESC
        LIMIT %s
        """,
        params + [limit]
    )
    
    return {"sessions": sessions}

@router.post("/{session_id}/export")
async def export_session_data(
    session_id: str,
    format: str = "csv"
):
    """Export businesses from a specific crawl session"""
    import csv
    import json
    import io
    from fastapi.responses import StreamingResponse
    from datetime import datetime
    
    # Verify session exists
    session = execute_query(
        "SELECT * FROM crawl_sessions WHERE id = %s",
        (session_id,),
        fetch_one=True
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get businesses
    businesses = execute_query(
        """
        SELECT 
            place_id,
            name,
            formatted_address,
            phone_number,
            website,
            rating,
            user_ratings_total,
            types[1] as primary_type,
            price_level,
            lat,
            lng
        FROM businesses
        WHERE crawl_session_id = %s
        ORDER BY rating DESC NULLS LAST
        """,
        (session_id,)
    )
    
    filename_base = f"{session['road_name']}_{session['city_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'place_id', 'name', 'formatted_address', 'phone_number',
            'website', 'rating', 'user_ratings_total', 'primary_type',
            'price_level', 'lat', 'lng'
        ])
        writer.writeheader()
        writer.writerows(businesses)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename_base}.csv"
            }
        )
    else:
        return StreamingResponse(
            io.BytesIO(json.dumps(businesses, indent=2, default=str).encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename_base}.json"
            }
        )