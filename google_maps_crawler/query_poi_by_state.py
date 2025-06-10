#!/usr/bin/env python3
"""
Query POI count from osm_businesses table grouped by state_code
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query

def query_poi_by_state():
    """Query POI count grouped by state_code"""
    try:
        query = """
            SELECT 
                state_code, 
                COUNT(*) as poi_count 
            FROM osm_businesses 
            GROUP BY state_code 
            ORDER BY poi_count DESC
        """
        
        results = execute_query(query)
        
        print("POI Count by State Code")
        print("=" * 30)
        print(f"{'State Code':<12} {'POI Count':>10}")
        print("-" * 30)
        
        total_pois = 0
        for row in results:
            state_code = row['state_code'] or 'NULL'
            poi_count = row['poi_count']
            total_pois += poi_count
            print(f"{state_code:<12} {poi_count:>10,}")
        
        print("-" * 30)
        print(f"{'TOTAL':<12} {total_pois:>10,}")
        print(f"\nTotal states: {len(results)}")
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return

if __name__ == "__main__":
    query_poi_by_state()