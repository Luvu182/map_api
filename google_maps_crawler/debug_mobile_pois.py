#!/usr/bin/env python3
"""Debug why POI count shows 0 for Mobile, AL"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query, get_db_connection
import psycopg2

def debug_mobile_pois():
    """Debug POI count issues for Mobile, AL"""
    
    print("=== Debugging Mobile, AL POI Count ===\n")
    
    # First, check the actual columns in osm_roads_main
    query0 = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'osm_roads_main' 
        ORDER BY ordinal_position
        LIMIT 20
    """
    print("0. Columns in osm_roads_main table:")
    columns = execute_query(query0)
    for col in columns:
        print(f"   - {col['column_name']}: {col['data_type']}")
    
    # 1. Check if there are roads in Mobile, AL using road_city_mapping
    query1 = """
        SELECT COUNT(DISTINCT r.osm_id) as road_count 
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
    """
    result = execute_query(query1, fetch_one=True)
    print(f"\n1. Total roads in Mobile, AL: {result['road_count']}")
    
    # 2. Show 5 sample roads in Mobile with their osm_id
    query2 = """
        SELECT r.osm_id, r.name, r.highway, rcm.city_name, rcm.state_code
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
        AND r.name IS NOT NULL
        LIMIT 5
    """
    print("\n2. Sample roads in Mobile, AL:")
    roads = execute_query(query2)
    for road in roads:
        print(f"   - OSM ID: {road['osm_id']}, Name: {road['name']}, Type: {road['highway']}")
    
    # 3. Check data types
    query3 = """
        SELECT 
            column_name, 
            data_type 
        FROM information_schema.columns 
        WHERE table_name = 'osm_roads_main' AND column_name = 'osm_id'
        
        UNION ALL
        
        SELECT 
            column_name, 
            data_type 
        FROM information_schema.columns 
        WHERE table_name = 'osm_businesses' AND column_name = 'nearest_road_id'
    """
    print("\n3. Data type check:")
    types = execute_query(query3)
    for t in types:
        print(f"   - {t['column_name']}: {t['data_type']}")
    
    # 4. Check if there are any businesses in Mobile area (by coordinates)
    query4 = """
        SELECT COUNT(*) as business_count
        FROM osm_businesses b
        WHERE b.lat BETWEEN 30.6 AND 30.8 
        AND b.lon BETWEEN -88.3 AND -88.0
    """
    result = execute_query(query4, fetch_one=True)
    print(f"\n4. Total businesses in Mobile area (by coordinates): {result['business_count']}")
    
    # 5. Show sample businesses in Mobile area
    if result['business_count'] > 0:
        query5 = """
            SELECT 
                b.osm_id as business_osm_id,
                b.name,
                b.nearest_road_id,
                b.lat,
                b.lon,
                b.amenity
            FROM osm_businesses b
            WHERE b.lat BETWEEN 30.6 AND 30.8 
            AND b.lon BETWEEN -88.3 AND -88.0
            LIMIT 5
        """
        print("\n5. Sample businesses in Mobile area:")
        businesses = execute_query(query5)
        for biz in businesses:
            print(f"   - Business: {biz['name']}, Nearest Road ID: {biz['nearest_road_id']}, Type: {biz['amenity']}")
    
    # 6. Check if any of these businesses match roads in Mobile
    query6 = """
        SELECT COUNT(*) as matched_count
        FROM osm_businesses b
        INNER JOIN osm_roads_main r ON b.nearest_road_id = r.osm_id
        INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
    """
    result = execute_query(query6, fetch_one=True)
    print(f"\n6. Businesses matched to Mobile roads: {result['matched_count']}")
    
    # 7. Check for type casting issues - try explicit casting
    query7 = """
        SELECT COUNT(*) as matched_count_cast
        FROM osm_businesses b
        INNER JOIN osm_roads_main r ON CAST(b.nearest_road_id AS BIGINT) = r.osm_id
        INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
    """
    try:
        result = execute_query(query7, fetch_one=True)
        print(f"\n7. Businesses matched with explicit casting: {result['matched_count_cast']}")
    except Exception as e:
        print(f"\n7. Error with casting: {e}")
    
    # 8. Check if nearest_road_id values exist in osm_roads_main at all
    query8 = """
        WITH mobile_area_businesses AS (
            SELECT DISTINCT nearest_road_id
            FROM osm_businesses
            WHERE lat BETWEEN 30.6 AND 30.8 
            AND lon BETWEEN -88.3 AND -88.0
            AND nearest_road_id IS NOT NULL
            LIMIT 10
        )
        SELECT 
            mb.nearest_road_id,
            CASE WHEN r.osm_id IS NOT NULL THEN 'Found' ELSE 'Not Found' END as road_exists,
            rcm.city_name,
            rcm.state_code
        FROM mobile_area_businesses mb
        LEFT JOIN osm_roads_main r ON mb.nearest_road_id = r.osm_id
        LEFT JOIN road_city_mapping rcm ON r.id = rcm.road_id
    """
    print("\n8. Checking if nearest_road_id values exist in osm_roads_main:")
    results = execute_query(query8)
    for res in results:
        print(f"   - Road ID {res['nearest_road_id']}: {res['road_exists']}, City: {res['city_name']}, State: {res['state_code']}")
    
    # 9. Alternative approach - check businesses near Mobile roads using spatial query
    query9 = """
        WITH mobile_roads AS (
            SELECT r.osm_id, r.geometry
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
            LIMIT 100
        )
        SELECT COUNT(DISTINCT b.osm_id) as nearby_businesses
        FROM osm_businesses b
        JOIN mobile_roads r ON ST_DWithin(
            ST_SetSRID(ST_MakePoint(b.lon, b.lat), 4326)::geography,
            r.geometry::geography,
            100  -- within 100 meters
        )
    """
    try:
        result = execute_query(query9, fetch_one=True)
        print(f"\n9. Businesses within 100m of Mobile roads (spatial): {result['nearby_businesses']}")
    except Exception as e:
        print(f"\n9. Error with spatial query: {e}")
    
    # 10. MOST IMPORTANT - Check the exact query used in the dashboard
    query10 = """
        SELECT 
            COUNT(DISTINCT b.osm_id) as poi_count,
            COUNT(DISTINCT r.osm_id) as roads_with_pois
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        LEFT JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
        WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
    """
    result = execute_query(query10, fetch_one=True)
    print(f"\n10. Dashboard query - POI count: {result['poi_count']}, Roads with POIs: {result['roads_with_pois']}")
    
    # 11. Check if the issue is with the join direction
    query11 = """
        SELECT 
            COUNT(DISTINCT b.osm_id) as business_count
        FROM osm_businesses b
        WHERE b.nearest_road_id IN (
            SELECT r.osm_id 
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.city_name = 'Mobile' AND rcm.state_code = 'AL'
        )
    """
    result = execute_query(query11, fetch_one=True)
    print(f"\n11. Businesses linked to Mobile roads (subquery): {result['business_count']}")

if __name__ == "__main__":
    debug_mobile_pois()