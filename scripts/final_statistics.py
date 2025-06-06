#!/usr/bin/env python3
"""
Final statistics after import completion
"""

from supabase import create_client, Client

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_final_statistics():
    """Get final statistics after import"""
    print("FINAL IMPORT STATISTICS")
    print("="*70)
    
    # Total roads in database
    total_result = supabase.table('roads').select('count', count='exact').execute()
    total_roads = total_result.count
    print(f"\nTotal unique roads in database: {total_roads:,}")
    print(f"Expected from file count: ~5,263,747")
    print(f"Difference (duplicates): {5263747 - total_roads:,} ({(5263747 - total_roads)/5263747*100:.1f}%)")
    
    # Counties processed
    counties_result = supabase.table('roads').select('county_fips').execute()
    unique_counties = len(set(r['county_fips'] for r in counties_result.data))
    print(f"\nCounties processed: {unique_counties}/323")
    
    # States with data
    states_result = supabase.table('roads').select('state_code').execute()
    unique_states = len(set(r['state_code'] for r in states_result.data))
    print(f"States with data: {unique_states}")
    
    # Named vs unnamed
    named_result = supabase.table('roads').select('count', count='exact').neq('fullname', None).execute()
    named_roads = named_result.count
    unnamed_roads = total_roads - named_roads
    
    print(f"\nRoads with names: {named_roads:,} ({named_roads/total_roads*100:.1f}%)")
    print(f"Roads without names: {unnamed_roads:,} ({unnamed_roads/total_roads*100:.1f}%)")
    
    # By category
    print("\n" + "-"*70)
    print("Roads by Category:")
    categories = {
        'Primary Roads': 0,
        'Secondary Roads': 0,
        'Local Streets': 0,
        'Special Roads': 0
    }
    
    for category in categories:
        result = supabase.table('roads').select('count', count='exact').eq('road_category', category).execute()
        categories[category] = result.count
    
    total_by_cat = sum(categories.values())
    for category, count in categories.items():
        print(f"  {category}: {count:,} ({count/total_by_cat*100:.1f}%)")
    
    # Top 10 states by road count
    print("\n" + "-"*70)
    print("Top 10 States by Road Count:")
    
    # This is approximate since we can't do GROUP BY easily
    state_counts = {}
    for row in states_result.data:
        state = row['state_code']
        state_counts[state] = state_counts.get(state, 0) + 1
    
    for i, (state, count) in enumerate(sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i}. {state}: ~{count*1000:,} roads")

if __name__ == "__main__":
    get_final_statistics()