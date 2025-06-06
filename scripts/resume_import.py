#!/usr/bin/env python3
"""
Resume import from where it stopped (county 01125)
"""

import os
import sys
from datetime import datetime
from import_to_supabase import (
    supabase, import_roads_for_county, refresh_materialized_view,
    STATE_MAPPING
)

def get_imported_counties():
    """Get list of counties already imported"""
    result = supabase.table('roads').select('county_fips').execute()
    imported = set()
    for row in result.data:
        imported.add(row['county_fips'])
    return imported

def resume_import():
    """Resume import from where it stopped"""
    print("Checking already imported counties...")
    
    # Get all counties from files
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    all_counties = []
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('_roads.dbf'):
            county_fips = filename.split('_')[2]
            state_fips = county_fips[:2]
            if state_fips in STATE_MAPPING:
                all_counties.append(county_fips)
    
    # Get imported counties
    imported = get_imported_counties()
    print(f"Already imported: {len(imported)} counties")
    
    # Find remaining counties
    remaining = [c for c in all_counties if c not in imported]
    print(f"Remaining to import: {len(remaining)} counties")
    
    if not remaining:
        print("All counties already imported!")
        return
    
    # Start importing remaining counties
    print("\nResuming import...")
    start_time = datetime.now()
    total_imported = len(imported) * 15000  # rough estimate
    
    for idx, county_fips in enumerate(remaining, 1):
        print(f"\n  Processing remaining county {idx}/{len(remaining)}: {county_fips}")
        inserted = import_roads_for_county(county_fips)
        total_imported += inserted
        print(f"  Total roads imported so far: {total_imported:,}")
    
    print("\nImport completed!")
    print(f"Duration: {datetime.now() - start_time}")
    
    # Refresh materialized view
    refresh_materialized_view()

if __name__ == "__main__":
    resume_import()