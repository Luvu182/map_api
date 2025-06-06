#!/usr/bin/env python3
"""
Check details of a specific road by linearid
"""

from supabase import create_client, Client
import sys

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

def check_road(linearid):
    """Check details of a specific road"""
    print(f"Checking road with LinearID: {linearid}")
    print("="*60)
    
    # Get road details
    result = supabase.table('roads').select('*').eq('linearid', str(linearid)).execute()
    
    if not result.data:
        print(f"No road found with LinearID: {linearid}")
        return
        
    road = result.data[0]
    
    # Display details
    print(f"\nRoad Details:")
    print(f"  LinearID: {road['linearid']}")
    print(f"  Full Name: {road['fullname'] or '[No Name]'}")
    print(f"  Road Type (RTTYP): {road['rttyp'] or 'N/A'}")
    print(f"  MTFCC Code: {road['mtfcc']}")
    print(f"  MTFCC Description: {MTFCC_DESCRIPTIONS.get(road['mtfcc'], 'Unknown')}")
    print(f"  Road Category: {road['road_category']}")
    print(f"  County FIPS: {road['county_fips']}")
    print(f"  State Code: {road['state_code']}")
    
    # Get county name
    county_result = supabase.table('counties').select('*').eq('county_fips', road['county_fips']).execute()
    if county_result.data:
        print(f"  County: {county_result.data[0].get('county_name', 'Unknown')}")
    
    # Get state name
    state_result = supabase.table('states').select('*').eq('state_code', road['state_code']).execute()
    if state_result.data:
        print(f"  State: {state_result.data[0]['state_name']}")
    
    # RTTYP meanings
    print(f"\nRoad Type Details:")
    rttyp_meanings = {
        'C': 'Connector',
        'E': 'Extension', 
        'I': 'Interstate',
        'M': 'Common name',
        'O': 'Other',
        'S': 'State recognized',
        'U': 'U.S. route'
    }
    if road['rttyp']:
        print(f"  RTTYP '{road['rttyp']}' means: {rttyp_meanings.get(road['rttyp'], 'Unknown')}")

if __name__ == "__main__":
    # Check if linearid provided
    if len(sys.argv) > 1:
        linearid = sys.argv[1]
    else:
        linearid = "112969"  # Default
    
    check_road(linearid)