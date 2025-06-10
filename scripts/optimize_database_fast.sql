-- Script tối ưu database nhanh hơn

-- 1. VACUUM thông thường (không FULL) để nhanh hơn
VACUUM ANALYZE;

-- 2. Chỉ VACUUM FULL các bảng quan trọng
VACUUM (FULL, ANALYZE) osm_roads_main;
VACUUM ANALYZE crawl_stats;
VACUUM ANALYZE place_search_cache;

-- 3. Cập nhật statistics
ANALYZE osm_roads_main (name, type, state_code, county_code, city_code);

-- 4. Kiểm tra kích thước database
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'roads_db';

-- 5. Kiểm tra các bảng lớn nhất
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- 6. Đếm số dòng trong bảng chính
SELECT 
    'osm_roads_main' as table_name,
    count(*) as row_count
FROM osm_roads_main
UNION ALL
SELECT 
    'crawl_stats' as table_name,
    count(*) as row_count
FROM crawl_stats
UNION ALL
SELECT 
    'place_search_cache' as table_name,
    count(*) as row_count
FROM place_search_cache;