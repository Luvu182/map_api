#!/usr/bin/env python3
"""
Process all 323 counties and create complete hierarchy
Process in batches to avoid memory issues
"""

import os
import csv
import json
import struct
import time
from collections import defaultdict

# State FIPS to name mapping
STATE_NAMES = {
    '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
    '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
    '11': 'District of Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
    '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa',
    '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
    '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
    '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
    '32': 'Nevada', '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico',
    '36': 'New York', '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio',
    '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
    '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas',
    '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
    '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
}

# DBF reading functions
def read_dbf_header(f):
    header = f.read(32)
    num_records = struct.unpack('<I', header[4:8])[0]
    header_length = struct.unpack('<H', header[8:10])[0]
    record_length = struct.unpack('<H', header[10:12])[0]
    return num_records, header_length, record_length

def read_dbf_fields(f, header_length):
    fields = []
    num_fields = (header_length - 32 - 1) // 32
    for i in range(num_fields):
        field_data = f.read(32)
        name = field_data[0:11].decode('utf-8').strip('\x00').strip()
        field_type = field_data[11:12].decode('utf-8')
        length = struct.unpack('B', field_data[16:17])[0]
        fields.append({'name': name, 'type': field_type, 'length': length})
    f.read(1)  # Skip terminator
    return fields

def read_dbf_records(f, fields, num_records, record_length):
    records = []
    for i in range(num_records):
        if i % 10000 == 0 and i > 0:
            print(f"    Read {i}/{num_records} records...")
        
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

def process_county_batch(dbf_files, start_idx, end_idx, input_dir, output_dir):
    """Process a batch of counties"""
    batch_data = {
        'counties_processed': 0,
        'total_roads': 0,
        'summary': defaultdict(lambda: defaultdict(int)),
        'errors': []
    }
    
    for idx in range(start_idx, min(end_idx, len(dbf_files))):
        dbf_file = dbf_files[idx]
        county_fips = dbf_file.split('_')[2]
        state_fips = county_fips[:2]
        state_name = STATE_NAMES.get(state_fips, f"State {state_fips}")
        
        print(f"  [{idx+1}/{len(dbf_files)}] Processing {state_name} - County {county_fips}...")
        
        try:
            dbf_path = os.path.join(input_dir, dbf_file)
            
            with open(dbf_path, 'rb') as f:
                num_records, header_length, record_length = read_dbf_header(f)
                fields = read_dbf_fields(f, header_length)
                
                # Process in chunks to save memory
                chunk_size = 5000
                road_categories = defaultdict(int)
                
                for chunk_start in range(0, num_records, chunk_size):
                    f.seek(header_length + chunk_start * record_length)
                    chunk_records = read_dbf_records(f, fields, 
                                                   min(chunk_size, num_records - chunk_start), 
                                                   record_length)
                    
                    for record in chunk_records:
                        mtfcc = record.get('MTFCC', '')
                        road_category = get_road_category(mtfcc)
                        road_categories[road_category] += 1
                        batch_data['total_roads'] += 1
                
                # Update summary
                for category, count in road_categories.items():
                    batch_data['summary'][f"{state_name}|{county_fips}"][category] = count
                
                batch_data['counties_processed'] += 1
                
        except Exception as e:
            error_msg = f"Error processing {dbf_file}: {str(e)}"
            print(f"    {error_msg}")
            batch_data['errors'].append(error_msg)
    
    return batch_data

def main():
    start_time = time.time()
    
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    output_dir = '../processed_data/hierarchy'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all DBF files
    dbf_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.dbf')])
    total_counties = len(dbf_files)
    
    print(f"Found {total_counties} counties to process")
    print("Processing in batches of 50 counties...")
    
    # Process in batches
    batch_size = 50
    all_summaries = {}
    total_roads = 0
    all_errors = []
    
    for batch_start in range(0, total_counties, batch_size):
        batch_end = min(batch_start + batch_size, total_counties)
        print(f"\nBatch {batch_start//batch_size + 1}: Counties {batch_start+1}-{batch_end}")
        
        batch_data = process_county_batch(dbf_files, batch_start, batch_end, input_dir, output_dir)
        
        # Merge results
        all_summaries.update(batch_data['summary'])
        total_roads += batch_data['total_roads']
        all_errors.extend(batch_data['errors'])
        
        print(f"  Batch complete: {batch_data['counties_processed']} counties, {batch_data['total_roads']:,} roads")
    
    # Create final summary
    print("\nCreating final summary...")
    
    # Organize by state
    state_summaries = defaultdict(lambda: {
        'counties': defaultdict(dict),
        'total_counties': 0,
        'total_roads': 0,
        'road_types': defaultdict(int)
    })
    
    for key, road_types in all_summaries.items():
        state_name, county_fips = key.split('|')
        state_summaries[state_name]['counties'][county_fips] = road_types
        state_summaries[state_name]['total_counties'] += 1
        
        for category, count in road_types.items():
            state_summaries[state_name]['total_roads'] += count
            state_summaries[state_name]['road_types'][category] += count
    
    # Save comprehensive summary
    summary = {
        'processing_time': time.time() - start_time,
        'total_counties': len(all_summaries),
        'total_roads': total_roads,
        'errors': all_errors,
        'states': {}
    }
    
    # Convert defaultdicts to regular dicts for JSON
    for state, data in state_summaries.items():
        summary['states'][state] = {
            'total_counties': data['total_counties'],
            'total_roads': data['total_roads'],
            'road_types': dict(data['road_types']),
            'counties': dict(data['counties'])
        }
    
    # Save JSON summary
    json_path = os.path.join(output_dir, 'complete_hierarchy_summary.json')
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSaved JSON summary to: {json_path}")
    
    # Save CSV summary by state
    csv_path = os.path.join(output_dir, 'state_road_summary.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['state', 'counties', 'total_roads', 'primary', 'secondary', 'local', 'special'])
        
        for state, data in sorted(summary['states'].items()):
            writer.writerow([
                state,
                data['total_counties'],
                data['total_roads'],
                data['road_types'].get('Primary Roads', 0),
                data['road_types'].get('Secondary Roads', 0),
                data['road_types'].get('Local Streets', 0),
                data['road_types'].get('Special Roads', 0)
            ])
    
    print(f"Saved CSV summary to: {csv_path}")
    
    # Save detailed county CSV
    county_csv_path = os.path.join(output_dir, 'county_road_details.csv')
    with open(county_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['state', 'county_fips', 'total_roads', 'primary', 'secondary', 'local', 'special'])
        
        for state, state_data in sorted(summary['states'].items()):
            for county, road_types in sorted(state_data['counties'].items()):
                total = sum(road_types.values())
                writer.writerow([
                    state,
                    county,
                    total,
                    road_types.get('Primary Roads', 0),
                    road_types.get('Secondary Roads', 0),
                    road_types.get('Local Streets', 0),
                    road_types.get('Special Roads', 0)
                ])
    
    print(f"Saved county details to: {county_csv_path}")
    
    # Print final statistics
    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    print(f"Total time: {summary['processing_time']:.1f} seconds")
    print(f"Counties processed: {summary['total_counties']}")
    print(f"Total roads: {summary['total_roads']:,}")
    
    if summary['errors']:
        print(f"\nErrors encountered: {len(summary['errors'])}")
        for error in summary['errors'][:5]:
            print(f"  - {error}")
    
    # Road type totals
    road_type_totals = defaultdict(int)
    for state_data in summary['states'].values():
        for road_type, count in state_data['road_types'].items():
            road_type_totals[road_type] += count
    
    print("\nRoad type distribution:")
    for road_type, count in sorted(road_type_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / summary['total_roads']) * 100
        print(f"  {road_type}: {count:,} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()