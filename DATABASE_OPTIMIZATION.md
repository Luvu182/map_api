# Database Optimization Guide

## Current Database Status
- **Total Size**: 2.7GB
- **Roads Table**: 2.758GB (99% of total)
- **Other Tables**: ~10MB (PostGIS/Tiger Geocoder tables)
- **Total Records**: 5,203,313 roads

## 1. PostGIS Tables Analysis

### Tables We DON'T Need (Safe to Remove)
These are PostGIS Tiger Geocoder tables for address geocoding that we're not using:

```sql
-- Tiger Geocoder tables (NOT NEEDED)
- pagc_rules       (856 kB) - Address parsing rules
- pagc_lex         (336 kB) - Address lexicon
- pagc_gaz         (128 kB) - Gazetteer data
- street_type_lookup (128 kB) - Street type abbreviations
- state_lookup     (104 kB) - State abbreviations
- direction_lookup (40 kB) - Direction abbreviations
- secondary_unit_lookup (40 kB) - Unit types (Apt, Suite, etc)
- place_lookup     (24 kB) - Place name lookups
- countysub_lookup (24 kB) - County subdivision lookups
- county_lookup    (24 kB) - County lookups
- loader_* tables  - Tiger data loader utilities
- geocode_* tables - Geocoding settings
- addrfeat, edges, faces, addr - Tiger address features
- cousub, place, county, tract, bg, tabblock* - Census boundaries
- zcta5, zip_* tables - ZIP code data
```

**Total to remove**: ~3MB of unnecessary tables

### Tables We MUST KEEP
```sql
-- Core PostGIS (REQUIRED)
- spatial_ref_sys  (7MB) - Coordinate reference systems
- topology         (24KB) - Topology metadata

-- Our data (REQUIRED)
- roads            (2.7GB) - Main road data
- states           (72KB) - State information
- counties         (240KB) - County information
- cities           (16KB) - City data
- businesses       (72KB) - Google Maps crawler data
- crawl_status     (24KB) - Crawler status
- city_counties    (8KB) - City-county mappings
- road_statistics  (32KB) - Materialized view
```

## 2. VACUUM FULL Explanation

### What is VACUUM FULL?
- **Purpose**: Reclaims disk space and defragments tables
- **How it works**: Rewrites entire table to remove dead rows and compact data
- **When needed**: After large deletes/updates or to optimize storage

### Impact on System
```
⚠️ IMPORTANT: VACUUM FULL locks the table completely during operation
- Users CANNOT read or write during vacuum
- Can take 5-30 minutes for large tables
- Requires extra disk space (temporarily doubles table size)
```

### Safer Alternative: Regular VACUUM
```sql
VACUUM ANALYZE roads;  -- Non-blocking, updates statistics
```

## 3. Geometry Column Explanation

### What is the geometry column?
- **Purpose**: Stores geographic shapes (points, lines, polygons)
- **Current status**: Column exists but is EMPTY (NULL for all rows)
- **Size impact**: Minimal when empty, but reserves space

### Why we added it:
- For future spatial queries (find roads within X miles)
- Draw roads on maps
- Calculate distances between roads
- Spatial joins with other geographic data

### Should we keep it?
- **Keep if**: Planning to add geographic data later
- **Remove if**: Only need road names/IDs, not locations

## 4. Optimization Plan

### Step 1: Remove Unnecessary Tables (Safe)
```sql
-- Remove Tiger Geocoder tables we don't use
DROP TABLE IF EXISTS pagc_rules CASCADE;
DROP TABLE IF EXISTS pagc_lex CASCADE;
DROP TABLE IF EXISTS pagc_gaz CASCADE;
DROP TABLE IF EXISTS street_type_lookup CASCADE;
DROP TABLE IF EXISTS state_lookup CASCADE;
DROP TABLE IF EXISTS direction_lookup CASCADE;
DROP TABLE IF EXISTS secondary_unit_lookup CASCADE;
DROP TABLE IF EXISTS place_lookup CASCADE;
DROP TABLE IF EXISTS countysub_lookup CASCADE;
DROP TABLE IF EXISTS county_lookup CASCADE;
DROP TABLE IF EXISTS loader_lookuptables CASCADE;
DROP TABLE IF EXISTS loader_platform CASCADE;
DROP TABLE IF EXISTS loader_variables CASCADE;
DROP TABLE IF EXISTS geocode_settings CASCADE;
DROP TABLE IF EXISTS geocode_settings_default CASCADE;
DROP TABLE IF EXISTS addrfeat CASCADE;
DROP TABLE IF EXISTS edges CASCADE;
DROP TABLE IF EXISTS faces CASCADE;
DROP TABLE IF EXISTS addr CASCADE;
DROP TABLE IF EXISTS featnames CASCADE;
DROP TABLE IF EXISTS place CASCADE;
DROP TABLE IF EXISTS cousub CASCADE;
DROP TABLE IF EXISTS county CASCADE;
DROP TABLE IF EXISTS state CASCADE;
DROP TABLE IF EXISTS tract CASCADE;
DROP TABLE IF EXISTS tabblock CASCADE;
DROP TABLE IF EXISTS tabblock20 CASCADE;
DROP TABLE IF EXISTS bg CASCADE;
DROP TABLE IF EXISTS zcta5 CASCADE;
DROP TABLE IF EXISTS zip_lookup CASCADE;
DROP TABLE IF EXISTS zip_lookup_all CASCADE;
DROP TABLE IF EXISTS zip_lookup_base CASCADE;
DROP TABLE IF EXISTS zip_state CASCADE;
DROP TABLE IF EXISTS zip_state_loc CASCADE;
```

### Step 2: Optimize Roads Table (Optional)
```sql
-- Option A: Quick optimization (minimal downtime)
VACUUM ANALYZE roads;

-- Option B: Full optimization (requires downtime)
VACUUM FULL roads;  -- WARNING: Locks table for 10-30 minutes
```

### Step 3: Remove Geometry Column (If Not Needed)
```sql
-- Only if you're sure you don't need geographic data
ALTER TABLE roads DROP COLUMN geom;
```

### Step 4: Remove Duplicates (Optional)
```sql
-- Find duplicates
SELECT linearid, COUNT(*) 
FROM roads 
GROUP BY linearid 
HAVING COUNT(*) > 1;

-- Remove duplicates (keep first occurrence)
DELETE FROM roads a
USING roads b
WHERE a.id > b.id AND a.linearid = b.linearid;
```

## 5. Expected Results

### After Optimization:
- Remove Tiger tables: Save ~3MB
- VACUUM FULL: Could save 10-20% (270-540MB)
- Remove geometry column: Save ~100-200MB
- Remove duplicates: Save ~50MB

### Total Potential Savings: 400-800MB
**Final size**: ~1.9-2.3GB (closer to Supabase)

## 6. Backup Before Optimization

```bash
# IMPORTANT: Backup first!
./backup_postgres.sh

# Or manual backup
docker exec roads-postgres pg_dump -U postgres -d roads_db | gzip > backup_before_optimization.sql.gz
```

## 7. Monitoring Commands

```sql
-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) 
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;

-- Check database size
SELECT pg_database_size('roads_db')/1024/1024 || ' MB' as size;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan;
```