#!/usr/bin/env python3
"""
Get comprehensive road statistics
"""

from supabase import create_client, Client

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_road_statistics():
    """Get comprehensive road statistics"""
    print("Road Statistics Summary")
    print("=" * 60)
    
    # Total roads imported so far
    total_result = supabase.table('roads').select('count', count='exact').execute()
    total_roads = total_result.count
    print(f"\nTotal roads imported: {total_roads:,}")
    
    # Roads with names
    named_result = supabase.table('roads').select('count', count='exact').neq('fullname', None).execute()
    named_roads = named_result.count
    
    # Roads without names
    unnamed_result = supabase.table('roads').select('count', count='exact').is_('fullname', 'null').execute()
    unnamed_roads = unnamed_result.count
    
    print(f"\nRoads WITH names: {named_roads:,} ({named_roads/total_roads*100:.1f}%)")
    print(f"Roads WITHOUT names: {unnamed_roads:,} ({unnamed_roads/total_roads*100:.1f}%)")
    
    # Breakdown by category
    print("\n" + "=" * 60)
    print("Breakdown by Road Category:")
    print("-" * 60)
    
    categories = ['Primary Roads', 'Secondary Roads', 'Local Streets', 'Special Roads']
    
    for category in categories:
        # Total in category
        cat_total = supabase.table('roads').select('count', count='exact').eq('road_category', category).execute().count
        
        # Named in category
        cat_named = supabase.table('roads').select('count', count='exact').eq('road_category', category).neq('fullname', None).execute().count
        
        # Unnamed in category
        cat_unnamed = cat_total - cat_named
        
        print(f"\n{category}:")
        print(f"  Total: {cat_total:,}")
        print(f"  With names: {cat_named:,} ({cat_named/cat_total*100:.1f}%)")
        print(f"  Without names: {cat_unnamed:,} ({cat_unnamed/cat_total*100:.1f}%)")
    
    # Progress update
    print("\n" + "=" * 60)
    print("Import Progress:")
    print(f"Counties processed: {len(set(r['county_fips'] for r in supabase.table('roads').select('county_fips').execute().data))}/323")
    print(f"Expected total roads: ~5,263,747")
    print(f"Current progress: {total_roads/5263747*100:.1f}%")
    
    # Estimated final numbers
    if total_roads > 0:
        unnamed_rate = unnamed_roads / total_roads
        print(f"\nEstimated when complete:")
        print(f"  Total roads: ~5,263,747")
        print(f"  Roads with names: ~{int(5263747 * (1 - unnamed_rate)):,}")
        print(f"  Roads without names: ~{int(5263747 * unnamed_rate):,}")

if __name__ == "__main__":
    get_road_statistics()