# Dashboard Performance Optimization

## Problem
Dashboard was loading slowly due to expensive queries on 27M+ records:
- `COUNT(DISTINCT CONCAT(name, '|', county_fips))` was taking several seconds

## Solutions Implemented

### 1. Statistics Cache Table ✅
Created `osm_stats_cache` table that stores pre-calculated stats:
```sql
CREATE TABLE osm_stats_cache (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_segments BIGINT,
    segments_with_names BIGINT,
    unique_roads_with_names BIGINT,
    last_updated TIMESTAMP
);
```

**Result**: Dashboard stats now load instantly (< 1ms)

### 2. Materialized View ✅
Created `osm_road_stats` materialized view as backup:
```sql
CREATE MATERIALIZED VIEW osm_road_stats AS
SELECT 
    COUNT(*) as total_segments,
    COUNT(name) as segments_with_names,
    COUNT(DISTINCT CONCAT(name, '|', county_fips)) as unique_roads_with_names
FROM osm_roads_main;
```

### 3. Query Indexes ✅
Added indexes for common queries:
- `idx_osm_roads_main_state_county_name` - For filtering by location
- `idx_osm_roads_main_name_pattern` - For name searches
- `idx_osm_roads_main_named` - For roads with names only

### 4. Backend Updates ✅
- `/stats` endpoint now queries cache table instead of main table
- Query time reduced from ~5 seconds to < 1ms

## How to Update Stats

After importing new data:

```sql
-- Option 1: Update cache table (fastest)
UPDATE osm_stats_cache SET
    total_segments = (SELECT COUNT(*) FROM osm_roads_main),
    segments_with_names = (SELECT COUNT(name) FROM osm_roads_main),
    unique_roads_with_names = (SELECT COUNT(DISTINCT CONCAT(name, '|', county_fips)) 
                              FROM osm_roads_main WHERE name IS NOT NULL),
    last_updated = NOW()
WHERE id = 1;

-- Option 2: Refresh materialized view
REFRESH MATERIALIZED VIEW osm_road_stats;
```

## Performance Results

Before optimization:
- Dashboard load time: 5-10 seconds
- Stats query: ~5 seconds

After optimization:
- Dashboard load time: < 100ms
- Stats query: < 1ms

## Frontend Display

Dashboard now correctly shows:
- **Total Roads**: 27,157,444 (segments)
- **Roads with Names**: 2,768,406 (unique roads, not segments)

This is displayed as "2.77M unique roads available for crawling"