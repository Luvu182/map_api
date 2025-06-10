-- Create materialized view for fast dashboard statistics

-- Drop if exists
DROP MATERIALIZED VIEW IF EXISTS osm_road_stats CASCADE;

-- Create materialized view for dashboard stats (simplified)
CREATE MATERIALIZED VIEW osm_road_stats AS
SELECT 
    -- Total counts
    COUNT(*) as total_segments,
    COUNT(name) as segments_with_names,
    COUNT(DISTINCT CONCAT(name, '|', county_fips)) FILTER (WHERE name IS NOT NULL) as unique_roads_with_names,
    
    -- Last update time
    NOW() as last_updated
FROM osm_roads_main;

-- Create index
CREATE UNIQUE INDEX idx_osm_road_stats ON osm_road_stats ((1));

-- Initial refresh
REFRESH MATERIALIZED VIEW osm_road_stats;

-- Check the stats
SELECT * FROM osm_road_stats;