#!/usr/bin/env python3
"""
Fast import with better duplicate handling
"""

import os
import sys
from datetime import datetime
from import_to_supabase import (
    supabase, get_road_category, read_dbf_file,
    STATE_MAPPING, refresh_materialized_view
)

def get_existing_linearids():
    """Get all existing linearids from database"""
    print("Loading existing linearids...")
    existing = set()
    offset = 0
    limit = 1000
    
    while True:
        result = supabase.table('roads').select('linearid').range(offset, offset + limit - 1).execute()
        if not result.data:
            break
        for row in result.data:
            existing.add(row['linearid'])
        offset += limit
        print(f"  Loaded {len(existing)} linearids...", end='\r')
    
    print(f"\n  Total existing linearids: {len(existing)}")
    return existing

def import_roads_fast(county_fips: str, existing_linearids: set):
    """Import roads for a county, skipping existing linearids"""
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    dbf_file = f'tl_2024_{county_fips}_roads.dbf'
    dbf_path = os.path.join(input_dir, dbf_file)
    
    if not os.path.exists(dbf_path):
        return 0
    
    state_fips = county_fips[:2]
    state_code, _ = STATE_MAPPING[state_fips]
    
    # Read DBF file
    records = read_dbf_file(dbf_path)
    
    # Filter out existing linearids
    new_records = []
    skipped = 0
    
    for record in records:
        linearid = record.get('LINEARID', '')
        if linearid in existing_linearids:
            skipped += 1
            continue
            
        new_records.append({
            'linearid': linearid,
            'fullname': record.get('FULLNAME', '') or None,
            'rttyp': record.get('RTTYP', '') or None,
            'mtfcc': record.get('MTFCC', ''),
            'road_category': get_road_category(record.get('MTFCC', '')),
            'county_fips': county_fips,
            'state_code': state_code
        })
        existing_linearids.add(linearid)  # Add to set to avoid duplicates in same run
    
    print(f"  Found {len(new_records)} new roads (skipped {skipped} existing)")
    
    # Insert in batches
    batch_size = 1000
    inserted = 0
    
    for i in range(0, len(new_records), batch_size):
        batch = new_records[i:i + batch_size]
        try:
            supabase.table('roads').insert(batch).execute()
            inserted += len(batch)
            print(f"  Inserted {inserted}/{len(new_records)} records", end='\r')
        except Exception as e:
            print(f"\n  Error: {e}")
    
    print(f"\n  Total inserted: {inserted}")
    return inserted

def main():
    """Fast import with duplicate checking"""
    print("Fast import with duplicate checking...")
    
    # Get all counties
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    all_counties = []
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('_roads.dbf'):
            county_fips = filename.split('_')[2]
            state_fips = county_fips[:2]
            if state_fips in STATE_MAPPING:
                all_counties.append(county_fips)
    
    # Get existing linearids
    existing_linearids = get_existing_linearids()
    
    # Get imported counties
    result = supabase.table('roads').select('county_fips').execute()
    imported_counties = set(row['county_fips'] for row in result.data)
    
    # Find remaining counties
    remaining = [c for c in all_counties if c not in imported_counties]
    print(f"\nCounties to import: {len(remaining)}")
    
    # Import remaining
    start_time = datetime.now()
    total_imported = 0
    
    for idx, county_fips in enumerate(remaining, 1):
        print(f"\nProcessing county {idx}/{len(remaining)}: {county_fips}")
        inserted = import_roads_fast(county_fips, existing_linearids)
        total_imported += inserted
        print(f"Total roads imported: {total_imported:,}")
    
    print(f"\nCompleted in: {datetime.now() - start_time}")
    refresh_materialized_view()

if __name__ == "__main__":
    main()