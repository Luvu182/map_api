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
        
        # 1. Count total roads in San Diego
        query1 = """
        SELECT COUNT(DISTINCT r.name) as total_roads_san_diego
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
        WHERE rcm.city_name = 'San Diego' AND rcm.state_code = 'CA';
        """
        run_query(conn, query1, "1. Total roads in San Diego, CA")
        
        # 2. Count total POIs in San Diego (directly from POI table)
        query2 = """
        SELECT COUNT(*) as total_pois_san_diego
        FROM osm_business_pois
        WHERE city = 'San Diego' AND state_code = 'CA';
        """
        run_query(conn, query2, "2. Total POIs in San Diego")
        
        # 3. POI breakdown by business type in San Diego
        query3 = """
        SELECT 
            business_type,
            COUNT(*) as poi_count
        FROM osm_business_pois
        WHERE city = 'San Diego' AND state_code = 'CA'
        GROUP BY business_type
        ORDER BY poi_count DESC
        LIMIT 15;
        """
        run_query(conn, query3, "3. Top 15 business types in San Diego")
        
        # 4. Compare with Mobile, AL
        query4 = """
        SELECT 
            city || ', ' || state_code as location,
            COUNT(*) as total_pois
        FROM osm_business_pois
        WHERE (city = 'San Diego' AND state_code = 'CA')
           OR (city = 'Mobile' AND state_code = 'AL')
        GROUP BY city, state_code
        ORDER BY total_pois DESC;
        """
        run_query(conn, query4, "4. POI comparison: San Diego vs Mobile")
        
        # 5. Check road_poi_stats for California
        query5 = """
        SELECT 
            'California Roads' as category,
            COUNT(*) as roads_with_stats,
            SUM(poi_count) as total_pois_mapped,
            AVG(poi_count) as avg_pois_per_road,
            MAX(poi_count) as max_pois_on_road
        FROM road_poi_stats_al
        WHERE state_code = 'CA';
        """
        run_query(conn, query5, "5. Road POI stats for California (checking road_poi_stats_al)")
        
        # 6. Sample roads with POI counts using spatial join
        query6 = """
        WITH road_poi_counts AS (
            SELECT 
                r.name as road_name,
                COUNT(DISTINCT p.osm_id) as poi_count
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id
            LEFT JOIN osm_business_pois p 
                ON rcm.city_name = p.city 
                AND rcm.state_code = p.state_code
                AND ST_DWithin(r.geometry::geography, p.geometry::geography, 100) -- Within 100 meters
            WHERE rcm.city_name = 'San Diego' 
                AND rcm.state_code = 'CA'
            GROUP BY r.name
            HAVING COUNT(DISTINCT p.osm_id) > 0
        )
        SELECT * FROM road_poi_counts
        ORDER BY poi_count DESC
        LIMIT 10;
        """
        run_query(conn, query6, "6. Top 10 roads in San Diego with most POIs (using spatial proximity)")
        
        # 7. Check if we have pre-computed stats
        query7 = """
        SELECT 
            'road_poi_stats_al' as table_name,
            COUNT(*) as total_records,
            COUNT(CASE WHEN state_code = 'CA' THEN 1 END) as california_records
        FROM road_poi_stats_al
        UNION ALL
        SELECT 
            'road_poi_stats_hi' as table_name,
            COUNT(*) as total_records,
            COUNT(CASE WHEN state_code = 'CA' THEN 1 END) as california_records
        FROM road_poi_stats_hi;
        """
        run_query(conn, query7, "7. Check pre-computed POI stats tables")
        
        # 8. Check osm_stats_cache
        query8 = """
        SELECT * FROM osm_stats_cache
        WHERE city_name = 'San Diego' AND state_code = 'CA';
        """
        run_query(conn, query8, "8. San Diego stats from cache")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()