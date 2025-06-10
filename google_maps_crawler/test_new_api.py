#!/usr/bin/env python3
"""
Test script for new Google Maps Places API
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crawler.google_maps import GoogleMapsClient
from app.database.postgres_client import PostgresClient
import json

def test_text_search():
    """Test basic text search functionality"""
    print("=== Testing New Places API ===\n")
    
    # Initialize client
    gmaps = GoogleMapsClient()
    
    if not gmaps.api_key:
        print("❌ No API key configured!")
        print("Please set GOOGLE_MAPS_API_KEY in your .env file")
        return
    
    # Test 1: Basic text search
    print("1. Testing basic text search...")
    results = gmaps.search_text("restaurants in Times Square, New York", tier='basic')
    print(f"   Found {len(results)} results")
    if results:
        print(f"   First result: {results[0].get('displayName', {}).get('text', 'N/A')}")
    
    # Test 2: Road-based search
    print("\n2. Testing road-based search...")
    results = gmaps.search_businesses_on_road(
        road_name="Broadway",
        city_name="New York",
        state_code="NY",
        tier='enterprise_minimal'
    )
    print(f"   Found {len(results)} businesses on Broadway")
    
    # Test 3: Enterprise tier with all fields
    print("\n3. Testing enterprise tier (all fields)...")
    results = gmaps.search_businesses_on_road(
        road_name="Main Street",
        city_name="Los Angeles", 
        state_code="CA",
        center_lat=34.0522,
        center_lng=-118.2437,
        tier='enterprise'
    )
    
    if results:
        print(f"   Found {len(results)} results")
        # Check which fields we got
        first = results[0]
        fields_received = []
        
        field_checks = {
            'displayName': 'Name',
            'nationalPhoneNumber': 'Phone',
            'websiteUri': 'Website',
            'rating': 'Rating',
            'currentOpeningHours': 'Hours',
            'priceLevel': 'Price Level'
        }
        
        for field, label in field_checks.items():
            if field in first:
                fields_received.append(label)
        
        print(f"   Fields received: {', '.join(fields_received)}")
        
        # Parse and display first business
        business = gmaps.parse_business(first, 12345, "Main Street")
        print(f"\n   Sample Business:")
        print(f"   - Name: {business.name}")
        print(f"   - Phone: {business.phone_number}")
        print(f"   - Rating: {business.rating}")
        print(f"   - Website: {business.website}")

def test_with_real_road():
    """Test with actual road from database"""
    print("\n=== Testing with Real Road Data ===\n")
    
    from app.database.postgres_client import execute_query
    gmaps = GoogleMapsClient()
    
    # Get a high-potential road
    road = execute_query("""
        SELECT 
            r.osm_id,
            r.name,
            rcm.city_name,
            rcm.state_code,
            ST_Y(ST_Centroid(r.geometry)) as lat,
            ST_X(ST_Centroid(r.geometry)) as lng,
            rbs.poi_count
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        LEFT JOIN road_business_stats rbs ON r.osm_id = rbs.osm_id
        WHERE r.name IS NOT NULL
        AND rcm.city_name IN ('New York', 'Los Angeles', 'Chicago')
        AND rbs.poi_count > 20
        ORDER BY rbs.poi_count DESC
        LIMIT 1
    """, fetch_one=True)
    
    if road:
        print(f"Testing road: {road['name']}, {road['city_name']}, {road['state_code']}")
        print(f"OSM POI count: {road['poi_count']}")
        
        results = gmaps.search_businesses_on_road(
            road_name=road['name'],
            city_name=road['city_name'],
            state_code=road['state_code'],
            center_lat=road['lat'],
            center_lng=road['lng'],
            tier='enterprise'
        )
        
        print(f"\nGoogle Maps found: {len(results)} businesses")
        
        # Show business types found
        if results:
            types_found = set()
            for r in results:
                types_found.update(r.get('types', []))
            
            print(f"Business types: {', '.join(list(types_found)[:10])}...")

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        print("⚠️  Please set GOOGLE_MAPS_API_KEY environment variable")
        print("   export GOOGLE_MAPS_API_KEY='your-key-here'")
        sys.exit(1)
    
    try:
        test_text_search()
        test_with_real_road()
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()