-- Script to run mapping state by state, skipping completed ones

-- First check what's already done
WITH mapping_status AS (
    SELECT 
        state_code,
        COUNT(DISTINCT city_name) as cities_mapped,
        COUNT(*) as total_segments
    FROM road_city_mapping
    GROUP BY state_code
),
target_status AS (
    SELECT 
        state_code,
        COUNT(*) as target_cities
    FROM target_cities_346
    GROUP BY state_code
)
SELECT 
    t.state_code,
    t.target_cities,
    COALESCE(m.cities_mapped, 0) as cities_mapped,
    COALESCE(m.total_segments, 0) as segments_mapped,
    CASE 
        WHEN COALESCE(m.cities_mapped, 0) >= t.target_cities THEN 'COMPLETE'
        WHEN COALESCE(m.cities_mapped, 0) > 0 THEN 'PARTIAL'
        ELSE 'NOT STARTED'
    END as status
FROM target_status t
LEFT JOIN mapping_status m ON t.state_code = m.state_code
ORDER BY t.state_code;

-- Run mapping for states not complete
DO $$
DECLARE
    v_state RECORD;
    v_result RECORD;
    v_error_count INTEGER := 0;
BEGIN
    -- Get states that need mapping
    FOR v_state IN 
        WITH need_mapping AS (
            SELECT DISTINCT tc.state_code
            FROM target_cities_346 tc
            WHERE NOT EXISTS (
                -- Skip states that are already complete
                SELECT 1 
                FROM (
                    SELECT state_code, COUNT(DISTINCT city_name) as mapped
                    FROM road_city_mapping
                    GROUP BY state_code
                ) m
                WHERE m.state_code = tc.state_code
                    AND m.mapped >= (
                        SELECT COUNT(*) 
                        FROM target_cities_346 
                        WHERE state_code = tc.state_code
                    )
            )
            AND tc.state_code NOT IN ('AK', 'AL', 'AR') -- Already confirmed complete
            ORDER BY tc.state_code
        )
        SELECT * FROM need_mapping
    LOOP
        BEGIN
            RAISE NOTICE '';
            RAISE NOTICE '========================================';
            RAISE NOTICE 'Processing state: %', v_state.state_code;
            RAISE NOTICE '========================================';
            
            -- Clear any partial data for this state
            DELETE FROM road_city_mapping WHERE state_code = v_state.state_code;
            
            -- Run mapping for this state
            SELECT * INTO v_result
            FROM map_roads_to_target_cities_fixed(v_state.state_code);
            
            RAISE NOTICE 'State % COMPLETED: % cities, % segments', 
                v_state.state_code, v_result.cities_covered, v_result.roads_mapped;
            
        EXCEPTION 
            WHEN unique_violation THEN
                RAISE WARNING 'State % had duplicate key errors', v_state.state_code;
                v_error_count := v_error_count + 1;
                IF v_error_count > 5 THEN
                    RAISE EXCEPTION 'Too many errors, stopping';
                END IF;
            WHEN OTHERS THEN
                RAISE WARNING 'State % error: %', v_state.state_code, SQLERRM;
                v_error_count := v_error_count + 1;
                IF v_error_count > 5 THEN
                    RAISE EXCEPTION 'Too many errors, stopping';
                END IF;
        END;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE 'Mapping process completed!';
END $$;

-- Final summary
SELECT 
    COUNT(DISTINCT state_code) as states_mapped,
    COUNT(DISTINCT city_name || state_code) as cities_mapped,
    COUNT(*) as total_segments,
    pg_size_pretty(pg_total_relation_size('road_city_mapping')) as table_size
FROM road_city_mapping;

-- Show top 10 cities by road count
SELECT 
    city_name,
    state_code,
    COUNT(*) as road_segments,
    COUNT(DISTINCT osm_id) as unique_roads
FROM road_city_mapping
GROUP BY city_name, state_code
ORDER BY road_segments DESC
LIMIT 10;