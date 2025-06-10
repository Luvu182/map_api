-- Create materialized view for fast dashboard statistics
-- This pre-calculates stats and refreshes periodically

-- Drop if exists
DROP MATERIALIZED VIEW IF EXISTS osm_road_stats CASCADE;

-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW osm_road_stats AS
SELECT 
    -- Total counts
    COUNT(*) as total_segments,
    COUNT(name) as segments_with_names,
    COUNT(DISTINCT CONCAT(name, '|', county_fips)) FILTER (WHERE name IS NOT NULL) as unique_roads_with_names,
    
    -- By road type
    COUNT(*) FILTER (WHERE highway IN ('motorway', 'trunk')) as highway_segments,
    COUNT(*) FILTER (WHERE highway IN ('primary', 'secondary', 'tertiary')) as major_road_segments,
    COUNT(*) FILTER (WHERE highway = 'residential') as residential_segments,
    COUNT(*) FILTER (WHERE highway = 'service') as service_segments,
    
    -- Stats
    ROUND(AVG(
        CASE WHEN name IS NOT NULL 
        THEN ST_Length(geography(geometry))/1000.0 
        END
    ), 2) as avg_road_length_km,
    
    -- Last update time
    NOW() as last_updated
FROM osm_roads_main;

-- Create indexes on the materialized view
CREATE UNIQUE INDEX idx_osm_road_stats_single_row ON osm_road_stats ((1));

-- Create state-level statistics
DROP MATERIALIZED VIEW IF EXISTS osm_road_stats_by_state CASCADE;

CREATE MATERIALIZED VIEW osm_road_stats_by_state AS
SELECT 
    state_code,
    COUNT(*) as total_segments,
    COUNT(DISTINCT county_fips) as counties,
    COUNT(name) as segments_with_names,
    COUNT(DISTINCT CONCAT(name, '|', county_fips)) FILTER (WHERE name IS NOT NULL) as unique_roads
FROM osm_roads_main
GROUP BY state_code;

-- Create index
CREATE UNIQUE INDEX idx_osm_road_stats_by_state ON osm_road_stats_by_state (state_code);

-- Function to refresh stats (call this after imports or periodically)
CREATE OR REPLACE FUNCTION refresh_road_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY osm_road_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY osm_road_stats_by_state;
END;
$$ LANGUAGE plpgsql;

-- Initial refresh
REFRESH MATERIALIZED VIEW osm_road_stats;
REFRESH MATERIALIZED VIEW osm_road_stats_by_state;

-- Check the stats
SELECT * FROM osm_road_stats;
SELECT * FROM osm_road_stats_by_state ORDER BY total_segments DESC LIMIT 10;