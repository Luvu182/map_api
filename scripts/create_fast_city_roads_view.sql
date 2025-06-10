-- Create materialized view for fast city road queries

-- Drop if exists
DROP MATERIALIZED VIEW IF EXISTS city_roads_simple CASCADE;

-- Create simple materialized view with pre-joined data
CREATE MATERIALIZED VIEW city_roads_simple AS
SELECT 
    r.osm_id,
    r.name as road_name,
    r.highway,
    r.ref,
    rcm.city_name,
    rcm.state_code,
    r.county_fips
FROM osm_roads_main r
INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
WHERE r.name IS NOT NULL;

-- Create indexes for fast queries
CREATE INDEX idx_city_roads_simple_city ON city_roads_simple(city_name, state_code);
CREATE INDEX idx_city_roads_simple_name ON city_roads_simple(road_name);
CREATE INDEX idx_city_roads_simple_state ON city_roads_simple(state_code);

-- Analyze for query planner
ANALYZE city_roads_simple;

-- Show row count
SELECT COUNT(*) as total_roads FROM city_roads_simple;