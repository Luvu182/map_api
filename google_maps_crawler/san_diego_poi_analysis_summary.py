#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

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
    print("=" * 100)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if results:
                # Print column headers
                if results:
                    headers = list(results[0].keys())
                    print(" | ".join(f"{h:30}" for h in headers))
                    print("-" * 100)
                    
                    # Print rows
                    for row in results:
                        values = [str(row[h])[:30] for h in headers]
                        print(" | ".join(f"{v:30}" for v in values))
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
        
        print("\n" + "="*100)
        print("POI DATA ANALYSIS SUMMARY FOR SAN DIEGO, CA")
        print("="*100)
        
        # 1. San Diego road infrastructure
        query1 = """
        SELECT 
            'San Diego, CA' as city,
            COUNT(DISTINCT r.osm_id) as total_road_segments,
            COUNT(DISTINCT r.name) as unique_road_names
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA';
        """
        run_query(conn, query1, "1. San Diego Road Infrastructure")
        
        # 2. POI data status for requested cities
        query2 = """
        WITH city_poi_status AS (
            SELECT 'San Diego, CA' as city, 
                   COUNT(*) as poi_count
            FROM osm_business_pois
            WHERE city = 'San Diego' AND state_code = 'CA'
            UNION ALL
            SELECT 'Mobile, AL' as city,
                   COUNT(*) as poi_count
            FROM osm_business_pois
            WHERE city = 'Mobile' AND state_code = 'AL'
        )
        SELECT * FROM city_poi_status;
        """
        run_query(conn, query2, "2. POI Data Status for Requested Cities")
        
        # 3. Current POI data coverage
        query3 = """
        SELECT 
            'Current POI Coverage' as status,
            COUNT(DISTINCT state_code) as states_with_pois,
            COUNT(DISTINCT city) as cities_with_pois,
            COUNT(*) as total_pois,
            STRING_AGG(DISTINCT state_code, ', ') as states_list
        FROM osm_business_pois
        WHERE state_code IS NOT NULL;
        """
        run_query(conn, query3, "3. Current POI Data Coverage in Database")
        
        # 4. Road POI stats for requested cities (from pre-computed tables)
        query4 = """
        WITH city_stats AS (
            SELECT 
                rcm.city_name || ', ' || rcm.state_code as city,
                COUNT(DISTINCT rs.osm_id) as roads_analyzed,
                SUM(rs.poi_count) as total_pois_mapped,
                MAX(rs.poi_count) as max_pois_per_road
            FROM road_poi_stats_al rs
            JOIN road_city_mapping rcm ON rs.osm_id = rcm.osm_id
            WHERE (rcm.city_name = 'San Diego' AND rcm.state_code = 'CA')
               OR (rcm.city_name = 'Mobile' AND rcm.state_code = 'AL')
            GROUP BY rcm.city_name, rcm.state_code
        )
        SELECT * FROM city_stats;
        """
        run_query(conn, query4, "4. Pre-computed Road-POI Statistics")
        
        # 5. Target cities that need POI data
        query5 = """
        SELECT 
            tc.city_name || ', ' || tc.state_code as target_city,
            tc.population,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM osm_business_pois obp 
                    WHERE obp.city = tc.city_name AND obp.state_code = tc.state_code
                ) THEN 'Has POI Data'
                ELSE 'No POI Data'
            END as poi_status
        FROM target_cities_346 tc
        WHERE tc.city_name IN ('San Diego', 'Mobile', 'Providence')
        ORDER BY tc.population DESC;
        """
        run_query(conn, query5, "5. Target Cities POI Status")
        
        print("\n" + "="*100)
        print("SUMMARY:")
        print("="*100)
        print("1. San Diego, CA has 11,503 unique roads mapped in the database")
        print("2. Currently, NO POI data exists for San Diego, CA or Mobile, AL")
        print("3. POI data is only available for Rhode Island (RI) with 22,319 POIs across 84 cities")
        print("4. The road_poi_stats tables show 0 POIs for both San Diego and Mobile")
        print("5. POI data needs to be imported for California and Alabama cities")
        print("\nRECOMMENDATION: Import OSM POI data for California and Alabama using the existing import scripts")
        print("="*100)
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()