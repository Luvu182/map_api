#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'roads_db',
    'user': 'postgres',
    'password': 'roadsdb2024secure'
}

def run_query(conn, query, description):
    """Run a query and print results"""
    print(f"\n{description}")
    print("=" * 80)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if results:
                # Print column headers
                if results:
                    headers = list(results[0].keys())
                    print(" | ".join(f"{h:25}" for h in headers))
                    print("-" * 100)
                    
                    # Print rows
                    for row in results:
                        values = [str(row[h])[:25] for h in headers]
                        print(" | ".join(f"{v:25}" for v in values))
            else:
                print("No results")
        
        return results
    except Exception as e:
        print(f"Query error: {e}")
        return None

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        
        # First, let's check the schema of relevant tables
        print("\nChecking table schemas...")
        
        # Check osm_roads_main schema
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'osm_roads_main' 
                ORDER BY ordinal_position
                LIMIT 10;
            """)
            columns = cur.fetchall()
            print("\nColumns in osm_roads_main:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Check road_city_mapping schema
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'road_city_mapping' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("\nColumns in road_city_mapping:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Check osm_business_pois schema
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'osm_business_pois' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("\nColumns in osm_business_pois:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Now let's run the analysis queries
        
        # 1. Count total roads in San Diego
        query1 = """
        SELECT COUNT(DISTINCT r.name) as total_roads_san_diego
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA';
        """
        run_query(conn, query1, "1. Total roads in San Diego, CA")
        
        # 2. Count how many roads have POIs mapped
        query2 = """
        SELECT COUNT(DISTINCT r.name) as roads_with_pois
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        JOIN osm_business_pois obp ON r.osm_id = obp.road_osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA';
        """
        run_query(conn, query2, "2. Roads in San Diego with POIs mapped")
        
        # 3. Show top 10 roads with most POIs in San Diego
        query3 = """
        SELECT 
            r.name as road_name,
            COUNT(obp.osm_id) as poi_count
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        JOIN osm_business_pois obp ON r.osm_id = obp.road_osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA'
        GROUP BY r.name
        ORDER BY poi_count DESC
        LIMIT 10;
        """
        run_query(conn, query3, "3. Top 10 roads in San Diego with most POIs")
        
        # 4. Check total POI count for San Diego
        query4 = """
        SELECT COUNT(DISTINCT obp.osm_id) as total_pois_san_diego
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        JOIN osm_business_pois obp ON r.osm_id = obp.road_osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA';
        """
        run_query(conn, query4, "4. Total POI count for San Diego")
        
        # 5. Compare POI coverage percentage between San Diego and Mobile
        query5 = """
        WITH city_stats AS (
            SELECT 
                rcm.city_name,
                rcm.state_code,
                COUNT(DISTINCT r.name) as total_roads,
                COUNT(DISTINCT CASE WHEN obp.osm_id IS NOT NULL THEN r.name END) as roads_with_pois,
                COUNT(DISTINCT obp.osm_id) as total_pois
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
            LEFT JOIN osm_business_pois obp ON r.osm_id = obp.road_osm_id
            WHERE (rcm.city_name = 'San Diego' AND rcm.state_code = 'CA')
               OR (rcm.city_name = 'Mobile' AND rcm.state_code = 'AL')
            GROUP BY rcm.city_name, rcm.state_code
        )
        SELECT 
            city_name || ', ' || state_code as city,
            total_roads,
            roads_with_pois,
            total_pois,
            ROUND(100.0 * roads_with_pois / NULLIF(total_roads, 0), 2) as coverage_percentage
        FROM city_stats
        ORDER BY city_name;
        """
        run_query(conn, query5, "5. POI coverage comparison: San Diego vs Mobile")
        
        # Additional query: Check if San Diego exists in road_city_mapping
        query_check = """
        SELECT city_name, state_code, COUNT(*) as road_segments
        FROM road_city_mapping
        WHERE city_name ILIKE '%san diego%'
        GROUP BY city_name, state_code
        ORDER BY road_segments DESC;
        """
        run_query(conn, query_check, "Check: San Diego in road_city_mapping table")
        
        # Check sample POIs
        query_sample_pois = """
        SELECT 
            obp.name,
            obp.amenity,
            obp.shop,
            r.name as road_name,
            rcm.city_name
        FROM osm_business_pois obp
        JOIN osm_roads_main r ON obp.road_osm_id = r.osm_id
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA'
        LIMIT 10;
        """
        run_query(conn, query_sample_pois, "Sample POIs in San Diego")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()