#!/usr/bin/env python3
"""Debug the exact API query for Mobile, AL POI count"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query

city_name = "Mobile"
state_code = "AL"

# First check if city_roads_simple view exists and has data for Mobile
query1 = """
    SELECT COUNT(*) as count
    FROM pg_matviews
    WHERE matviewname = 'city_roads_simple'
"""
result = execute_query(query1, fetch_one=True)
print(f"1. city_roads_simple materialized view exists: {result['count'] > 0}")

if result['count'] > 0:
    # Check data in city_roads_simple for Mobile
    query2 = """
        SELECT COUNT(*) as road_count
        FROM city_roads_simple
        WHERE city_name = %s AND state_code = %s
    """
    result = execute_query(query2, [city_name, state_code], fetch_one=True)
    print(f"2. Roads in city_roads_simple for Mobile, AL: {result['road_count']}")
    
    # Show sample roads
    query3 = """
        SELECT osm_id, road_name, highway
        FROM city_roads_simple
        WHERE city_name = %s AND state_code = %s
        LIMIT 5
    """
    print("\n3. Sample roads from city_roads_simple:")
    roads = execute_query(query3, [city_name, state_code])
    for road in roads:
        print(f"   - OSM ID: {road['osm_id']}, Name: {road['road_name']}, Type: {road['highway']}")

# Now test the exact subquery from the API
query4 = """
    SELECT nearest_road_id, COUNT(*) as poi_count
    FROM osm_businesses
    WHERE state_code = %s
    GROUP BY nearest_road_id
    HAVING nearest_road_id IN (
        SELECT osm_id FROM city_roads_simple 
        WHERE city_name = %s AND state_code = %s
    )
    LIMIT 10
"""
print(f"\n4. Testing POI subquery for state {state_code} and Mobile roads:")
results = execute_query(query4, [state_code, city_name, state_code])
for res in results:
    print(f"   - Road ID {res['nearest_road_id']}: {res['poi_count']} POIs")

# Check businesses in AL that might match Mobile roads
query5 = """
    WITH mobile_roads AS (
        SELECT DISTINCT r.osm_id
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = %s AND rcm.state_code = %s
    )
    SELECT 
        COUNT(DISTINCT b.osm_id) as business_count,
        COUNT(DISTINCT b.nearest_road_id) as unique_roads_with_businesses
    FROM osm_businesses b
    WHERE b.state_code = %s
        AND b.nearest_road_id IN (SELECT osm_id FROM mobile_roads)
"""
result = execute_query(query5, [city_name, state_code, state_code], fetch_one=True)
print(f"\n5. Businesses in AL linked to Mobile roads:")
print(f"   - Total businesses: {result['business_count']}")
print(f"   - Unique roads with businesses: {result['unique_roads_with_businesses']}")

# Show some actual business examples
query6 = """
    WITH mobile_roads AS (
        SELECT DISTINCT r.osm_id, r.name as road_name
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        WHERE rcm.city_name = %s AND rcm.state_code = %s
    )
    SELECT 
        b.name as business_name,
        b.business_type,
        b.nearest_road_id,
        mr.road_name,
        b.city as business_city
    FROM osm_businesses b
    JOIN mobile_roads mr ON b.nearest_road_id = mr.osm_id
    WHERE b.state_code = %s
    LIMIT 10
"""
print(f"\n6. Sample businesses in Mobile:")
businesses = execute_query(query6, [city_name, state_code, state_code])
for biz in businesses:
    print(f"   - {biz['business_name']} ({biz['business_type']}) on {biz['road_name']} (Road ID: {biz['nearest_road_id']})")