-- Recreate views and materialized views that were dropped with CASCADE

-- 1. Create view: roads_in_target_cities
CREATE OR REPLACE VIEW roads_in_target_cities AS
SELECT r.*
FROM osm_roads_main r
WHERE EXISTS (
    SELECT 1 
    FROM road_city_mapping rcm
    WHERE rcm.road_id = r.id
);

-- 2. Create view: road_business_with_city
CREATE OR REPLACE VIEW road_business_with_city AS
SELECT 
    r.id as road_id,
    r.osm_id as road_osm_id,
    r.name as road_name,
    r.highway,
    r.state_code,
    rcm.city_name,
    b.osm_id as business_osm_id,
    b.name as business_name,
    b.business_type,
    b.tags
FROM osm_roads_main r
JOIN road_city_mapping rcm ON r.id = rcm.road_id
LEFT JOIN osm_businesses b ON ST_DWithin(
    r.geometry::geography,
    b.geometry::geography,
    100 -- within 100 meters
);

-- 3. Create view: road_business_potential
CREATE OR REPLACE VIEW road_business_potential AS
SELECT 
    rcm.city_name,
    rcm.state_code,
    r.highway,
    COUNT(DISTINCT r.id) as road_count,
    COUNT(DISTINCT b.osm_id) as business_count,
    ROUND((COUNT(DISTINCT b.osm_id)::numeric / NULLIF(COUNT(DISTINCT r.id), 0)) * 100, 2) as business_density_pct
FROM osm_roads_main r
JOIN road_city_mapping rcm ON r.id = rcm.road_id
LEFT JOIN osm_businesses b ON ST_DWithin(
    r.geometry::geography,
    b.geometry::geography,
    100
)
GROUP BY rcm.city_name, rcm.state_code, r.highway;

-- 4. Create materialized view: osm_road_stats
CREATE MATERIALIZED VIEW osm_road_stats AS
SELECT 
    state_code,
    COUNT(*) as total_roads,
    COUNT(DISTINCT osm_id) as unique_osm_ids,
    COUNT(name) as roads_with_names,
    COUNT(DISTINCT highway) as highway_types,
    MIN(imported_at) as first_import,
    MAX(imported_at) as last_import
FROM osm_roads_main
GROUP BY state_code;

-- Create index on materialized view
CREATE INDEX idx_osm_road_stats_state ON osm_road_stats(state_code);

-- 5. Create materialized view: osm_road_stats_by_state
CREATE MATERIALIZED VIEW osm_road_stats_by_state AS
SELECT 
    state_code,
    highway,
    COUNT(*) as road_count,
    COUNT(name) as named_roads,
    ROUND((COUNT(name)::numeric / COUNT(*)) * 100, 2) as named_percentage
FROM osm_roads_main
GROUP BY state_code, highway
ORDER BY state_code, road_count DESC;

-- Create indexes
CREATE INDEX idx_osm_road_stats_by_state_state ON osm_road_stats_by_state(state_code);
CREATE INDEX idx_osm_road_stats_by_state_highway ON osm_road_stats_by_state(highway);

-- Refresh materialized views with data
REFRESH MATERIALIZED VIEW osm_road_stats;
REFRESH MATERIALIZED VIEW osm_road_stats_by_state;

-- Show results
\echo 'Views and materialized views recreated successfully!'
\echo ''
\echo 'Checking views:'
SELECT schemaname, viewname, viewowner 
FROM pg_views 
WHERE viewname IN ('roads_in_target_cities', 'road_business_with_city', 'road_business_potential')
ORDER BY viewname;

\echo ''
\echo 'Checking materialized views:'
SELECT schemaname, matviewname, matviewowner 
FROM pg_matviews 
WHERE matviewname IN ('osm_road_stats', 'osm_road_stats_by_state')
ORDER BY matviewname;

\echo ''
\echo 'Sample data from osm_road_stats:'
SELECT * FROM osm_road_stats ORDER BY total_roads DESC LIMIT 5;