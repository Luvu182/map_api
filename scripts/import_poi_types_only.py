#!/usr/bin/env python3
"""
Ultra simple POI import - ONLY business type and subtype
For road business potential analysis
"""
import osmium
import psycopg2
from psycopg2.extras import execute_batch
import sys

class TypeOnlyHandler(osmium.SimpleHandler):
    def __init__(self, conn, state_code):
        super().__init__()
        self.conn = conn
        self.state_code = state_code
        self.batch = []
        self.batch_size = 10000  # Larger batch for speed
        self.count = 0
        
        # Commercial types only
        self.commercial = {'shop', 'amenity', 'tourism', 'office', 'craft', 'healthcare'}
        
        # Skip these amenities
        self.skip = {
            'parking', 'parking_space', 'bicycle_parking', 'bench', 
            'waste_basket', 'toilets', 'drinking_water', 'fountain'
        }
        
    def node(self, n):
        tags = dict(n.tags)
        
        # Must have name to be a real business
        if 'name' not in tags:
            return
            
        # Find type
        biz_type = None
        biz_subtype = None
        
        for t in self.commercial:
            if t in tags:
                biz_type = t
                biz_subtype = tags[t]
                break
                
        if not biz_type:
            return
            
        # Skip non-commercial
        if biz_type == 'amenity' and biz_subtype in self.skip:
            return
            
        # Simple record - only essentials (truncate to fit columns)
        self.batch.append((
            n.id,  # osm_id
            biz_type[:20] if biz_type else None,  # Truncate to 20 chars
            biz_subtype[:50] if biz_subtype else None,  # Truncate to 50 chars
            n.location.lon,
            n.location.lat,
            self.state_code
        ))
        
        self.count += 1
        
        if len(self.batch) >= self.batch_size:
            self.flush()
            
        if self.count % 50000 == 0:
            print(f"Processed {self.count:,} POIs...")
            
    def flush(self):
        if not self.batch:
            return
            
        cur = self.conn.cursor()
        
        # Create temp table for ultra-fast insert
        cur.execute("""
            CREATE TEMP TABLE IF NOT EXISTS poi_import (
                osm_id BIGINT,
                business_type VARCHAR,
                business_subtype VARCHAR,
                lon DOUBLE PRECISION,
                lat DOUBLE PRECISION,
                state_code VARCHAR(2)
            )
        """)
        
        # Bulk insert to temp
        execute_batch(cur, """
            INSERT INTO poi_import VALUES (%s, %s, %s, %s, %s, %s)
        """, self.batch, page_size=5000)
        
        # Insert to main table
        cur.execute("""
            INSERT INTO osm_businesses (
                osm_id, osm_type, business_type, business_subtype,
                geometry, state_code, name
            )
            SELECT 
                osm_id, 'node', business_type, business_subtype,
                ST_SetSRID(ST_MakePoint(lon, lat), 4326),
                state_code, ''
            FROM poi_import
            ON CONFLICT (osm_id) DO NOTHING
        """)
        
        cur.execute("TRUNCATE poi_import")
        self.conn.commit()
        
        self.batch = []
        
    def close(self):
        self.flush()
        print(f"✓ Total: {self.count:,} commercial POIs")

def main():
    if len(sys.argv) != 3:
        print("Usage: python import_poi_types_only.py STATE_CODE FILE")
        sys.exit(1)
        
    state_code = sys.argv[1]
    osm_file = sys.argv[2]
    
    conn = psycopg2.connect(
        host="roads-postgres",
        database="roads_db", 
        user="postgres",
        password="roadsdb2024secure"
    )
    
    print(f"Importing {state_code} (types only)...")
    
    handler = TypeOnlyHandler(conn, state_code)
    handler.apply_file(osm_file, locations=True)
    handler.close()
    
    # Summary
    cur = conn.cursor()
    cur.execute("""
        SELECT business_type, COUNT(*) 
        FROM osm_businesses 
        WHERE state_code = %s 
        GROUP BY business_type
    """, (state_code,))
    
    print("\nSummary:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,}")
        
    conn.close()

if __name__ == "__main__":
    main()