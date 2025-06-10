#!/usr/bin/env python3
"""Check osm_businesses table schema and state_code column"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query

# Check columns in osm_businesses table
query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'osm_businesses' 
    ORDER BY ordinal_position
"""
print("Columns in osm_businesses table:")
columns = execute_query(query)
for col in columns:
    print(f"  - {col['column_name']}: {col['data_type']}")

# Check if state_code exists and has values
if any(col['column_name'] == 'state_code' for col in columns):
    query2 = """
        SELECT 
            COUNT(*) as total,
            COUNT(state_code) as with_state_code,
            COUNT(DISTINCT state_code) as unique_states
        FROM osm_businesses
    """
    result = execute_query(query2, fetch_one=True)
    print(f"\nState code stats:")
    print(f"  - Total businesses: {result['total']}")
    print(f"  - With state_code: {result['with_state_code']}")
    print(f"  - Unique states: {result['unique_states']}")
    
    # Show sample state codes
    query3 = """
        SELECT state_code, COUNT(*) as count
        FROM osm_businesses
        WHERE state_code IS NOT NULL
        GROUP BY state_code
        ORDER BY count DESC
        LIMIT 10
    """
    print("\nTop states by business count:")
    states = execute_query(query3)
    for state in states:
        print(f"  - {state['state_code']}: {state['count']} businesses")