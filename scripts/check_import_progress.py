#!/usr/bin/env python3
"""
Check import progress and statistics
"""

from supabase import create_client, Client

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_progress():
    """Check current import progress"""
    print("Checking import progress...\n")
    
    # Count roads
    result = supabase.table('roads').select('count', count='exact').execute()
    road_count = result.count
    print(f"Roads imported: {road_count:,}")
    
    # Count by state
    result = supabase.table('roads').select('state_code').execute()
    states = {}
    for row in result.data:
        state = row['state_code']
        states[state] = states.get(state, 0) + 1
    
    print(f"\nStates with data: {len(states)}")
    print("\nTop 5 states by road count:")
    for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {state}: {count:,}")
    
    # Count counties with data
    result = supabase.table('roads').select('county_fips', count='exact').execute()
    print(f"\nCounties processed: {len(set(r['county_fips'] for r in result.data))}/323")
    
    print("\nExpected total: ~5,263,747 roads")
    print(f"Progress: {road_count/5263747*100:.1f}%")

if __name__ == "__main__":
    check_progress()