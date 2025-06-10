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

def main():
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Check if there's a linearid column in osm_business_pois
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'osm_business_pois'
                AND column_name LIKE '%road%' OR column_name LIKE '%linear%'
                ORDER BY column_name;
            """)
            columns = cur.fetchall()
            print("\nColumns in osm_business_pois related to roads:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Check all columns
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'osm_business_pois'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("\nAll columns in osm_business_pois:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Check sample data from osm_business_pois
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * 
                FROM osm_business_pois 
                WHERE city = 'San Diego' AND state_code = 'CA'
                LIMIT 5;
            """)
            results = cur.fetchall()
            
            print("\nSample POIs in San Diego:")
            if results:
                for i, row in enumerate(results):
                    print(f"\nPOI {i+1}:")
                    for key, value in row.items():
                        if key != 'geometry' and key != 'tags':  # Skip complex fields
                            print(f"  {key}: {value}")
        
        # Check if there's a separate join table
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT tablename
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (tablename LIKE '%road%poi%' OR tablename LIKE '%poi%road%')
                ORDER BY tablename;
            """)
            tables = cur.fetchall()
            
            print("\nTables that might link roads and POIs:")
            for table in tables:
                print(f"- {table['tablename']}")
        
        # Check road_poi_stats tables
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('road_poi_stats_al', 'road_poi_stats_hi')
                ORDER BY table_name, ordinal_position
                LIMIT 10;
            """)
            columns = cur.fetchall()
            print("\nColumns in road_poi_stats tables:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
                
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()