-- Query to find top 20 roads in San Diego ordered by POI count
-- This query joins osm_roads_main with osm_businesses to count POIs per road

WITH san_diego_roads AS (
    -- First get all roads that are in San Diego
    SELECT DISTINCT 
        r.osm_id,
        r.name as road_name,
        r.highway,
        r.geometry
    FROM osm_roads_main r
    INNER JOIN road_city_mapping rcm ON r.id = rcm.road_id
    WHERE rcm.city_name = 'San Diego' 
        AND rcm.state_code = 'CA'
        AND r.name IS NOT NULL
),
road_poi_counts AS (
    -- Count POIs for each road
    SELECT 
        sr.osm_id,
        sr.road_name,
        sr.highway,
        COUNT(DISTINCT b.osm_id) as poi_count
    FROM san_diego_roads sr
    LEFT JOIN osm_businesses b ON b.nearest_road_id = sr.osm_id
    GROUP BY sr.osm_id, sr.road_name, sr.highway
)
-- Final result: top 20 roads by POI count
SELECT 
    road_name,
    osm_id,
    highway as highway_type,
    poi_count
FROM road_poi_counts
ORDER BY poi_count DESC
LIMIT 20;