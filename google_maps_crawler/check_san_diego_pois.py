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
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            # Print column headers
            if results:
                headers = list(results[0].keys())
                print(" | ".join(f"{h:20}" for h in headers))
                print("-" * 80)
                
                # Print rows
                for row in results:
                    values = [str(row[h])[:20] for h in headers]
                    print(" | ".join(f"{v:20}" for v in values))
        else:
            print("No results")
    
    return results

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        
        # 1. Count total roads in San Diego
        query1 = """
        SELECT COUNT(DISTINCT road_name) as total_roads_san_diego
        FROM target_roads
        WHERE city_name = 'San Diego' AND state_code = 'CA';
        """
        run_query(conn, query1, "1. Total roads in San Diego, CA")
        
        # 2. Count how many roads have POIs mapped
        query2 = """
        SELECT COUNT(DISTINCT tr.road_name) as roads_with_pois
        FROM target_roads tr
        JOIN osm_business_pois obp ON tr.linearid = obp.linearid
        WHERE tr.city_name = 'San Diego' AND tr.state_code = 'CA';
        """
        run_query(conn, query2, "2. Roads in San Diego with POIs mapped")
        
        # 3. Show top 10 roads with most POIs in San Diego
        query3 = """
        SELECT 
            tr.road_name,
            COUNT(obp.osm_id) as poi_count
        FROM target_roads tr
        JOIN osm_business_pois obp ON tr.linearid = obp.linearid
        WHERE tr.city_name = 'San Diego' AND tr.state_code = 'CA'
        GROUP BY tr.road_name
        ORDER BY poi_count DESC
        LIMIT 10;
        """
        run_query(conn, query3, "3. Top 10 roads in San Diego with most POIs")
        
        # 4. Check total POI count for San Diego
        query4 = """
        SELECT COUNT(DISTINCT obp.osm_id) as total_pois_san_diego
        FROM target_roads tr
        JOIN osm_business_pois obp ON tr.linearid = obp.linearid
        WHERE tr.city_name = 'San Diego' AND tr.state_code = 'CA';
        """
        run_query(conn, query4, "4. Total POI count for San Diego")
        
        # 5. Compare POI coverage percentage between San Diego and Mobile
        query5 = """
        WITH city_stats AS (
            SELECT 
                tr.city_name,
                tr.state_code,
                COUNT(DISTINCT tr.road_name) as total_roads,
                COUNT(DISTINCT CASE WHEN obp.osm_id IS NOT NULL THEN tr.road_name END) as roads_with_pois,
                COUNT(DISTINCT obp.osm_id) as total_pois
            FROM target_roads tr
            LEFT JOIN osm_business_pois obp ON tr.linearid = obp.linearid
            WHERE (tr.city_name = 'San Diego' AND tr.state_code = 'CA')
               OR (tr.city_name = 'Mobile' AND tr.state_code = 'AL')
            GROUP BY tr.city_name, tr.state_code
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
        
        # Additional query: Check if San Diego exists in target_roads
        query_check = """
        SELECT city_name, state_code, COUNT(*) as road_segments
        FROM target_roads
        WHERE city_name ILIKE '%san diego%'
        GROUP BY city_name, state_code;
        """
        run_query(conn, query_check, "Check: San Diego in target_roads table")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()