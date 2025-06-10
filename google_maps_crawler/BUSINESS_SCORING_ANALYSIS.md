# Business Potential Scoring Analysis Report

## Executive Summary

After analyzing the current implementation and available data, I've found that the system uses multiple scoring approaches:

1. **Current Frontend Scoring** (in `get_top_business_roads`): Based on road type, name patterns, and length
2. **Mentioned Formula**: Uses POI counts (20+ = 10, 10-19 = 8, <10 = count * 0.5)
3. **Available Data**: OSM business data exists for AL (23,793) and CA (145,971)

## Current Scoring System Analysis

### Frontend Scoring Components

The current `get_top_business_roads` function uses:

```sql
-- Base score by highway type
CASE
    WHEN highway IN ('primary', 'secondary') THEN 40
    WHEN highway IN ('tertiary', 'residential') THEN 30
    WHEN highway = 'living_street' THEN 25
    WHEN highway IN ('motorway', 'trunk') THEN 15
    WHEN highway = 'unclassified' THEN 10
    WHEN highway = 'service' THEN 5
    WHEN highway IN ('footway', 'cycleway', 'path', 'track') THEN 0
    ELSE 3
END

-- Bonus for commercial-sounding names
+ CASE
    WHEN name LIKE '%(main|broadway|market|commercial|plaza|center)%' THEN 30
    WHEN name LIKE '%(1st|first|2nd|second|3rd|third)%' THEN 20
    WHEN name LIKE '%business%' THEN 25
    ELSE 0
END

-- Bonus for optimal road length
+ CASE
    WHEN length BETWEEN 2-5 km THEN 20
    WHEN length BETWEEN 1-2 km THEN 15
    WHEN length BETWEEN 0.5-1 km THEN 10
    ELSE 5
END
```

### Issues with Current Approach

1. **No actual business data integration** - Scoring is based on assumptions, not real POI/business counts
2. **Name-based scoring is unreliable** - "Main Street" might have no businesses in a small town
3. **Length scoring is arbitrary** - Longer roads aren't necessarily more commercial

## Recommended Scoring Formula

Based on the analysis, here's a data-driven approach that combines road characteristics with actual business density:

### Option 1: Hybrid Score (Recommended)

```sql
-- Combines actual business count with road type weighting
CASE
    -- High-value commercial roads
    WHEN highway IN ('primary', 'secondary', 'tertiary') THEN
        CASE
            WHEN business_count >= 20 THEN 100
            WHEN business_count >= 10 THEN 85 + business_count * 0.75
            WHEN business_count >= 5 THEN 70 + business_count * 2
            WHEN business_count >= 1 THEN 50 + business_count * 4
            ELSE 40  -- Base score for major roads even without businesses
        END
    
    -- Mixed-use roads
    WHEN highway IN ('residential', 'unclassified', 'living_street') THEN
        CASE
            WHEN business_count >= 15 THEN 90
            WHEN business_count >= 8 THEN 75 + business_count
            WHEN business_count >= 3 THEN 50 + business_count * 3
            WHEN business_count >= 1 THEN 30 + business_count * 5
            ELSE 20  -- Base score for potential
        END
    
    -- Low-priority roads
    ELSE
        CASE
            WHEN business_count >= 10 THEN 70
            WHEN business_count >= 5 THEN 50 + business_count * 2
            WHEN business_count >= 1 THEN 20 + business_count * 5
            ELSE 0
        END
END AS business_potential_score
```

### Option 2: Pure Data-Driven Score

```sql
-- Based purely on business density percentiles
CASE
    WHEN business_count = 0 THEN 0
    WHEN business_count = 1 THEN 30    -- Has business presence
    WHEN business_count = 2 THEN 45    -- Multiple businesses
    WHEN business_count <= 5 THEN 50 + business_count * 5  -- 55-75
    WHEN business_count <= 10 THEN 70 + (business_count - 5) * 3  -- 73-85
    WHEN business_count <= 20 THEN 85 + (business_count - 10) * 1  -- 86-95
    ELSE 95 + LEAST(5, (business_count - 20) * 0.25)  -- 95-100 cap
END AS business_potential_score
```

### Option 3: Simple Linear Scale

```sql
-- Simple and predictable
LEAST(100, business_count * 5)
```

## Implementation Recommendations

### 1. Create Materialized View for Performance

```sql
CREATE MATERIALIZED VIEW road_business_scores AS
WITH business_counts AS (
    SELECT 
        r.osm_id,
        r.name,
        r.highway,
        r.state_code,
        r.county_fips,
        COUNT(DISTINCT b.osm_id) as business_count,
        STRING_AGG(DISTINCT b.business_type, ', ' ORDER BY b.business_type) as business_types
    FROM osm_roads_main r
    LEFT JOIN osm_businesses b 
        ON r.state_code = b.state_code 
        AND ST_DWithin(r.geometry, b.geometry, 50)
    WHERE r.name IS NOT NULL
    GROUP BY r.osm_id, r.name, r.highway, r.state_code, r.county_fips
)
SELECT 
    *,
    -- Use Option 1 hybrid scoring
    [scoring formula here] as business_potential_score
FROM business_counts;

CREATE INDEX idx_road_business_scores_state ON road_business_scores(state_code);
CREATE INDEX idx_road_business_scores_score ON road_business_scores(business_potential_score DESC);
```

### 2. Update get_top_business_roads Function

Modify the function to use the materialized view instead of calculating scores on the fly.

### 3. Consider Additional Factors

For even better scoring, consider:
- **Competition density**: Too many similar businesses might reduce potential
- **Population density**: Available from census data
- **Traffic patterns**: If available from state DOT
- **Zoning information**: Commercial vs residential zones

## Conclusion

The current scoring system makes reasonable assumptions but lacks integration with actual business data. By implementing the hybrid scoring approach (Option 1), you can:

1. Maintain reasonable scores for roads without business data
2. Boost scores significantly when actual businesses are present
3. Account for road type differences (major roads vs residential)
4. Provide more accurate business potential predictions

The key insight from the analysis is that most roads (>90%) have 0-5 businesses, so the scoring formula should be sensitive in this range while not over-weighting outliers with 20+ businesses.