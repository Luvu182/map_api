-- Create road POI statistics table for Alabama test
-- This will help identify roads with actual businesses

-- Drop if exists
DROP TABLE IF EXISTS road_poi_stats_hi;

-- Create summary table for Alabama
CREATE TABLE road_poi_stats_hi AS
SELECT 
    r.osm_id,
    r.name,
    r.highway,
    r.state_code,
    r.county_fips,
    COUNT(DISTINCT b.osm_id) as poi_count,
    COUNT(DISTINCT b.business_type) as business_type_count,
    STRING_AGG(DISTINCT b.business_type, ', ' ORDER BY b.business_type) as business_types,
    COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as brand_count,
    STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
        FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as top_brands
FROM osm_roads_main r
LEFT JOIN osm_businesses b 
    ON b.nearest_road_id = r.osm_id
WHERE r.state_code = 'HI'
    AND r.name IS NOT NULL
GROUP BY r.osm_id, r.name, r.highway, r.state_code, r.county_fips;

-- Create indexes for fast queries
CREATE INDEX idx_road_poi_stats_hi_osm_id ON road_poi_stats_hi(osm_id);
CREATE INDEX idx_road_poi_stats_hi_poi_count ON road_poi_stats_hi(poi_count DESC);
CREATE INDEX idx_road_poi_stats_hi_name ON road_poi_stats_hi(name);

-- Show top roads with most businesses
SELECT 
    name,
    highway,
    poi_count,
    business_type_count,
    brand_count,
    LEFT(business_types, 100) as business_types_sample,
    LEFT(top_brands, 100) as brands_sample
FROM road_poi_stats_hi
WHERE poi_count > 0
ORDER BY poi_count DESC
LIMIT 20;