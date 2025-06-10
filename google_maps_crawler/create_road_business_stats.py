#!/usr/bin/env python3
"""Create the road_business_stats materialized view"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query, get_db_connection
import psycopg2

def create_view():
    """Create road_business_stats materialized view"""
    
    print("Creating road_business_stats materialized view...")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop if exists
        print("Dropping existing view if any...")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS road_business_stats CASCADE")
        
        # Create the view
        print("Creating materialized view (this may take a while)...")
        create_query = """
        CREATE MATERIALIZED VIEW road_business_stats AS
        SELECT 
            r.osm_id,
            r.name,
            r.highway,
            r.state_code,
            r.county_fips,
            -- POI counts
            COUNT(DISTINCT b.osm_id) as poi_count,
            COUNT(DISTINCT b.business_type) as business_type_variety,
            COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL) as brand_count,
            -- POI categories
            COUNT(*) FILTER (WHERE b.business_type = 'shop') as shops,
            COUNT(*) FILTER (WHERE b.business_type = 'amenity' AND b.business_subtype IN ('restaurant', 'cafe', 'fast_food', 'bar')) as food_places,
            COUNT(*) FILTER (WHERE b.business_type = 'amenity' AND b.business_subtype IN ('bank', 'pharmacy')) as essential_services,
            -- Data quality
            COUNT(*) FILTER (WHERE b.phone IS NOT NULL AND b.phone != '') as has_phone,
            COUNT(*) FILTER (WHERE b.opening_hours IS NOT NULL AND b.opening_hours != '') as has_hours,
            -- Calculate business potential score (0-100)
            CASE 
                WHEN COUNT(b.osm_id) = 0 THEN 0
                WHEN COUNT(b.osm_id) >= 20 THEN 100
                WHEN COUNT(b.osm_id) >= 10 THEN 80
                WHEN COUNT(b.osm_id) >= 5 THEN 60
                WHEN COUNT(b.osm_id) >= 3 THEN 40
                WHEN COUNT(b.osm_id) >= 1 THEN 20
                ELSE 0
            END as business_potential_score,
            -- Top categories and brands
            STRING_AGG(DISTINCT b.business_type || ':' || b.business_subtype, ', ' ORDER BY b.business_type || ':' || b.business_subtype) 
                FILTER (WHERE b.business_subtype IS NOT NULL) as business_categories,
            STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
                FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as top_brands
        FROM osm_roads_main r
        LEFT JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
        WHERE r.name IS NOT NULL
        GROUP BY r.osm_id, r.name, r.highway, r.state_code, r.county_fips
        """
        cursor.execute(create_query)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_road_business_stats_osm_id ON road_business_stats(osm_id)")
        cursor.execute("CREATE INDEX idx_road_business_stats_state ON road_business_stats(state_code)")
        cursor.execute("CREATE INDEX idx_road_business_stats_score ON road_business_stats(business_potential_score DESC)")
        cursor.execute("CREATE INDEX idx_road_business_stats_poi_count ON road_business_stats(poi_count DESC)")
        
        # Commit
        conn.commit()
        
        # Get count
        cursor.execute("SELECT COUNT(*) as total_roads FROM road_business_stats")
        result = cursor.fetchone()
        print(f"\nView created successfully with {result[0]} roads")
        
        # Check roads with POIs
        cursor.execute("SELECT COUNT(*) as roads_with_pois FROM road_business_stats WHERE poi_count > 0")
        result = cursor.fetchone()
        print(f"Roads with POIs: {result[0]}")
        
        # Check Mobile specifically
        cursor.execute("""
            SELECT 
                COUNT(*) as mobile_roads,
                SUM(poi_count) as total_pois
            FROM road_business_stats rbs
            JOIN road_city_mapping rcm ON rbs.osm_id = (
                SELECT osm_id FROM osm_roads_main WHERE id = rcm.road_id
            )
            WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
        """)
        result = cursor.fetchone()
        print(f"\nMobile, AL stats:")
        print(f"  Roads: {result[0]}")
        print(f"  Total POIs: {result[1] or 0}")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_view()