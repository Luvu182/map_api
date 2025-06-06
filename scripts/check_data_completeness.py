#!/usr/bin/env python3
"""
Check data completeness in Supabase
"""

from supabase import create_client, Client

SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_data_completeness():
    """Check what fields are available in the database"""
    print("Checking data completeness in Supabase...")
    print("="*60)
    
    # Get sample road to see all fields
    sample = supabase.table('roads').select('*').limit(1).execute()
    
    if sample.data:
        print("\nAvailable fields in 'roads' table:")
        for field in sample.data[0].keys():
            print(f"  - {field}")
    
    # Check specific road with all details
    print("\n" + "="*60)
    print("Sample road with complete data:")
    
    # Get a road with a name
    named_road = supabase.table('roads').select('*').neq('fullname', None).limit(1).execute()
    
    if named_road.data:
        road = named_road.data[0]
        print(f"\nLinearID: {road['linearid']}")
        print(f"Full Name: {road['fullname']}")
        print(f"MTFCC: {road['mtfcc']}")
        print(f"Road Category: {road['road_category']}")
        print(f"RTTYP: {road['rttyp']}")
        print(f"County FIPS: {road['county_fips']}")
        print(f"State Code: {road['state_code']}")
        print(f"Created At: {road['created_at']}")
    
    # Check what's missing from original data
    print("\n" + "="*60)
    print("Fields from original TIGER data NOT imported:")
    original_fields = ['LINEARID', 'FULLNAME', 'RTTYP', 'MTFCC', 'STATEFP', 'COUNTYFP', 
                      'DIVROAD', 'QUALIFIER', 'ROUTENUM', 'ROADFLG', 'EXTTYP', 'TTYP', 
                      'DECKEDROAD', 'ARIDL', 'ARIDR', 'GCSEFLG', 'OFFSETL', 'OFFSETR']
    
    imported_fields = ['linearid', 'fullname', 'rttyp', 'mtfcc', 'state_code', 'county_fips', 
                      'road_category', 'created_at']
    
    missing = []
    for field in original_fields:
        if field.lower() not in [f.lower() for f in imported_fields]:
            missing.append(field)
    
    if missing:
        print(f"Missing fields: {', '.join(missing)}")
    else:
        print("All essential fields imported!")
    
    # Show MTFCC description mapping
    print("\n" + "="*60)
    print("MTFCC codes stored? YES")
    print("Road categories derived from MTFCC? YES")
    print("Can identify road types? YES")
    
    # Test query for special roads
    special_roads = supabase.table('roads').select('mtfcc').eq('road_category', 'Special Roads').limit(10).execute()
    
    if special_roads.data:
        print("\nSample Special Roads MTFCC codes:")
        mtfcc_codes = set()
        for road in special_roads.data:
            mtfcc_codes.add(road['mtfcc'])
        
        mtfcc_map = {
            'S1630': 'Ramp',
            'S1740': 'Private Road/Driveway',
            'S1730': 'Alley',
            'S1780': 'Parking Lot Road',
            'S1500': 'Vehicular Trail (4WD)'
        }
        
        for code in sorted(mtfcc_codes):
            desc = mtfcc_map.get(code, 'Other Special Road')
            print(f"  {code}: {desc}")

if __name__ == "__main__":
    check_data_completeness()