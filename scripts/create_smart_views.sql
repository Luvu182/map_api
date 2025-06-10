-- Materialized Views for Smart POI Analysis and Google Maps Crawler Integration

-- 1. Business density by road for smart crawling prioritization
CREATE MATERIALIZED VIEW IF NOT EXISTS road_business_density AS
SELECT 
    r.osm_id as road_id,
    r.name as road_name,
    r.state_code,
    r.county_fips,
    COUNT(DISTINCT b.osm_id) as total_businesses,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.brand IS NOT NULL) as chain_stores,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'shop') as shops,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'amenity' 
        AND b.business_subtype IN ('restaurant', 'cafe', 'fast_food', 'bar')) as food_drink,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'amenity' 
        AND b.business_subtype IN ('bank', 'pharmacy', 'fuel')) as essential_services,
    AVG(b.business_score) as avg_business_score,
    -- Data quality indicators
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.phone IS NULL) as missing_phone,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.website IS NULL) as missing_website,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.opening_hours IS NULL) as missing_hours,
    -- Crawl priority score (higher = more important to crawl)
    (COUNT(DISTINCT b.osm_id) * 10 + 
     COUNT(DISTINCT b.osm_id) FILTER (WHERE b.brand IS NOT NULL) * 20 +
     COUNT(DISTINCT b.osm_id) FILTER (WHERE b.phone IS NULL) * 5 +
     COALESCE(AVG(b.business_score), 0)) as crawl_priority_score
FROM osm_roads_main r
LEFT JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
GROUP BY r.osm_id, r.name, r.state_code, r.county_fips;

CREATE INDEX idx_road_density_priority ON road_business_density(crawl_priority_score DESC);
CREATE INDEX idx_road_density_state ON road_business_density(state_code);
CREATE INDEX idx_road_density_businesses ON road_business_density(total_businesses DESC);

-- 2. City-level business statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS city_business_stats AS
SELECT 
    tc.city_name,
    tc.state_code,
    COUNT(DISTINCT b.osm_id) as total_businesses,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.brand IS NOT NULL) as chain_stores,
    COUNT(DISTINCT b.brand) as unique_brands,
    -- Business type breakdown
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'shop') as shops,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'amenity') as amenities,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'office') as offices,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_type = 'tourism') as tourism,
    -- Popular categories
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_subtype = 'restaurant') as restaurants,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_subtype = 'supermarket') as supermarkets,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_subtype = 'convenience') as convenience_stores,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.business_subtype = 'fuel') as gas_stations,
    -- Data quality
    AVG(b.business_score) as avg_business_score,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.phone IS NOT NULL)::FLOAT / 
        NULLIF(COUNT(DISTINCT b.osm_id), 0) * 100 as phone_coverage_pct,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.website IS NOT NULL)::FLOAT / 
        NULLIF(COUNT(DISTINCT b.osm_id), 0) * 100 as website_coverage_pct,
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.opening_hours IS NOT NULL)::FLOAT / 
        NULLIF(COUNT(DISTINCT b.osm_id), 0) * 100 as hours_coverage_pct,
    -- Verification freshness
    COUNT(DISTINCT b.osm_id) FILTER (WHERE b.check_date > CURRENT_DATE - INTERVAL '6 months') as recently_verified,
    MAX(b.check_date) as latest_verification
FROM target_cities_346 tc
LEFT JOIN osm_businesses b ON tc.city_name = b.city AND tc.state_code = b.state_code
GROUP BY tc.city_name, tc.state_code;

CREATE INDEX idx_city_stats_state ON city_business_stats(state_code);
CREATE INDEX idx_city_stats_businesses ON city_business_stats(total_businesses DESC);

-- 3. Brand presence analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS brand_presence AS
SELECT 
    b.brand,
    b.brand_wikidata,
    COUNT(DISTINCT b.osm_id) as total_locations,
    COUNT(DISTINCT b.state_code) as states_count,
    COUNT(DISTINCT b.city || ',' || b.state_code) as cities_count,
    array_agg(DISTINCT b.state_code ORDER BY b.state_code) as states_list,
    -- Most common business type for this brand
    MODE() WITHIN GROUP (ORDER BY b.business_type) as primary_business_type,
    MODE() WITHIN GROUP (ORDER BY b.business_subtype) as primary_business_subtype,
    -- Data quality
    AVG(b.business_score) as avg_score,
    COUNT(b.phone) FILTER (WHERE b.phone IS NOT NULL)::FLOAT / COUNT(*) * 100 as phone_coverage_pct,
    COUNT(b.website) FILTER (WHERE b.website IS NOT NULL)::FLOAT / COUNT(*) * 100 as website_coverage_pct,
    COUNT(b.opening_hours) FILTER (WHERE b.opening_hours IS NOT NULL)::FLOAT / COUNT(*) * 100 as hours_coverage_pct,
    -- Services
    COUNT(*) FILTER (WHERE b.drive_through = TRUE) as drive_through_locations,
    COUNT(*) FILTER (WHERE b.delivery = TRUE) as delivery_locations,
    COUNT(*) FILTER (WHERE b.is_24_7 = TRUE) as always_open_locations
FROM osm_businesses b
WHERE b.brand IS NOT NULL
GROUP BY b.brand, b.brand_wikidata
HAVING COUNT(DISTINCT b.osm_id) >= 3;  -- Only brands with 3+ locations

CREATE INDEX idx_brand_presence_locations ON brand_presence(total_locations DESC);
CREATE INDEX idx_brand_presence_brand ON brand_presence(brand);

-- 4. Business clustering heatmap (grid-based)
CREATE MATERIALIZED VIEW IF NOT EXISTS business_cluster_grid AS
WITH grid_bounds AS (
    SELECT 
        ST_XMin(ST_Extent(geometry)) as xmin,
        ST_YMin(ST_Extent(geometry)) as ymin,
        ST_XMax(ST_Extent(geometry)) as xmax,
        ST_YMax(ST_Extent(geometry)) as ymax
    FROM osm_businesses
),
grid_cells AS (
    SELECT 
        ST_MakeEnvelope(
            xmin + (x * 0.01),  -- 0.01 degree grid cells (~1km)
            ymin + (y * 0.01),
            xmin + ((x + 1) * 0.01),
            ymin + ((y + 1) * 0.01),
            4326
        ) as cell_geom,
        x, y
    FROM grid_bounds,
         generate_series(0, CEIL((xmax - xmin) / 0.01)::int - 1) as x,
         generate_series(0, CEIL((ymax - ymin) / 0.01)::int - 1) as y
)
SELECT 
    g.x, g.y,
    g.cell_geom,
    COUNT(b.osm_id) as business_count,
    COUNT(DISTINCT b.brand) FILTER (WHERE b.brand IS NOT NULL) as unique_brands,
    COUNT(b.osm_id) FILTER (WHERE b.business_type = 'shop') as shops,
    COUNT(b.osm_id) FILTER (WHERE b.business_type = 'amenity' 
        AND b.business_subtype IN ('restaurant', 'cafe', 'fast_food')) as restaurants,
    AVG(b.business_score) as avg_score,
    -- Classify cluster type
    CASE 
        WHEN COUNT(b.osm_id) >= 50 THEN 'high_density'
        WHEN COUNT(b.osm_id) >= 20 THEN 'medium_density'
        WHEN COUNT(b.osm_id) >= 5 THEN 'low_density'
        ELSE 'sparse'
    END as density_class
FROM grid_cells g
LEFT JOIN osm_businesses b ON ST_Contains(g.cell_geom, b.geometry)
GROUP BY g.x, g.y, g.cell_geom
HAVING COUNT(b.osm_id) > 0;

CREATE INDEX idx_cluster_grid_geom ON business_cluster_grid USING GIST(cell_geom);
CREATE INDEX idx_cluster_grid_count ON business_cluster_grid(business_count DESC);

-- 5. Missing data opportunities (for targeted crawling)
CREATE MATERIALIZED VIEW IF NOT EXISTS crawl_opportunities AS
SELECT 
    b.osm_id,
    b.name,
    b.brand,
    b.business_type,
    b.business_subtype,
    b.city,
    b.state_code,
    b.nearest_road_name,
    b.business_score,
    -- What's missing
    CASE WHEN b.phone IS NULL THEN 1 ELSE 0 END as missing_phone,
    CASE WHEN b.website IS NULL THEN 1 ELSE 0 END as missing_website,
    CASE WHEN b.opening_hours IS NULL THEN 1 ELSE 0 END as missing_hours,
    CASE WHEN b.email IS NULL THEN 1 ELSE 0 END as missing_email,
    -- Priority score (higher = more important to crawl)
    b.business_score +
    CASE WHEN b.brand IS NOT NULL THEN 20 ELSE 0 END +
    CASE WHEN b.phone IS NULL THEN 10 ELSE 0 END +
    CASE WHEN b.website IS NULL THEN 5 ELSE 0 END +
    CASE WHEN b.opening_hours IS NULL THEN 5 ELSE 0 END as crawl_priority
FROM osm_businesses b
WHERE (b.phone IS NULL OR b.website IS NULL OR b.opening_hours IS NULL)
AND b.business_score >= 20;  -- Focus on important businesses

CREATE INDEX idx_crawl_opportunities_priority ON crawl_opportunities(crawl_priority DESC);
CREATE INDEX idx_crawl_opportunities_state ON crawl_opportunities(state_code);

-- 6. Cuisine diversity analysis (for food businesses)
CREATE MATERIALIZED VIEW IF NOT EXISTS cuisine_diversity AS
SELECT 
    COALESCE(b.city, 'Unknown') as city,
    b.state_code,
    b.cuisine,
    COUNT(*) as restaurant_count,
    COUNT(DISTINCT b.brand) as unique_brands,
    AVG(b.business_score) as avg_score,
    COUNT(*) FILTER (WHERE b.delivery = TRUE) as with_delivery,
    COUNT(*) FILTER (WHERE b.takeaway = TRUE) as with_takeaway,
    COUNT(*) FILTER (WHERE b.drive_through = TRUE) as with_drive_through
FROM osm_businesses b
WHERE b.cuisine IS NOT NULL
AND b.business_type = 'amenity'
AND b.business_subtype IN ('restaurant', 'fast_food', 'cafe')
GROUP BY b.city, b.state_code, b.cuisine
HAVING COUNT(*) >= 2;

CREATE INDEX idx_cuisine_city_state ON cuisine_diversity(state_code, city);
CREATE INDEX idx_cuisine_type ON cuisine_diversity(cuisine);

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_business_views() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY road_business_density;
    REFRESH MATERIALIZED VIEW CONCURRENTLY city_business_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY brand_presence;
    REFRESH MATERIALIZED VIEW CONCURRENTLY business_cluster_grid;
    REFRESH MATERIALIZED VIEW CONCURRENTLY crawl_opportunities;
    REFRESH MATERIALIZED VIEW CONCURRENTLY cuisine_diversity;
END;
$$ LANGUAGE plpgsql;

-- Usage examples:
-- Find roads with highest crawl priority:
-- SELECT * FROM road_business_density WHERE state_code = 'CA' ORDER BY crawl_priority_score DESC LIMIT 100;

-- Find cities with poor data coverage:
-- SELECT * FROM city_business_stats WHERE phone_coverage_pct < 50 ORDER BY total_businesses DESC;

-- Find major brands to prioritize:
-- SELECT * FROM brand_presence WHERE total_locations > 10 AND phone_coverage_pct < 50;

-- Find high-density business clusters:
-- SELECT * FROM business_cluster_grid WHERE density_class = 'high_density' ORDER BY business_count DESC;