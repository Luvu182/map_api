-- Final Business Potential Scoring System
-- Based on analysis of real POI data from AL and CA

-- Drop existing views
DROP MATERIALIZED VIEW IF EXISTS road_business_potential CASCADE;

-- Create the comprehensive scoring view
CREATE MATERIALIZED VIEW road_business_potential AS
WITH road_metrics AS (
    SELECT 
        r.osm_id,
        r.name as road_name,
        r.highway,
        r.state_code,
        r.county_fips,
        ST_Length(r.geometry::geography)/1000 as length_km,
        
        -- POI metrics
        COALESCE(COUNT(DISTINCT b.osm_id), 0) as poi_count,
        COUNT(DISTINCT b.business_type) as business_type_count,
        COUNT(DISTINCT b.business_subtype) as business_subtype_count,
        
        -- POI density
        CASE 
            WHEN ST_Length(r.geometry::geography) > 0 
            THEN COUNT(DISTINCT b.osm_id) / (ST_Length(r.geometry::geography)/1000)
            ELSE 0 
        END as poi_per_km,
        
        -- Business types list
        STRING_AGG(DISTINCT b.business_type, ', ' ORDER BY b.business_type) as business_types,
        STRING_AGG(DISTINCT b.business_subtype, ', ' ORDER BY b.business_subtype) 
            FILTER (WHERE b.business_subtype IS NOT NULL) as business_subtypes
            
    FROM osm_roads_main r
    LEFT JOIN osm_businesses b 
        ON b.nearest_road_id = r.osm_id 
        AND r.state_code = b.state_code
    WHERE r.name IS NOT NULL
    GROUP BY r.osm_id, r.name, r.highway, r.state_code, r.county_fips, r.geometry
)
SELECT 
    osm_id,
    road_name,
    highway,
    state_code,
    county_fips,
    ROUND(length_km::numeric, 2) as length_km,
    poi_count,
    business_type_count,
    ROUND(poi_per_km::numeric, 2) as poi_density,
    business_types,
    CASE 
        WHEN LENGTH(business_subtypes) > 200 
        THEN LEFT(business_subtypes, 197) || '...'
        ELSE business_subtypes
    END as business_subtypes,
    
    -- Component scores
    -- 1. POI Score (40%)
    ROUND((CASE
        WHEN poi_count = 0 THEN 0
        WHEN poi_count = 1 THEN 30
        WHEN poi_count = 2 THEN 50
        WHEN poi_count = 3 THEN 65
        WHEN poi_count = 4 THEN 75
        WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
        WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
        ELSE 100
    END * 0.4)::numeric, 1) as poi_score,
    
    -- 2. Road Type Score (20%)
    ROUND((CASE
        WHEN highway IN ('primary', 'secondary') THEN 80
        WHEN highway = 'tertiary' THEN 70
        WHEN highway IN ('residential', 'unclassified') THEN 60
        WHEN highway = 'living_street' THEN 50
        WHEN highway IN ('motorway', 'trunk') THEN 30
        ELSE 20
    END * 0.2)::numeric, 1) as road_type_score,
    
    -- 3. Diversity Score (20%)
    ROUND((CASE
        WHEN business_type_count >= 5 THEN 100
        WHEN business_type_count = 4 THEN 80
        WHEN business_type_count = 3 THEN 60
        WHEN business_type_count = 2 THEN 40
        WHEN business_type_count = 1 THEN 20
        ELSE 0
    END * 0.2)::numeric, 1) as diversity_score,
    
    -- 4. Location Score (10%)
    ROUND((CASE
        WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
        WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
        WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
        WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
        ELSE 0
    END * 0.1)::numeric, 1) as location_score,
    
    -- 5. Density Score (10%)
    ROUND((CASE
        WHEN poi_per_km >= 10 THEN 100
        WHEN poi_per_km >= 5 THEN 80
        WHEN poi_per_km >= 2 THEN 60
        WHEN poi_per_km >= 1 THEN 40
        WHEN poi_per_km > 0 THEN 20
        ELSE 0
    END * 0.1)::numeric, 1) as density_score,
    
    -- Total Business Potential Score
    ROUND(
        -- POI Score (40%)
        (CASE
            WHEN poi_count = 0 THEN 0
            WHEN poi_count = 1 THEN 30
            WHEN poi_count = 2 THEN 50
            WHEN poi_count = 3 THEN 65
            WHEN poi_count = 4 THEN 75
            WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
            WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
            ELSE 100
        END * 0.4) +
        
        -- Road Type Score (20%)
        (CASE
            WHEN highway IN ('primary', 'secondary') THEN 80
            WHEN highway = 'tertiary' THEN 70
            WHEN highway IN ('residential', 'unclassified') THEN 60
            WHEN highway = 'living_street' THEN 50
            WHEN highway IN ('motorway', 'trunk') THEN 30
            ELSE 20
        END * 0.2) +
        
        -- Diversity Score (20%)
        (CASE
            WHEN business_type_count >= 5 THEN 100
            WHEN business_type_count = 4 THEN 80
            WHEN business_type_count = 3 THEN 60
            WHEN business_type_count = 2 THEN 40
            WHEN business_type_count = 1 THEN 20
            ELSE 0
        END * 0.2) +
        
        -- Location Score (10%)
        (CASE
            WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
            WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
            WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
            WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
            ELSE 0
        END * 0.1) +
        
        -- Density Score (10%)
        (CASE
            WHEN poi_per_km >= 10 THEN 100
            WHEN poi_per_km >= 5 THEN 80
            WHEN poi_per_km >= 2 THEN 60
            WHEN poi_per_km >= 1 THEN 40
            WHEN poi_per_km > 0 THEN 20
            ELSE 0
        END * 0.1)
    ::numeric, 1) as business_potential_score,
    
    -- Category
    CASE
        WHEN (
            -- Full formula repeated for categorization
            (CASE
                WHEN poi_count = 0 THEN 0
                WHEN poi_count = 1 THEN 30
                WHEN poi_count = 2 THEN 50
                WHEN poi_count = 3 THEN 65
                WHEN poi_count = 4 THEN 75
                WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
                WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
                ELSE 100
            END * 0.4) +
            (CASE
                WHEN highway IN ('primary', 'secondary') THEN 80
                WHEN highway = 'tertiary' THEN 70
                WHEN highway IN ('residential', 'unclassified') THEN 60
                WHEN highway = 'living_street' THEN 50
                WHEN highway IN ('motorway', 'trunk') THEN 30
                ELSE 20
            END * 0.2) +
            (CASE
                WHEN business_type_count >= 5 THEN 100
                WHEN business_type_count = 4 THEN 80
                WHEN business_type_count = 3 THEN 60
                WHEN business_type_count = 2 THEN 40
                WHEN business_type_count = 1 THEN 20
                ELSE 0
            END * 0.2) +
            (CASE
                WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
                WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
                WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
                WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
                ELSE 0
            END * 0.1) +
            (CASE
                WHEN poi_per_km >= 10 THEN 100
                WHEN poi_per_km >= 5 THEN 80
                WHEN poi_per_km >= 2 THEN 60
                WHEN poi_per_km >= 1 THEN 40
                WHEN poi_per_km > 0 THEN 20
                ELSE 0
            END * 0.1)
        ) >= 90 THEN 'Cực kỳ tiềm năng'
        WHEN (
            -- Same formula...
            (CASE
                WHEN poi_count = 0 THEN 0
                WHEN poi_count = 1 THEN 30
                WHEN poi_count = 2 THEN 50
                WHEN poi_count = 3 THEN 65
                WHEN poi_count = 4 THEN 75
                WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
                WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
                ELSE 100
            END * 0.4) +
            (CASE
                WHEN highway IN ('primary', 'secondary') THEN 80
                WHEN highway = 'tertiary' THEN 70
                WHEN highway IN ('residential', 'unclassified') THEN 60
                WHEN highway = 'living_street' THEN 50
                WHEN highway IN ('motorway', 'trunk') THEN 30
                ELSE 20
            END * 0.2) +
            (CASE
                WHEN business_type_count >= 5 THEN 100
                WHEN business_type_count = 4 THEN 80
                WHEN business_type_count = 3 THEN 60
                WHEN business_type_count = 2 THEN 40
                WHEN business_type_count = 1 THEN 20
                ELSE 0
            END * 0.2) +
            (CASE
                WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
                WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
                WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
                WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
                ELSE 0
            END * 0.1) +
            (CASE
                WHEN poi_per_km >= 10 THEN 100
                WHEN poi_per_km >= 5 THEN 80
                WHEN poi_per_km >= 2 THEN 60
                WHEN poi_per_km >= 1 THEN 40
                WHEN poi_per_km > 0 THEN 20
                ELSE 0
            END * 0.1)
        ) >= 70 THEN 'Rất tiềm năng'
        WHEN (
            -- Same formula...
            (CASE
                WHEN poi_count = 0 THEN 0
                WHEN poi_count = 1 THEN 30
                WHEN poi_count = 2 THEN 50
                WHEN poi_count = 3 THEN 65
                WHEN poi_count = 4 THEN 75
                WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
                WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
                ELSE 100
            END * 0.4) +
            (CASE
                WHEN highway IN ('primary', 'secondary') THEN 80
                WHEN highway = 'tertiary' THEN 70
                WHEN highway IN ('residential', 'unclassified') THEN 60
                WHEN highway = 'living_street' THEN 50
                WHEN highway IN ('motorway', 'trunk') THEN 30
                ELSE 20
            END * 0.2) +
            (CASE
                WHEN business_type_count >= 5 THEN 100
                WHEN business_type_count = 4 THEN 80
                WHEN business_type_count = 3 THEN 60
                WHEN business_type_count = 2 THEN 40
                WHEN business_type_count = 1 THEN 20
                ELSE 0
            END * 0.2) +
            (CASE
                WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
                WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
                WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
                WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
                ELSE 0
            END * 0.1) +
            (CASE
                WHEN poi_per_km >= 10 THEN 100
                WHEN poi_per_km >= 5 THEN 80
                WHEN poi_per_km >= 2 THEN 60
                WHEN poi_per_km >= 1 THEN 40
                WHEN poi_per_km > 0 THEN 20
                ELSE 0
            END * 0.1)
        ) >= 50 THEN 'Tiềm năng cao'
        WHEN (
            -- Same formula...
            (CASE
                WHEN poi_count = 0 THEN 0
                WHEN poi_count = 1 THEN 30
                WHEN poi_count = 2 THEN 50
                WHEN poi_count = 3 THEN 65
                WHEN poi_count = 4 THEN 75
                WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
                WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
                ELSE 100
            END * 0.4) +
            (CASE
                WHEN highway IN ('primary', 'secondary') THEN 80
                WHEN highway = 'tertiary' THEN 70
                WHEN highway IN ('residential', 'unclassified') THEN 60
                WHEN highway = 'living_street' THEN 50
                WHEN highway IN ('motorway', 'trunk') THEN 30
                ELSE 20
            END * 0.2) +
            (CASE
                WHEN business_type_count >= 5 THEN 100
                WHEN business_type_count = 4 THEN 80
                WHEN business_type_count = 3 THEN 60
                WHEN business_type_count = 2 THEN 40
                WHEN business_type_count = 1 THEN 20
                ELSE 0
            END * 0.2) +
            (CASE
                WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
                WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
                WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
                WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
                ELSE 0
            END * 0.1) +
            (CASE
                WHEN poi_per_km >= 10 THEN 100
                WHEN poi_per_km >= 5 THEN 80
                WHEN poi_per_km >= 2 THEN 60
                WHEN poi_per_km >= 1 THEN 40
                WHEN poi_per_km > 0 THEN 20
                ELSE 0
            END * 0.1)
        ) >= 30 THEN 'Tiềm năng trung bình'
        WHEN (
            -- Same formula...
            (CASE
                WHEN poi_count = 0 THEN 0
                WHEN poi_count = 1 THEN 30
                WHEN poi_count = 2 THEN 50
                WHEN poi_count = 3 THEN 65
                WHEN poi_count = 4 THEN 75
                WHEN poi_count <= 7 THEN 80 + (poi_count - 4) * 3
                WHEN poi_count <= 20 THEN 90 + (poi_count - 7) * 0.5
                ELSE 100
            END * 0.4) +
            (CASE
                WHEN highway IN ('primary', 'secondary') THEN 80
                WHEN highway = 'tertiary' THEN 70
                WHEN highway IN ('residential', 'unclassified') THEN 60
                WHEN highway = 'living_street' THEN 50
                WHEN highway IN ('motorway', 'trunk') THEN 30
                ELSE 20
            END * 0.2) +
            (CASE
                WHEN business_type_count >= 5 THEN 100
                WHEN business_type_count = 4 THEN 80
                WHEN business_type_count = 3 THEN 60
                WHEN business_type_count = 2 THEN 40
                WHEN business_type_count = 1 THEN 20
                ELSE 0
            END * 0.2) +
            (CASE
                WHEN road_name ILIKE '%main%' OR road_name ILIKE '%broadway%' THEN 100
                WHEN road_name ILIKE '%1st%' OR road_name ILIKE '%first%' THEN 80
                WHEN road_name ILIKE '%2nd%' OR road_name ILIKE '%3rd%' THEN 70
                WHEN road_name ILIKE '%center%' OR road_name ILIKE '%central%' THEN 60
                ELSE 0
            END * 0.1) +
            (CASE
                WHEN poi_per_km >= 10 THEN 100
                WHEN poi_per_km >= 5 THEN 80
                WHEN poi_per_km >= 2 THEN 60
                WHEN poi_per_km >= 1 THEN 40
                WHEN poi_per_km > 0 THEN 20
                ELSE 0
            END * 0.1)
        ) >= 10 THEN 'Tiềm năng thấp'
        ELSE 'Không tiềm năng'
    END as potential_category
    
FROM road_metrics;

-- Create indexes for performance
CREATE INDEX idx_business_potential_state 
    ON road_business_potential(state_code);
CREATE INDEX idx_business_potential_score 
    ON road_business_potential(business_potential_score DESC);
CREATE INDEX idx_business_potential_osm_id 
    ON road_business_potential(osm_id);
CREATE INDEX idx_business_potential_composite 
    ON road_business_potential(state_code, business_potential_score DESC);
CREATE INDEX idx_business_potential_category 
    ON road_business_potential(potential_category);

-- Grant permissions
GRANT SELECT ON road_business_potential TO PUBLIC;

-- Show distribution
SELECT 
    potential_category,
    COUNT(*) as road_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM road_business_potential
GROUP BY potential_category
ORDER BY 
    CASE potential_category
        WHEN 'Cực kỳ tiềm năng' THEN 1
        WHEN 'Rất tiềm năng' THEN 2
        WHEN 'Tiềm năng cao' THEN 3
        WHEN 'Tiềm năng trung bình' THEN 4
        WHEN 'Tiềm năng thấp' THEN 5
        ELSE 6
    END;