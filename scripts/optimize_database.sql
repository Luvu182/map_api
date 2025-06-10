-- Script tối ưu hóa database PostgreSQL sau khi xóa TIGER data
-- Chạy với quyền superuser

-- 1. VACUUM FULL để thu hồi không gian từ các bảng đã xóa
VACUUM FULL;

-- 2. ANALYZE để cập nhật statistics cho query planner
ANALYZE;

-- 3. REINDEX để tối ưu các index
REINDEX DATABASE roads_db;

-- 4. Tối ưu các bảng chính đang sử dụng
VACUUM (FULL, ANALYZE) osm_roads_main;
VACUUM (FULL, ANALYZE) crawl_stats;
VACUUM (FULL, ANALYZE) place_search_cache;

-- 5. Cập nhật statistics cho các cột quan trọng
ANALYZE osm_roads_main (name, type, state_code, county_code, city_code);
ANALYZE crawl_stats (state_code, county_code, crawl_date);

-- 6. Kiểm tra và loại bỏ các index không sử dụng
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- 7. Kiểm tra bloat trong các bảng
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 8. Tối ưu shared buffers và work_mem (chỉ hiển thị giá trị hiện tại)
SHOW shared_buffers;
SHOW work_mem;
SHOW maintenance_work_mem;

-- 9. Kiểm tra kích thước database sau tối ưu
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'roads_db';