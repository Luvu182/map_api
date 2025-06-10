"""
Tier optimization strategies for Google Maps API
Helps decide which tier to use based on business potential
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TierOptimizer:
    """
    Optimize API tier selection based on road characteristics
    Goal: Maximize data while minimizing costs
    """
    
    def __init__(self, db_client):
        self.db = db_client
        
    def get_optimal_tier(self, road_osm_id: int) -> Dict[str, any]:
        """
        Determine optimal tier based on road's business potential
        
        Returns:
            Dict with 'tier' and 'strategy' keys
        """
        # Get road business stats from OSM POI data
        stats = self.db.execute_query("""
            SELECT 
                poi_count,
                poi_density,
                business_potential_score
            FROM road_business_stats
            WHERE road_osm_id = %s
        """, (road_osm_id,), fetch_one=True)
        
        if not stats:
            # No POI data - use minimal tier
            return {
                'tier': 'enterprise_minimal',
                'strategy': 'discovery',
                'reason': 'No POI data available'
            }
        
        poi_count = stats.get('poi_count', 0)
        score = stats.get('business_potential_score', 0)
        
        # Decision logic
        if score >= 8 or poi_count >= 20:
            # High potential - get all data
            return {
                'tier': 'enterprise',
                'strategy': 'comprehensive',
                'reason': f'High potential (score: {score}, POIs: {poi_count})'
            }
        elif score >= 5 or poi_count >= 10:
            # Medium potential - get standard data
            return {
                'tier': 'pro',
                'strategy': 'standard',
                'reason': f'Medium potential (score: {score}, POIs: {poi_count})'
            }
        else:
            # Low potential - minimal data
            return {
                'tier': 'enterprise_minimal',
                'strategy': 'discovery',
                'reason': f'Low potential (score: {score}, POIs: {poi_count})'
            }
    
    def should_crawl_road(self, road_osm_id: int) -> bool:
        """
        Determine if road is worth crawling based on POI data
        """
        stats = self.db.execute_query("""
            SELECT poi_count, business_potential_score
            FROM road_business_stats
            WHERE road_osm_id = %s
        """, (road_osm_id,), fetch_one=True)
        
        if not stats:
            return False
            
        # Skip roads with very low potential
        return stats.get('poi_count', 0) > 0 or stats.get('business_potential_score', 0) >= 3
    
    def get_priority_roads(self, city_name: str, limit: int = 100) -> list:
        """
        Get roads prioritized by business potential
        """
        return self.db.execute_query("""
            SELECT 
                r.osm_id,
                r.name as road_name,
                rbs.poi_count,
                rbs.business_potential_score,
                rbs.dominant_business_types
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            JOIN road_business_stats rbs ON r.osm_id = rbs.road_osm_id
            WHERE rcm.city_name = %s
            AND rbs.poi_count > 0
            ORDER BY rbs.business_potential_score DESC, rbs.poi_count DESC
            LIMIT %s
        """, (city_name, limit))