-- Optimize search performance for road queries

-- 1. Ensure materialized view exists and is refreshed
REFRESH MATERIALIZED VIEW CONCURRENTLY city_roads_simple;

-- 2. Create optimized indexes if not exists
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search

-- GIN index for fast text search
CREATE INDEX IF NOT EXISTS idx_city_roads_simple_road_name_gin 
ON city_roads_simple USING gin(road_name gin_trgm_ops);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_city_roads_simple_city_state 
ON city_roads_simple(city_name, state_code);

CREATE INDEX IF NOT EXISTS idx_city_roads_simple_state_road
ON city_roads_simple(state_code, road_name);

-- Index for sorting by road name
CREATE INDEX IF NOT EXISTS idx_city_roads_simple_road_name_btree
ON city_roads_simple(road_name);

-- 3. Update table statistics
ANALYZE city_roads_simple;
ANALYZE osm_roads_main;
ANALYZE road_city_mapping;

-- 4. Show index usage stats
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'city_roads_simple'
ORDER BY idx_scan DESC;

-- 5. Check view size and row count
SELECT 
    'city_roads_simple' as view_name,
    pg_size_pretty(pg_total_relation_size('city_roads_simple')) as total_size,
    (SELECT COUNT(*) FROM city_roads_simple) as row_count;

-- 6. Test query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT DISTINCT ON (road_name, city_name, state_code)
    osm_id, road_name, highway, city_name, state_code
FROM city_roads_simple
WHERE road_name ILIKE '%main%'
AND city_name = 'Los Angeles'
AND state_code = 'CA'
LIMIT 20;