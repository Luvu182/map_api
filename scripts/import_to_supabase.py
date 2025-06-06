#!/usr/bin/env python3
"""
Import road data to Supabase database
"""

import os
import sys
import json
import struct
from datetime import datetime
from supabase import create_client, Client
import time
from typing import List, Dict

# Supabase configuration
SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# State mapping
STATE_MAPPING = {
    '01': ('AL', 'Alabama'), '02': ('AK', 'Alaska'), '04': ('AZ', 'Arizona'),
    '05': ('AR', 'Arkansas'), '06': ('CA', 'California'), '08': ('CO', 'Colorado'),
    '09': ('CT', 'Connecticut'), '10': ('DE', 'Delaware'), '11': ('DC', 'District of Columbia'),
    '12': ('FL', 'Florida'), '13': ('GA', 'Georgia'), '15': ('HI', 'Hawaii'),
    '16': ('ID', 'Idaho'), '17': ('IL', 'Illinois'), '18': ('IN', 'Indiana'),
    '19': ('IA', 'Iowa'), '20': ('KS', 'Kansas'), '21': ('KY', 'Kentucky'),
    '22': ('LA', 'Louisiana'), '23': ('ME', 'Maine'), '24': ('MD', 'Maryland'),
    '25': ('MA', 'Massachusetts'), '26': ('MI', 'Michigan'), '27': ('MN', 'Minnesota'),
    '28': ('MS', 'Mississippi'), '29': ('MO', 'Missouri'), '30': ('MT', 'Montana'),
    '31': ('NE', 'Nebraska'), '32': ('NV', 'Nevada'), '33': ('NH', 'New Hampshire'),
    '34': ('NJ', 'New Jersey'), '35': ('NM', 'New Mexico'), '36': ('NY', 'New York'),
    '37': ('NC', 'North Carolina'), '38': ('ND', 'North Dakota'), '39': ('OH', 'Ohio'),
    '40': ('OK', 'Oklahoma'), '41': ('OR', 'Oregon'), '42': ('PA', 'Pennsylvania'),
    '44': ('RI', 'Rhode Island'), '45': ('SC', 'South Carolina'), '46': ('SD', 'South Dakota'),
    '47': ('TN', 'Tennessee'), '48': ('TX', 'Texas'), '49': ('UT', 'Utah'),
    '50': ('VT', 'Vermont'), '51': ('VA', 'Virginia'), '53': ('WA', 'Washington'),
    '54': ('WV', 'West Virginia'), '55': ('WI', 'Wisconsin'), '56': ('WY', 'Wyoming')
}

# Major cities mapping
CITY_MAPPING = {
    'New York': {'counties': ['36061', '36047', '36081', '36005', '36085'], 'state': 'NY'},
    'Los Angeles': {'counties': ['06037'], 'state': 'CA'},
    'Chicago': {'counties': ['17031'], 'state': 'IL'},
    'Houston': {'counties': ['48201', '48157', '48039'], 'state': 'TX'},
    'Phoenix': {'counties': ['04013'], 'state': 'AZ'},
    'Philadelphia': {'counties': ['42101'], 'state': 'PA'},
    'San Antonio': {'counties': ['48029'], 'state': 'TX'},
    'San Diego': {'counties': ['06073'], 'state': 'CA'},
    'Dallas': {'counties': ['48113'], 'state': 'TX'},
    'San Jose': {'counties': ['06085'], 'state': 'CA'},
    'Austin': {'counties': ['48453'], 'state': 'TX'},
    'San Francisco': {'counties': ['06075'], 'state': 'CA'},
    'Seattle': {'counties': ['53033'], 'state': 'WA'},
    'Boston': {'counties': ['25025'], 'state': 'MA'},
    'Miami': {'counties': ['12086'], 'state': 'FL'}
}

def get_road_category(mtfcc):
    """Map MTFCC to road category"""
    if mtfcc == 'S1100':
        return 'Primary Roads'
    elif mtfcc == 'S1200':
        return 'Secondary Roads'
    elif mtfcc == 'S1400':
        return 'Local Streets'
    else:
        return 'Special Roads'

def read_dbf_file(dbf_path):
    """Read DBF file and return records"""
    records = []
    
    with open(dbf_path, 'rb') as f:
        # Read header
        header = f.read(32)
        num_records = struct.unpack('<I', header[4:8])[0]
        header_length = struct.unpack('<H', header[8:10])[0]
        record_length = struct.unpack('<H', header[10:12])[0]
        
        # Read field descriptors
        fields = []
        num_fields = (header_length - 32 - 1) // 32
        
        for i in range(num_fields):
            field_data = f.read(32)
            name = field_data[0:11].decode('utf-8').strip('\x00').strip()
            field_type = field_data[11:12].decode('utf-8')
            length = struct.unpack('B', field_data[16:17])[0]
            fields.append({'name': name, 'type': field_type, 'length': length})
        
        f.read(1)  # Skip terminator
        
        # Read records
        for i in range(num_records):
            record_data = f.read(record_length)
            if not record_data:
                break
                
            record = {}
            offset = 1  # Skip deletion flag
            
            for field in fields:
                value = record_data[offset:offset + field['length']]
                try:
                    value = value.decode('utf-8').strip()
                except:
                    value = ''
                record[field['name']] = value
                offset += field['length']
                
            records.append(record)
    
    return records

def batch_insert(table: str, data: List[Dict], batch_size: int = 1000):
    """Insert data in batches"""
    total = len(data)
    inserted = 0
    skipped = 0
    
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]
        try:
            result = supabase.table(table).insert(batch).execute()
            inserted += len(batch)
            print(f"  Inserted {inserted}/{total} records", end='\r')
        except Exception as e:
            if 'duplicate key' in str(e):
                print(f"\n  Found duplicates in batch, inserting one by one...")
                # Try inserting one by one for this batch
                for idx, record in enumerate(batch):
                    try:
                        supabase.table(table).insert(record).execute()
                        inserted += 1
                        if idx % 100 == 0:
                            print(f"    Progress: {idx}/{len(batch)} records in batch, Total: {inserted}/{total}", end='\r')
                    except Exception as e2:
                        if 'duplicate key' in str(e2):
                            skipped += 1
                        else:
                            pass  # Skip other errors silently
            else:
                print(f"\n  Error inserting batch: {e}")
    
    print(f"\n  Total inserted: {inserted}/{total} (skipped {skipped} duplicates)")
    return inserted

def import_states():
    """Import state data"""
    print("\n1. Importing states...")
    states = []
    for state_fips, (code, name) in STATE_MAPPING.items():
        states.append({
            'state_code': code,
            'state_name': name
        })
    
    batch_insert('states', states)
    print(f"  Imported {len(states)} states")

def import_counties():
    """Import county data from processed files"""
    print("\n2. Importing counties...")
    counties = set()
    
    # Get all county FIPS from downloaded files
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    for filename in os.listdir(input_dir):
        if filename.endswith('_roads.dbf'):
            county_fips = filename.split('_')[2]
            state_fips = county_fips[:2]
            if state_fips in STATE_MAPPING:
                counties.add(county_fips)
    
    # Create county records
    county_records = []
    for county_fips in sorted(counties):
        state_fips = county_fips[:2]
        state_code, _ = STATE_MAPPING[state_fips]
        county_records.append({
            'county_fips': county_fips,
            'state_code': state_code
        })
    
    batch_insert('counties', county_records)
    print(f"  Imported {len(county_records)} counties")
    return counties

def import_cities():
    """Import city data"""
    print("\n3. Importing cities and city-county mappings...")
    
    # Insert cities
    city_records = []
    city_id_map = {}
    
    for idx, (city_name, info) in enumerate(CITY_MAPPING.items(), 1):
        city_records.append({
            'city_id': idx,
            'city_name': city_name,
            'state_code': info['state']
        })
        city_id_map[city_name] = idx
    
    batch_insert('cities', city_records)
    
    # Insert city-county mappings
    mappings = []
    for city_name, info in CITY_MAPPING.items():
        city_id = city_id_map[city_name]
        for county_fips in info['counties']:
            mappings.append({
                'city_id': city_id,
                'county_fips': county_fips
            })
    
    batch_insert('city_counties', mappings)
    print(f"  Imported {len(city_records)} cities with {len(mappings)} county mappings")

def import_roads_for_county(county_fips: str, batch_size: int = 5000):
    """Import roads for a single county"""
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    dbf_file = f'tl_2024_{county_fips}_roads.dbf'
    dbf_path = os.path.join(input_dir, dbf_file)
    
    if not os.path.exists(dbf_path):
        return 0
    
    state_fips = county_fips[:2]
    state_code, _ = STATE_MAPPING[state_fips]
    
    # Read DBF file
    records = read_dbf_file(dbf_path)
    
    # Prepare road records
    road_records = []
    for record in records:
        road_records.append({
            'linearid': record.get('LINEARID', ''),
            'fullname': record.get('FULLNAME', '') or None,
            'rttyp': record.get('RTTYP', '') or None,
            'mtfcc': record.get('MTFCC', ''),
            'road_category': get_road_category(record.get('MTFCC', '')),
            'county_fips': county_fips,
            'state_code': state_code
        })
    
    # Insert in batches
    inserted = batch_insert('roads', road_records, batch_size)
    return inserted

def import_all_roads(counties: set):
    """Import all road data"""
    print("\n4. Importing road data...")
    print("  This will take some time for 5.2M records...")
    
    total_inserted = 0
    county_list = sorted(list(counties))
    
    for idx, county_fips in enumerate(county_list, 1):
        print(f"\n  Processing county {idx}/{len(county_list)}: {county_fips}")
        inserted = import_roads_for_county(county_fips)
        total_inserted += inserted
        print(f"  Total roads imported so far: {total_inserted:,}")
        
        # Small delay to avoid rate limiting
        if idx % 10 == 0:
            time.sleep(1)
    
    print(f"\n  Total roads imported: {total_inserted:,}")

def refresh_materialized_view():
    """Refresh the materialized view for statistics"""
    print("\n5. Refreshing statistics view...")
    try:
        supabase.rpc('refresh_materialized_view', {'view_name': 'road_statistics'}).execute()
        print("  Statistics view refreshed")
    except:
        print("  Note: Refresh materialized view manually in Supabase SQL editor:")
        print("  REFRESH MATERIALIZED VIEW road_statistics;")

def main():
    """Main import process"""
    print("Starting Supabase import process...")
    print(f"Target: {SUPABASE_URL}")
    
    start_time = datetime.now()
    
    try:
        # Import in order
        import_states()
        counties = import_counties()
        import_cities()
        
        # Import roads (this is the big one)
        import_all_roads(counties)
        
        # Refresh statistics
        refresh_materialized_view()
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\nImport completed in: {duration}")
        
    except Exception as e:
        print(f"\nError during import: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()