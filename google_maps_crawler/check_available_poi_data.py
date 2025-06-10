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
        
        # 1. Check which cities have POI data
        query1 = """
        SELECT 
            city,
            state_code,
            COUNT(*) as poi_count
        FROM osm_business_pois
        WHERE city IS NOT NULL
        GROUP BY city, state_code
        ORDER BY poi_count DESC
        LIMIT 20;
        """
        run_query(conn, query1, "1. Top 20 cities with POI data")
        
        # 2. Check states with POI data
        query2 = """
        SELECT 
            state_code,
            COUNT(*) as poi_count,
            COUNT(DISTINCT city) as city_count
        FROM osm_business_pois
        WHERE state_code IS NOT NULL
        GROUP BY state_code
        ORDER BY poi_count DESC;
        """
        run_query(conn, query2, "2. States with POI data")
        
        # 3. Check total POI count
        query3 = """
        SELECT 
            COUNT(*) as total_pois,
            COUNT(DISTINCT city) as total_cities,
            COUNT(DISTINCT state_code) as total_states
        FROM osm_business_pois;
        """
        run_query(conn, query3, "3. Overall POI statistics")
        
        # 4. Check if Mobile, AL has data
        query4 = """
        SELECT 
            city,
            state_code,
            COUNT(*) as poi_count
        FROM osm_business_pois
        WHERE city ILIKE '%mobile%' 
        GROUP BY city, state_code
        ORDER BY poi_count DESC;
        """
        run_query(conn, query4, "4. Cities with 'Mobile' in the name")
        
        # 5. Check California cities
        query5 = """
        SELECT 
            city,
            COUNT(*) as poi_count
        FROM osm_business_pois
        WHERE state_code = 'CA'
        GROUP BY city
        ORDER BY poi_count DESC
        LIMIT 15;
        """
        run_query(conn, query5, "5. California cities with POI data")
        
        # 6. Check road_poi_stats_al for specific cities
        query6 = """
        SELECT 
            rs.state_code,
            rcm.city_name,
            COUNT(DISTINCT rs.osm_id) as roads_with_stats,
            SUM(rs.poi_count) as total_pois
        FROM road_poi_stats_al rs
        JOIN road_city_mapping rcm ON rs.osm_id = rcm.osm_id
        WHERE rcm.city_name IN ('Mobile', 'Birmingham', 'Montgomery', 'Huntsville')
        GROUP BY rs.state_code, rcm.city_name
        ORDER BY total_pois DESC;
        """
        run_query(conn, query6, "6. POI stats for Alabama cities")
        
        # 7. Check osm_stats_cache schema
        query7 = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'osm_stats_cache'
        ORDER BY ordinal_position;
        """
        run_query(conn, query7, "7. Schema of osm_stats_cache table")
        
        # 8. Sample from osm_stats_cache
        query8 = """
        SELECT * FROM osm_stats_cache LIMIT 5;
        """
        run_query(conn, query8, "8. Sample data from osm_stats_cache")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()