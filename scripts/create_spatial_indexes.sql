-- Tạo spatial indexes để tăng tốc queries

-- 1. Index cho geometry column (quan trọng nhất)
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_geometry_gist 
ON osm_roads_main USING GIST (geometry);

-- 2. Index cho geography cast (dùng cho distance calculations)
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_geography_gist 
ON osm_roads_main USING GIST ((geometry::geography));

-- 3. Compound index cho state và county
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_state_county 
ON osm_roads_main (state_code, county_fips);

-- 4. Index cho highway type
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_highway 
ON osm_roads_main (highway);

-- 5. Index cho name searches
CREATE INDEX IF NOT EXISTS idx_osm_roads_main_name_trgm 
ON osm_roads_main USING gin (name gin_trgm_ops);

-- 6. Analyze table để update statistics
ANALYZE osm_roads_main;

-- 7. Kiểm tra indexes đã tạo
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE tablename = 'osm_roads_main'
ORDER BY pg_relation_size(indexname::regclass) DESC;