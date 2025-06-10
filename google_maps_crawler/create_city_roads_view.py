#!/usr/bin/env python3
"""Create the city_roads_simple materialized view"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query, get_db_connection
import psycopg2

def create_view():
    """Create city_roads_simple materialized view"""
    
    print("Creating city_roads_simple materialized view...")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop if exists
        print("Dropping existing view if any...")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS city_roads_simple CASCADE")
        
        # Create the view
        print("Creating materialized view...")
        create_query = """
        CREATE MATERIALIZED VIEW city_roads_simple AS
        SELECT 
            r.osm_id,
            r.name as road_name,
            r.highway,
            r.ref,
            rcm.city_name,
            rcm.state_code,
            r.county_fips
        FROM osm_roads_main r
        INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE r.name IS NOT NULL
        """
        cursor.execute(create_query)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_city_roads_simple_city ON city_roads_simple(city_name, state_code)")
        cursor.execute("CREATE INDEX idx_city_roads_simple_name ON city_roads_simple(road_name)")
        cursor.execute("CREATE INDEX idx_city_roads_simple_state ON city_roads_simple(state_code)")
        cursor.execute("CREATE INDEX idx_city_roads_simple_osm_id ON city_roads_simple(osm_id)")
        
        # Analyze
        print("Analyzing view...")
        cursor.execute("ANALYZE city_roads_simple")
        
        # Commit
        conn.commit()
        
        # Get count
        cursor.execute("SELECT COUNT(*) as total_roads FROM city_roads_simple")
        result = cursor.fetchone()
        print(f"\nView created successfully with {result[0]} roads")
        
        # Check Mobile specifically
        cursor.execute("""
            SELECT COUNT(*) as mobile_roads 
            FROM city_roads_simple 
            WHERE city_name = 'Mobile' AND state_code = 'AL'
        """)
        result = cursor.fetchone()
        print(f"Mobile, AL has {result[0]} roads in the view")
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_view()