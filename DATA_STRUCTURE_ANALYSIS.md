# Data Structure Analysis and Recommendations

## Current Situation

### 1. Data Sources
- **Shapefiles**: Most states imported from shapefiles (TX, FL, AZ, NY, etc.)
- **PBF File**: California imported directly from PBF to preserve full metadata

### 2. Current Tables
- `osm_roads`: Shapefile imports (limited to 254 chars per field)
- `california_roads_pbf`: PBF import with full metadata (up to 1,615 chars)

### 3. Key Differences

#### Shapefile Data (osm_roads)
```sql
-- Limited metadata due to shapefile format
- osm_id: VARCHAR(10)
- name: VARCHAR(254)
- highway: VARCHAR(254)
- other_tags: TEXT (truncated at 254 chars)
- state_code: CHAR(2)
- county_fips: CHAR(5)
```

#### PBF Data (california_roads_pbf)
```sql
-- Full metadata preserved
- osm_id: VARCHAR
- name: TEXT
- highway: TEXT
- other_tags: TEXT (full data, up to 1,615+ chars)
- ref: TEXT
- (missing state_code and county_fips)
```

## Problems Identified

1. **Data Inconsistency**: Different table structures for different states
2. **Missing Fields**: PBF imports lack county_fips needed for filtering
3. **Metadata Format**: `other_tags` is text in hstore format, hard to query
4. **Character Limits**: Shapefiles truncate valuable metadata

## Recommendation: Unified Schema

### Proposed Table Structure
```sql
CREATE TABLE osm_roads_unified (
    id BIGSERIAL PRIMARY KEY,
    osm_id BIGINT NOT NULL,
    name TEXT,
    highway VARCHAR(50),
    ref VARCHAR(100),
    
    -- Location (REQUIRED for system)
    state_code CHAR(2) NOT NULL,
    county_fips CHAR(5) NOT NULL,
    
    -- Geometry
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    
    -- All metadata as JSONB (flexible, queryable)
    tags JSONB DEFAULT '{}',
    
    -- Metadata
    source VARCHAR(10) CHECK (source IN ('pbf', 'shp')),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(osm_id, state_code)
);
```

### Benefits
1. **Consistent Structure**: Same schema for all states
2. **Full Metadata**: JSONB preserves all tags without truncation
3. **Queryable**: Can search metadata efficiently
4. **County Assignment**: Spatial join during import

### Example Queries with JSONB
```sql
-- Find roads by speed limit
SELECT name, tags->>'maxspeed' as speed_limit
FROM osm_roads_unified
WHERE tags->>'maxspeed' = '65 mph';

-- Find multi-lane highways
SELECT name, tags->>'lanes' as lanes
FROM osm_roads_unified
WHERE (tags->>'lanes')::INT > 4;
```

## Import Strategy

### Option A: Keep Current Structure (Not Recommended)
- Continue with mixed tables
- Inconsistent data quality
- Complex API queries

### Option B: Migrate to Unified Schema (Recommended)
1. Create unified table
2. Import California with county assignment
3. Re-import other states from PBF for full data
4. Update API to use unified table

### Option C: Quick Fix (If Time Constrained)
1. Add missing fields to california_roads_pbf
2. Create view combining both tables
3. Update API to use view

## Required Fields for Google Maps Search

**Essential**:
- `name`: Road name for search
- `geometry`: Location for GPS coordinates
- `state_code` + `county_fips`: Location filtering

**Useful**:
- `highway`: Road type filtering
- `ref`: Route numbers (I-10, US-101)
- `tags->>'maxspeed'`: Speed limits
- `tags->>'lanes'`: Number of lanes

## Next Steps

1. **Immediate**: Fix California data by adding county_fips
2. **Short-term**: Create unified table and migrate California
3. **Long-term**: Download PBF files for all states and re-import

## Commands for Migration

```bash
# 1. Create unified schema
psql -U postgres -d roads_db -f scripts/create_unified_import.sql

# 2. Import California with counties
psql -U postgres -d roads_db -c "
INSERT INTO osm_roads_unified (osm_id, name, highway, ref, state_code, county_fips, geometry, tags, source)
SELECT 
    c.osm_id::BIGINT,
    c.name,
    c.highway,
    c.ref,
    'CA' as state_code,
    cb.county_fips,
    c.geometry,
    hstore_to_jsonb(c.other_tags),
    'pbf'
FROM california_roads_pbf c
JOIN county_boundaries cb ON 
    cb.state_code = 'CA' 
    AND ST_Intersects(c.geometry, cb.boundary);"

# 3. Update API to use unified table
```