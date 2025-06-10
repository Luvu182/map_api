-- Analyze roads with nearby businesses using spatial join
-- For Hawaii as test case

-- Find roads with businesses within 50 meters
WITH road_business_counts AS (
    SELECT 
        r.osm_id,
        r.name,
        r.highway,
        COUNT(DISTINCT b.osm_id) as business_count,
        COUNT(DISTINCT b.business_type) as business_types,
        STRING_AGG(DISTINCT b.business_type, ', ' ORDER BY b.business_type) as type_list,
        COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as brands,
        STRING_AGG(DISTINCT b.brand, ', ' ORDER BY b.brand) 
            FILTER (WHERE b.brand IS NOT NULL AND b.brand != '') as brand_list
    FROM osm_roads_main r
    INNER JOIN osm_businesses b 
        ON ST_DWithin(r.geometry::geography, b.geometry::geography, 50) -- within 50m
    WHERE r.state_code = 'HI' 
        AND b.state_code = 'HI'
        AND r.name IS NOT NULL
    GROUP BY r.osm_id, r.name, r.highway
)
SELECT 
    name,
    highway,
    business_count,
    business_types,
    brands,
    LEFT(type_list, 80) as business_types,
    LEFT(brand_list, 80) as top_brands
FROM road_business_counts
ORDER BY business_count DESC
LIMIT 30;