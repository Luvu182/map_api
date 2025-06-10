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
        
        # List all tables
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename;
            """)
            tables = cur.fetchall()
            
            print("\nTables in the database:")
            print("=" * 80)
            for table in tables:
                print(f"{table['schemaname']:15} | {table['tablename']:30} | {table['size']:10}")
        
        # Check for POI related tables
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    tablename
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (tablename LIKE '%poi%' OR tablename LIKE '%business%' OR tablename LIKE '%osm%')
                ORDER BY tablename;
            """)
            poi_tables = cur.fetchall()
            
            print("\nPOI/Business related tables:")
            print("=" * 80)
            for table in poi_tables:
                print(f"- {table['tablename']}")
        
        # Check for road/city tables
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    tablename
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (tablename LIKE '%road%' OR tablename LIKE '%city%' OR tablename LIKE '%target%')
                ORDER BY tablename;
            """)
            road_tables = cur.fetchall()
            
            print("\nRoad/City related tables:")
            print("=" * 80)
            for table in road_tables:
                print(f"- {table['tablename']}")
                
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()