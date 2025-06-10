-- Create a pre-calculated mapping table for roads to cities
-- This is more efficient than doing spatial joins on the fly

-- First, create the mapping table
CREATE TABLE IF NOT EXISTS road_city_mapping (
    osm_id BIGINT PRIMARY KEY,
    road_name TEXT,
    state_code VARCHAR(2),
    county_fips VARCHAR(10),
    city_name TEXT,
    city_type TEXT,
    distance_m FLOAT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_road_city_mapping_state_county 
ON road_city_mapping(state_code, county_fips);

CREATE INDEX IF NOT EXISTS idx_road_city_mapping_road_name 
ON road_city_mapping(road_name);

-- Function to populate mapping for a specific county
CREATE OR REPLACE FUNCTION populate_road_city_mapping(
    p_state_code VARCHAR,
    p_county_fips VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    rows_inserted INTEGER;
BEGIN
    -- Delete existing mappings for this county
    DELETE FROM road_city_mapping 
    WHERE state_code = p_state_code 
    AND (p_county_fips IS NULL OR county_fips = p_county_fips);
    
    -- Insert new mappings
    WITH road_cities AS (
        SELECT 
            r.osm_id,
            r.name as road_name,
            r.state_code,
            r.county_fips,
            p.name as city_name,
            p.place_type as city_type,
            ST_Distance(r.geometry::geography, p.geometry::geography) as distance_m,
            ROW_NUMBER() OVER (PARTITION BY r.osm_id ORDER BY ST_Distance(r.geometry::geography, p.geometry::geography)) as rn
        FROM osm_roads_main r
        JOIN osm_places p 
            ON r.state_code = p.state_code
            AND ST_DWithin(r.geometry::geography, p.geometry::geography, 10000) -- 10km radius
        WHERE r.state_code = p_state_code
        AND r.county_fips = p_county_fips
        AND p.place_type IN ('city', 'town', 'village')
        AND r.name IS NOT NULL
    )
    INSERT INTO road_city_mapping 
    SELECT osm_id, road_name, state_code, county_fips, city_name, city_type, distance_m
    FROM road_cities
    WHERE rn = 1;
    
    GET DIAGNOSTICS rows_inserted = ROW_COUNT;
    RETURN rows_inserted;
END;
$$ LANGUAGE plpgsql;

-- Test with Riverside County
SELECT populate_road_city_mapping('CA', '06065');