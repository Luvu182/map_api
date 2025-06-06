#!/usr/bin/env python3
"""
Analyze types of unnamed roads to understand commercial potential
"""

from supabase import create_client, Client
from collections import defaultdict

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# MTFCC codes and their meanings
MTFCC_DESCRIPTIONS = {
    'S1100': 'Primary Road (Interstate/Highway)',
    'S1200': 'Secondary Road (US/State Highway)', 
    'S1400': 'Local Neighborhood Road/City Street',
    'S1500': 'Vehicular Trail (4WD)',
    'S1630': 'Ramp',
    'S1640': 'Service Drive/Frontage Road',
    'S1710': 'Walkway/Pedestrian Trail',
    'S1720': 'Stairway',
    'S1730': 'Alley',
    'S1740': 'Private Road/Driveway',
    'S1750': 'Internal Census Use',
    'S1780': 'Parking Lot Road',
    'S1820': 'Bike Path/Trail',
    'S1830': 'Bridle Path'
}

def analyze_unnamed_roads():
    """Analyze unnamed roads by type"""
    print("Analyzing unnamed roads by type...\n")
    
    # Get unnamed roads grouped by MTFCC
    print("Fetching unnamed roads data...")
    offset = 0
    limit = 1000
    mtfcc_counts = defaultdict(int)
    
    while True:
        result = supabase.table('roads').select('mtfcc').is_('fullname', 'null').range(offset, offset + limit - 1).execute()
        if not result.data:
            break
            
        for road in result.data:
            mtfcc_counts[road['mtfcc']] += 1
        
        offset += limit
        if offset % 10000 == 0:
            print(f"  Processed {offset} records...")
    
    # Display results
    print("\nUnnamed roads by type:")
    print("-" * 70)
    print(f"{'MTFCC':<8} {'Description':<45} {'Count':>10} {'%':>5}")
    print("-" * 70)
    
    total = sum(mtfcc_counts.values())
    commercial_potential = 0
    
    for mtfcc, count in sorted(mtfcc_counts.items(), key=lambda x: x[1], reverse=True):
        desc = MTFCC_DESCRIPTIONS.get(mtfcc, 'Unknown')
        pct = count / total * 100
        print(f"{mtfcc:<8} {desc:<45} {count:>10,} {pct:>5.1f}%")
        
        # Count roads with commercial potential
        if mtfcc in ['S1400', 'S1730', 'S1640']:  # Local streets, alleys, service roads
            commercial_potential += count
    
    print("-" * 70)
    print(f"{'TOTAL':<54} {total:>10,} 100.0%")
    
    print(f"\nRoads with commercial potential (Local/Alley/Service): {commercial_potential:,} ({commercial_potential/total*100:.1f}%)")
    
    # Check specific cities
    print("\n\nUnnamed roads in major commercial cities:")
    cities = ['New York City', 'Los Angeles', 'Chicago', 'San Francisco']
    
    for city in cities:
        # Get unnamed roads in city
        result = supabase.rpc('get_city_unnamed_roads_count', {'city_name': city}).execute()
        if result.data:
            print(f"  {city}: {result.data[0]['count']:,} unnamed roads")

if __name__ == "__main__":
    analyze_unnamed_roads()