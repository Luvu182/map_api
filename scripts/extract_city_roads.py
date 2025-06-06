#!/usr/bin/env python3
"""
Extract all road names for specific cities
"""

import struct
import csv
import os
from collections import defaultdict

# Major city to county mapping
CITY_COUNTY_MAP = {
    'New York': {'name': 'New York City', 'counties': ['36061', '36047', '36081', '36005', '36085']},
    'Los Angeles': {'name': 'Los Angeles', 'counties': ['06037']},
    'Chicago': {'name': 'Chicago', 'counties': ['17031']},
    'Houston': {'name': 'Houston', 'counties': ['48201', '48157', '48039']},
    'Phoenix': {'name': 'Phoenix', 'counties': ['04013']},
    'San Francisco': {'name': 'San Francisco', 'counties': ['06075']},
    'Seattle': {'name': 'Seattle', 'counties': ['53033']},
    'Boston': {'name': 'Boston', 'counties': ['25025']},
    'Miami': {'name': 'Miami', 'counties': ['12086']}
}

def read_dbf_file(dbf_path):
    """Read all records from DBF file"""
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
        
        # Read all records
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

def extract_city_roads(city_key):
    """Extract all roads for a specific city"""
    city_info = CITY_COUNTY_MAP[city_key]
    city_name = city_info['name']
    counties = city_info['counties']
    
    print(f"\nExtracting roads for {city_name}...")
    print(f"Counties: {', '.join(counties)}")
    
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    output_dir = '../processed_data/city_roads'
    os.makedirs(output_dir, exist_ok=True)
    
    all_roads = []
    road_stats = defaultdict(int)
    
    for county_fips in counties:
        dbf_file = f'tl_2024_{county_fips}_roads.dbf'
        dbf_path = os.path.join(input_dir, dbf_file)
        
        if not os.path.exists(dbf_path):
            print(f"  Warning: {dbf_file} not found")
            continue
            
        print(f"  Processing county {county_fips}...")
        records = read_dbf_file(dbf_path)
        
        for record in records:
            road_category = get_road_category(record.get('MTFCC', ''))
            
            road_info = {
                'city': city_name,
                'county_fips': county_fips,
                'linearid': record.get('LINEARID', ''),
                'fullname': record.get('FULLNAME', ''),
                'rttyp': record.get('RTTYP', ''),
                'mtfcc': record.get('MTFCC', ''),
                'road_category': road_category
            }
            
            all_roads.append(road_info)
            road_stats[road_category] += 1
    
    # Save to CSV
    output_file = os.path.join(output_dir, f'{city_key.lower()}_roads.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if all_roads:
            writer = csv.DictWriter(f, fieldnames=all_roads[0].keys())
            writer.writeheader()
            writer.writerows(all_roads)
    
    print(f"\nSaved {len(all_roads)} roads to {output_file}")
    print("\nRoad type distribution:")
    for road_type, count in sorted(road_stats.items()):
        print(f"  {road_type}: {count:,}")
    
    # Show sample roads
    print("\nSample roads with names:")
    named_roads = [r for r in all_roads if r['fullname']]
    for road in named_roads[:10]:
        print(f"  - {road['fullname']} ({road['road_category']})")
    
    return all_roads

def main():
    """Extract roads for major cities"""
    print("Available cities:")
    for key, info in CITY_COUNTY_MAP.items():
        print(f"  {key}: {info['name']}")
    
    # Extract for a few major cities
    for city in ['New York', 'Los Angeles', 'San Francisco']:
        extract_city_roads(city)
        print("\n" + "="*50)

if __name__ == "__main__":
    main()