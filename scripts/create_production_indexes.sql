-- Production indexes for optimal performance

-- Drop existing indexes that might conflict
DROP INDEX IF EXISTS idx_roads_state;
DROP INDEX IF EXISTS idx_roads_county;
DROP INDEX IF EXISTS idx_roads_fullname;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_roads_state_county ON roads(state_code, county_fips);
CREATE INDEX IF NOT EXISTS idx_roads_county_name ON roads(county_fips, fullname);
CREATE INDEX IF NOT EXISTS idx_roads_county_mtfcc ON roads(county_fips, mtfcc);

-- Full-text search on road names (requires pg_trgm)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_roads_fullname_pattern ON roads USING gin(fullname gin_trgm_ops);

-- MTFCC filtering
CREATE INDEX IF NOT EXISTS idx_roads_mtfcc ON roads(mtfcc);
CREATE INDEX IF NOT EXISTS idx_roads_mtfcc_state ON roads(mtfcc, state_code);

-- Crawl management indexes
CREATE INDEX IF NOT EXISTS idx_crawl_status_road_keyword ON crawl_status(road_linearid, keyword);
CREATE INDEX IF NOT EXISTS idx_crawl_status_keyword ON crawl_status(keyword);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status_date ON crawl_jobs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_road ON crawl_jobs(road_linearid);

-- Business search indexes
CREATE INDEX IF NOT EXISTS idx_businesses_road ON businesses(road_linearid) WHERE road_linearid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_businesses_types ON businesses USING gin(types);
CREATE INDEX IF NOT EXISTS idx_businesses_name_pattern ON businesses USING gin(name gin_trgm_ops);

-- Geometry index (if geometry imported)
CREATE INDEX IF NOT EXISTS idx_roads_geom ON roads USING gist(geom) WHERE geom IS NOT NULL;

-- Analyze all tables for query planner
ANALYZE roads;
ANALYZE states;
ANALYZE counties;
ANALYZE cities;
ANALYZE crawl_status;
ANALYZE crawl_jobs;
ANALYZE businesses;
ANALYZE mtfcc_descriptions;

-- Show index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;