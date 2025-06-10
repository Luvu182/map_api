#!/usr/bin/env python3
"""
Script to find and display the top 20 roads in San Diego by POI count
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from tabulate import tabulate

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'roads_db',  # Updated to match the database name in postgres_client.py
    'user': 'postgres',
    'password': 'roadsdb2024secure'
}

def run_query():
    """Execute the query and display results"""
    
    # The main query
    query = """
    WITH san_diego_roads AS (
        -- First get all roads that are in San Diego
        SELECT DISTINCT 
            r.osm_id,
            r.name as road_name,
            r.highway,
            r.geometry
        FROM osm_roads_main r
        INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = 'San Diego' 
            AND rcm.state_code = 'CA'
            AND r.name IS NOT NULL
    ),
    road_poi_counts AS (
        -- Count POIs for each road
        SELECT 
            sr.osm_id,
            sr.road_name,
            sr.highway,
            COUNT(DISTINCT b.osm_id) as poi_count
        FROM san_diego_roads sr
        LEFT JOIN osm_businesses b ON b.nearest_road_id = sr.osm_id
        GROUP BY sr.osm_id, sr.road_name, sr.highway
    )
    -- Final result: top 20 roads by POI count
    SELECT 
        road_name,
        osm_id,
        highway as highway_type,
        poi_count
    FROM road_poi_counts
    ORDER BY poi_count DESC
    LIMIT 20;
    """
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("Executing query...")
            cur.execute(query)
            results = cur.fetchall()
            
            if results:
                # Prepare data for tabulate
                headers = ["Rank", "Road Name", "OSM ID", "Highway Type", "POI Count"]
                table_data = []
                
                for idx, row in enumerate(results, 1):
                    table_data.append([
                        idx,
                        row['road_name'],
                        row['osm_id'],
                        row['highway_type'],
                        row['poi_count']
                    ])
                
                # Display results
                print("\n" + "="*80)
                print("TOP 20 ROADS IN SAN DIEGO BY POI COUNT")
                print("="*80 + "\n")
                
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                # Summary statistics
                total_pois = sum(row['poi_count'] for row in results)
                avg_pois = total_pois / len(results) if results else 0
                
                print(f"\nSummary:")
                print(f"- Total POIs on top 20 roads: {total_pois:,}")
                print(f"- Average POIs per road: {avg_pois:.1f}")
                print(f"- Highest POI count: {results[0]['poi_count']:,} ({results[0]['road_name']})")
                
            else:
                print("No results found. This could mean:")
                print("1. San Diego is not in the road_city_mapping table")
                print("2. No POIs are mapped to San Diego roads")
                print("3. There's an issue with the table joins")
                
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def check_data_availability():
    """Check if San Diego data exists in the database"""
    
    checks = [
        ("San Diego roads in road_city_mapping", """
            SELECT COUNT(DISTINCT r.osm_id) as count
            FROM osm_roads_main r
            INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA'
        """),
        ("Total POIs in osm_businesses", """
            SELECT COUNT(*) as count FROM osm_businesses
        """),
        ("POIs with nearest_road_id assigned", """
            SELECT COUNT(*) as count FROM osm_businesses WHERE nearest_road_id IS NOT NULL
        """)
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        print("\nData Availability Check:")
        print("-" * 50)
        
        for description, query in checks:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()
                count = result[0] if result else 0
                print(f"{description}: {count:,}")
        
        conn.close()
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f"Error checking data: {e}")

if __name__ == "__main__":
    # First check data availability
    check_data_availability()
    
    # Then run the main query
    run_query()