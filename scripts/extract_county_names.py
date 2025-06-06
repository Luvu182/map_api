#!/usr/bin/env python3
"""
Extract county FIPS codes and names from TIGER XML metadata files
"""

import os
import xml.etree.ElementTree as ET
import csv
import json
import re

def extract_county_info_from_xml(xml_path):
    """Extract county name and FIPS from XML metadata"""
    try:
        # Extract filename to get FIPS code
        filename = os.path.basename(xml_path)
        match = re.match(r'tl_2024_(\d{5})_roads\.shp\.iso\.xml', filename)
        if not match:
            return None
        
        fips_code = match.group(1)
        state_fips = fips_code[:2]
        
        # Read file and search for county info using regex
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the title line containing county info
        # Pattern: "TIGER/Line Shapefile, Current, County, Baltimore County, MD, All Roads"
        title_pattern = r'<gco:CharacterString>TIGER/Line Shapefile[^<]*County,\s*([^,]+),\s*([A-Z]{2}),\s*All Roads</gco:CharacterString>'
        match = re.search(title_pattern, content)
        
        if match:
            county_with_suffix = match.group(1).strip()
            state_abbr = match.group(2).strip()
            
            # Remove "County" suffix if present
            county_name = county_with_suffix
            if county_name.endswith(' County'):
                county_name = county_name[:-7]
            
            return {
                'fips': fips_code,
                'state_fips': state_fips,
                'county_name': county_name,
                'state_abbr': state_abbr
            }
    
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
    
    return None

def main():
    input_dir = '../raw_data/shapefiles/TIGER_Roads/extracted'
    output_dir = '../processed_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all XML files
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.shp.iso.xml')]
    
    print(f"Found {len(xml_files)} XML files to process")
    
    counties = []
    errors = []
    
    for xml_file in sorted(xml_files):
        xml_path = os.path.join(input_dir, xml_file)
        info = extract_county_info_from_xml(xml_path)
        
        if info:
            counties.append(info)
            print(f"Processed: {info['fips']} - {info['county_name']}, {info['state_abbr']}")
        else:
            errors.append(xml_file)
    
    print(f"\nSuccessfully extracted {len(counties)} counties")
    
    # Save as CSV
    csv_path = os.path.join(output_dir, 'county_fips_names.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['fips', 'state_fips', 'county_name', 'state_abbr'])
        writer.writeheader()
        writer.writerows(counties)
    
    print(f"Saved CSV to: {csv_path}")
    
    # Save as JSON
    json_path = os.path.join(output_dir, 'county_fips_names.json')
    with open(json_path, 'w') as f:
        json.dump(counties, f, indent=2)
    
    print(f"Saved JSON to: {json_path}")
    
    # Create a mapping dictionary
    mapping = {item['fips']: f"{item['county_name']}, {item['state_abbr']}" for item in counties}
    mapping_path = os.path.join(output_dir, 'county_fips_mapping.json')
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Saved mapping to: {mapping_path}")
    
    if errors:
        print(f"\nFailed to process {len(errors)} files:")
        for error in errors[:5]:
            print(f"  - {error}")

if __name__ == "__main__":
    main()