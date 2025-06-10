"""
Business location analyzer using advanced scoring system
"""
import logging
from typing import Dict, Tuple, Optional
from ..database.postgres_client import PostgresClient

logger = logging.getLogger(__name__)

class BusinessAnalyzer:
    def __init__(self, db_client: PostgresClient):
        self.db = db_client
    
    def analyze_location(self, lat: float, lon: float, radius_km: float = 0.5) -> Dict:
        """
        Analyze a business location using the advanced scoring system
        
        Returns comprehensive analysis including:
        - Score (0-100)
        - Rating (Excellent/Very Good/Good/Fair/Poor/Very Poor)
        - Recommendation
        - Best business types for the location
        - Potential challenges
        - Detailed area metrics
        """
        try:
            query = """
                SELECT calculate_business_score_advanced(%s, %s, %s) as analysis
            """
            
            from scripts.database_config import execute_query
            result = execute_query(
                query, 
                (lat, lon, radius_km),
                fetch_one=True
            )
            
            if result and result['analysis']:
                return result['analysis']
            
            return self._get_default_analysis()
            
        except Exception as e:
            logger.error(f"Error analyzing location ({lat}, {lon}): {e}")
            return self._get_default_analysis()
    
    def get_area_classification(self, lat: float, lon: float, radius_km: float = 0.5) -> Dict:
        """
        Get simple area classification
        """
        try:
            query = """
                SELECT classify_area_type(%s, %s, %s) as classification
            """
            
            from scripts.database_config import execute_query
            result = execute_query(
                query,
                (lat, lon, radius_km),
                fetch_one=True
            )
            
            if result and result['classification']:
                return result['classification']
                
            return {
                'area_type': 'unknown',
                'business_suitability': 'unknown',
                'description': 'Unable to classify area'
            }
            
        except Exception as e:
            logger.error(f"Error classifying area ({lat}, {lon}): {e}")
            return {
                'area_type': 'unknown',
                'business_suitability': 'unknown',
                'description': 'Error classifying area'
            }
    
    def format_analysis_summary(self, analysis: Dict) -> str:
        """
        Format analysis results into a human-readable summary
        """
        if not analysis:
            return "No analysis available"
        
        score = analysis.get('score', 0)
        rating = analysis.get('rating', 'Unknown')
        recommendation = analysis.get('recommendation', '')
        
        # Get best business types
        best_for = analysis.get('business_insights', {}).get('best_for', [])
        challenges = analysis.get('business_insights', {}).get('challenges', [])
        
        # Get key metrics
        area_analysis = analysis.get('area_analysis', {})
        road_density = area_analysis.get('basic_metrics', {}).get('road_density_per_sqkm', 0)
        nearest_major = area_analysis.get('accessibility', {}).get('nearest_major_road_m', 0)
        
        summary = f"""
Business Potential Analysis:
Score: {score}/100 ({rating})
{recommendation}

Best suited for: {', '.join(best_for) if best_for else 'General businesses'}
{f"Challenges: {', '.join(challenges)}" if challenges else ""}

Key metrics:
- Road density: {road_density} roads/km²
- Nearest major road: {nearest_major}m
"""
        return summary.strip()
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis when scoring fails"""
        return {
            'score': 0,
            'rating': 'Unknown',
            'recommendation': 'Unable to analyze location',
            'score_breakdown': {
                'density_score': 0,
                'accessibility_score': 0,
                'road_quality_score': 0,
                'area_type_score': 0,
                'traffic_score': 0
            },
            'business_insights': {
                'best_for': ['unknown'],
                'challenges': ['Analysis unavailable']
            }
        }
    
    def should_crawl_location(self, lat: float, lon: float, min_score: int = 30) -> bool:
        """
        Determine if a location is worth crawling based on business potential
        
        Args:
            lat: Latitude
            lon: Longitude  
            min_score: Minimum score threshold (default 30)
            
        Returns:
            True if location has sufficient business potential
        """
        analysis = self.analyze_location(lat, lon)
        score = analysis.get('score', 0)
        
        if score < min_score:
            logger.info(f"Skipping location ({lat}, {lon}) - low business potential: {score}")
            return False
            
        return True
    
    def get_recommended_search_radius(self, area_type: str) -> int:
        """
        Get recommended search radius based on area type
        
        Returns radius in meters
        """
        radius_map = {
            'rural': 2000,  # Search wider in rural areas
            'suburban_residential': 1000,
            'suburban_mixed': 500,
            'suburban_general': 500,
            'urban_mixed': 300,
            'urban_commercial': 200  # Dense areas need smaller radius
        }
        
        return radius_map.get(area_type, 500)