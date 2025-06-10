-- Create business potential score based on actual POI data
-- This will replace the guessing algorithm with real data

-- Create materialized view for road business statistics
DROP MATERIALIZED VIEW IF EXISTS road_business_stats CASCADE;

CREATE MATERIALIZED VIEW road_business_stats AS
SELECT 
    r.osm_id,
    r.name,
    r.highway,
    r.state_code,
    r.county_fips,
    -- POI counts
    COUNT(DISTINCT b.osm_id) as poi_count,
    COUNT(DISTINCT b.business_type) as business_type_variety,
    COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL) as brand_count,
    -- POI categories
    COUNT(*) FILTER (WHERE b.business_type = 'shop') as shops,
    COUNT(*) FILTER (WHERE b.business_type = 'amenity' AND b.business_subtype IN ('restaurant', 'cafe', 'fast_food', 'bar')) as food_places,
    COUNT(*) FILTER (WHERE b.business_type = 'amenity' AND b.business_subtype IN ('bank', 'pharmacy')) as essential_services,
    -- Data quality
    COUNT(*) FILTER (WHERE b.phone IS NOT NULL AND b.phone != '') as has_phone,
    COUNT(*) FILTER (WHERE b.opening_hours IS NOT NULL AND b.opening_hours != '') as has_hours,
    -- Calculate business potential score (0-100)
    CASE 
        WHEN COUNT(b.osm_id) = 0 THEN 0
        WHEN COUNT(b.osm_id) >= 20 THEN 100
        WHEN COUNT(b.osm_id) >= 10 THEN 80
        WHEN COUNT(b.osm_id) >= 5 THEN 60
        WHEN COUNT(b.osm_id) >= 3 THEN 40
        WHEN COUNT(b.osm_id) >= 1 THEN 20
        ELSE 0
    END as business_potential_score,
    -- Top categories and brands
    STRING_AGG(DISTINCT b.business_type || ':' || b.business_subtype, ', ' ORDER BY b.business_type || ':' || b.business_subtype) 
        FILTER (WHERE b.business_subtype IS NOT NULL) as business_categories,
    STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
        FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as top_brands
FROM osm_roads_main r
LEFT JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
WHERE r.name IS NOT NULL
GROUP BY r.osm_id, r.name, r.highway, r.state_code, r.county_fips;

-- Create indexes
CREATE INDEX idx_road_business_stats_osm_id ON road_business_stats(osm_id);
CREATE INDEX idx_road_business_stats_state ON road_business_stats(state_code);
CREATE INDEX idx_road_business_stats_score ON road_business_stats(business_potential_score DESC);
CREATE INDEX idx_road_business_stats_poi_count ON road_business_stats(poi_count DESC);

-- Create function to get road business score
CREATE OR REPLACE FUNCTION get_road_business_score(p_osm_id BIGINT)
RETURNS TABLE (
    score INTEGER,
    poi_count INTEGER,
    top_categories TEXT,
    top_brands TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        business_potential_score::INTEGER,
        poi_count::INTEGER,
        LEFT(business_categories, 100),
        LEFT(top_brands, 100)
    FROM road_business_stats
    WHERE osm_id = p_osm_id;
END;
$$ LANGUAGE plpgsql;

-- Show sample of roads with highest business potential
SELECT 
    name,
    highway,
    state_code,
    poi_count,
    business_potential_score,
    shops,
    food_places,
    brand_count,
    LEFT(top_brands, 80) as brands_sample
FROM road_business_stats
WHERE poi_count > 0
ORDER BY poi_count DESC
LIMIT 50;