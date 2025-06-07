-- Businesses table (OSM version)
CREATE TABLE IF NOT EXISTS businesses (
    id BIGSERIAL PRIMARY KEY,
    place_id VARCHAR(255) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    formatted_address TEXT,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    types TEXT[], -- Array of business types
    rating DECIMAL(2, 1),
    user_ratings_total INTEGER,
    price_level INTEGER CHECK (price_level >= 0 AND price_level <= 4),
    phone_number VARCHAR(50),
    website TEXT,
    opening_hours JSONB,
    
    -- Road association (OSM)
    road_osm_id BIGINT,
    road_name TEXT,
    distance_to_road DECIMAL(10, 2), -- meters
    
    -- Metadata
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'google_maps',
    
    -- Indexes
    CONSTRAINT valid_rating CHECK (rating >= 0 AND rating <= 5)
);

-- Indexes for performance
CREATE INDEX idx_businesses_road ON businesses(road_osm_id);
CREATE INDEX idx_businesses_location ON businesses USING GIST (
    ST_MakePoint(lng, lat)
);
CREATE INDEX idx_businesses_types ON businesses USING GIN(types);
CREATE INDEX idx_businesses_name ON businesses USING gin(name gin_trgm_ops);

-- Crawl jobs table (OSM version)
CREATE TABLE IF NOT EXISTS crawl_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_osm_id BIGINT,
    road_name TEXT,
    county_fips VARCHAR(5),
    state_code VARCHAR(2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    businesses_found INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Index for job processing
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_road ON crawl_jobs(road_osm_id);

-- View for business statistics by road (OSM version)
CREATE VIEW road_business_stats AS
SELECT 
    r.osm_id,
    r.name as road_name,
    r.highway as road_type,
    r.county_fips,
    r.state_code,
    COUNT(b.id) as business_count,
    ARRAY_AGG(DISTINCT unnest(b.types)) as business_types,
    AVG(b.rating) as avg_rating,
    AVG(b.distance_to_road) as avg_distance
FROM osm_roads_main r
LEFT JOIN businesses b ON r.osm_id = b.road_osm_id
GROUP BY r.osm_id, r.name, r.highway, r.county_fips, r.state_code;

-- Function to get nearby roads for a location (OSM version)
CREATE OR REPLACE FUNCTION get_nearby_roads(
    lat DECIMAL,
    lng DECIMAL, 
    radius_meters INTEGER DEFAULT 100
)
RETURNS TABLE (
    osm_id BIGINT,
    name TEXT,
    distance_meters DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.osm_id,
        r.name,
        ST_Distance(
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
            r.geometry::geography
        ) as distance_meters
    FROM osm_roads_main r
    WHERE ST_DWithin(
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
        r.geometry::geography,
        radius_meters
    )
    ORDER BY distance_meters
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;