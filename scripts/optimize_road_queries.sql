-- Optimize queries for road listing and searching

-- 1. Create composite index for road queries (if not exists)
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_state_county_name 
ON osm_roads_main(state_code, county_fips, name);

-- 2. Create index for name searches
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_name_pattern 
ON osm_roads_main(name varchar_pattern_ops) 
WHERE name IS NOT NULL;

-- 3. Create partial index for roads with names
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_named 
ON osm_roads_main(state_code, county_fips) 
WHERE name IS NOT NULL;

-- 4. Analyze table to update statistics
ANALYZE osm_roads_main;

-- 5. Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'osm_roads_main'
ORDER BY idx_scan DESC;