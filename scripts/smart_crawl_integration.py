#!/usr/bin/env python3
"""
Smart Google Maps Crawler Integration
Uses OSM POI data to intelligently prioritize crawling
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json

class SmartCrawlSelector:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        
    def get_high_priority_roads(self, state_code=None, limit=100):
        """Get roads with highest crawl priority"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            road_id,
            road_name,
            state_code,
            county_fips,
            total_businesses,
            chain_stores,
            missing_phone,
            missing_website,
            crawl_priority_score,
            ST_AsGeoJSON(r.geometry) as geometry_json
        FROM road_business_density rbd
        JOIN osm_roads_main r ON rbd.road_id = r.osm_id
        WHERE total_businesses >= 3
        """
        
        params = []
        if state_code:
            query += " AND rbd.state_code = %s"
            params.append(state_code)
            
        query += " ORDER BY crawl_priority_score DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        return cur.fetchall()
        
    def get_businesses_for_road(self, road_id):
        """Get all businesses along a specific road"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                osm_id,
                name,
                brand,
                business_type,
                business_subtype,
                phone,
                website,
                opening_hours,
                lat,
                lon,
                business_score
            FROM osm_businesses
            WHERE nearest_road_id = %s
            ORDER BY business_score DESC
        """, (road_id,))
        
        return cur.fetchall()
        
    def get_missing_data_businesses(self, state_code=None, limit=1000):
        """Get businesses missing critical data"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            osm_id,
            name,
            brand,
            business_type,
            business_subtype,
            city,
            state_code,
            lat,
            lon,
            nearest_road_name,
            crawl_priority
        FROM crawl_opportunities
        WHERE 1=1
        """
        
        params = []
        if state_code:
            query += " AND state_code = %s"
            params.append(state_code)
            
        query += " ORDER BY crawl_priority DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        return cur.fetchall()
        
    def get_brand_locations(self, brand_name):
        """Get all locations for a specific brand"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT * FROM get_brand_locations(%s)
        """, (brand_name,))
        
        return cur.fetchall()
        
    def get_business_clusters(self, min_density='medium_density'):
        """Get high-density business clusters"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        density_order = {
            'sparse': 0,
            'low_density': 1,
            'medium_density': 2,
            'high_density': 3
        }
        
        cur.execute("""
            SELECT 
                ST_X(ST_Centroid(cell_geom)) as center_lon,
                ST_Y(ST_Centroid(cell_geom)) as center_lat,
                business_count,
                unique_brands,
                shops,
                restaurants,
                density_class
            FROM business_cluster_grid
            WHERE density_class = ANY(%s)
            ORDER BY business_count DESC
        """, ([k for k, v in density_order.items() if v >= density_order[min_density]],))
        
        return cur.fetchall()
        
    def should_crawl_location(self, lat, lon, radius_m=500):
        """Check if a location is worth crawling based on POI density"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT * FROM calculate_business_density(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                %s
            )
        """, (lon, lat, radius_m))
        
        result = cur.fetchone()
        
        # Decision logic
        if result['total_businesses'] == 0:
            return False, "No businesses in area"
        elif result['total_businesses'] < 3:
            return False, "Too few businesses"
        elif result['recently_verified'] > result['total_businesses'] * 0.8:
            return False, "Recently verified area"
        elif result['with_hours_pct'] > 90:
            return False, "Well-documented area"
        else:
            return True, f"Good candidate: {result['total_businesses']} businesses"
            
    def get_crawl_strategy(self, state_code):
        """Get recommended crawl strategy for a state"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get state overview
        cur.execute("""
            SELECT 
                COUNT(*) as total_businesses,
                COUNT(DISTINCT brand) as unique_brands,
                AVG(phone IS NULL::int) * 100 as missing_phone_pct,
                AVG(website IS NULL::int) * 100 as missing_website_pct,
                AVG(opening_hours IS NULL::int) * 100 as missing_hours_pct
            FROM osm_businesses
            WHERE state_code = %s
        """, (state_code,))
        
        stats = cur.fetchone()
        
        # Get top missing brands
        cur.execute("""
            SELECT 
                brand,
                total_locations,
                phone_coverage_pct,
                website_coverage_pct
            FROM brand_presence
            WHERE %s = ANY(states_list)
            AND (phone_coverage_pct < 50 OR website_coverage_pct < 50)
            ORDER BY total_locations DESC
            LIMIT 10
        """, (state_code,))
        
        brands_to_update = cur.fetchall()
        
        strategy = {
            'state_code': state_code,
            'total_businesses': stats['total_businesses'],
            'data_quality': {
                'missing_phone_pct': round(stats['missing_phone_pct'], 1),
                'missing_website_pct': round(stats['missing_website_pct'], 1),
                'missing_hours_pct': round(stats['missing_hours_pct'], 1)
            },
            'priority': 'high' if stats['missing_phone_pct'] > 50 else 'medium',
            'brands_to_update': brands_to_update,
            'recommended_approach': []
        }
        
        # Recommendations
        if stats['missing_phone_pct'] > 70:
            strategy['recommended_approach'].append("Focus on phone number collection")
        if len(brands_to_update) > 5:
            strategy['recommended_approach'].append("Prioritize chain store updates")
        if stats['total_businesses'] > 10000:
            strategy['recommended_approach'].append("Use high-priority roads only")
            
        return strategy

# Usage example
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'roads_db',
        'user': 'postgres',
        'password': 'roadsdb2024secure'
    }
    
    crawler = SmartCrawlSelector(db_config)
    
    # Get high priority roads in California
    print("🎯 High Priority Roads in CA:")
    roads = crawler.get_high_priority_roads('CA', limit=10)
    for road in roads:
        print(f"  {road['road_name']}: {road['total_businesses']} businesses, "
              f"priority score: {road['crawl_priority_score']}")
    
    # Get crawl strategy
    print("\n📊 Crawl Strategy for CA:")
    strategy = crawler.get_crawl_strategy('CA')
    print(f"  Total businesses: {strategy['total_businesses']:,}")
    print(f"  Missing phone: {strategy['data_quality']['missing_phone_pct']}%")
    print(f"  Priority: {strategy['priority']}")
    print(f"  Recommendations: {', '.join(strategy['recommended_approach'])}")