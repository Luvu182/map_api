#!/usr/bin/env python3
"""
Check statistics about roads with null names
"""

from supabase import create_client, Client

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_null_names():
    """Check roads with null names"""
    print("Checking roads with null names...\n")
    
    # Count total roads
    total_result = supabase.table('roads').select('count', count='exact').execute()
    total_roads = total_result.count
    
    # Count roads with null names
    null_result = supabase.table('roads').select('count', count='exact').is_('fullname', 'null').execute()
    null_roads = null_result.count
    
    print(f"Total roads: {total_roads:,}")
    print(f"Roads with null names: {null_roads:,}")
    print(f"Percentage with null names: {null_roads/total_roads*100:.1f}%")
    
    # Check by road category
    print("\nNull names by road category:")
    categories = ['Primary Roads', 'Secondary Roads', 'Local Streets', 'Special Roads']
    
    for category in categories:
        result = supabase.table('roads').select('count', count='exact').eq('road_category', category).is_('fullname', 'null').execute()
        count = result.count
        total_cat = supabase.table('roads').select('count', count='exact').eq('road_category', category).execute().count
        print(f"  {category}: {count:,}/{total_cat:,} ({count/total_cat*100:.1f}%)")
    
    # Show sample of null name roads
    print("\nSample roads with null names:")
    samples = supabase.table('roads').select('linearid, mtfcc, road_category, county_fips').is_('fullname', 'null').limit(10).execute()
    
    for road in samples.data:
        print(f"  LinearID: {road['linearid']}, MTFCC: {road['mtfcc']}, Category: {road['road_category']}")

if __name__ == "__main__":
    check_null_names()