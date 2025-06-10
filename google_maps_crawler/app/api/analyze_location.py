"""
API endpoint for location analysis
"""
from fastapi import APIRouter, Query, HTTPException
from ..crawler.business_analyzer import BusinessAnalyzer
from ..database.postgres_client import PostgresClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/analyze-location")
async def analyze_location(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(0.5, description="Radius in km")
):
    """
    Analyze business potential for a specific location
    
    Returns:
    - score: 0-100
    - rating: Excellent/Very Good/Good/Fair/Poor/Very Poor  
    - recommendation: Text recommendation
    - business_insights: Best business types and challenges
    - score_breakdown: Detailed scoring components
    """
    try:
        db = PostgresClient()
        analyzer = BusinessAnalyzer(db)
        
        # Get analysis
        analysis = analyzer.analyze_location(lat, lon, radius)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing location: {e}")
        raise HTTPException(status_code=500, detail=str(e))