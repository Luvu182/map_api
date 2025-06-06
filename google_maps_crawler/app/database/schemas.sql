-- Businesses table
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
    
    -- Road association
    road_linearid VARCHAR(30) REFERENCES roads(linearid),
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
CREATE INDEX idx_businesses_road ON businesses(road_linearid);
CREATE INDEX idx_businesses_location ON businesses USING GIST (
    ST_MakePoint(lng, lat)
);
CREATE INDEX idx_businesses_types ON businesses USING GIN(types);
CREATE INDEX idx_businesses_name ON businesses USING gin(name gin_trgm_ops);

-- Crawl jobs table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_linearid VARCHAR(30) REFERENCES roads(linearid),
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
CREATE INDEX idx_crawl_jobs_road ON crawl_jobs(road_linearid);

-- View for business statistics by road
CREATE VIEW road_business_stats AS
SELECT 
    r.linearid,
    r.fullname as road_name,
    r.road_category,
    r.county_fips,
    r.state_code,
    COUNT(b.id) as business_count,
    ARRAY_AGG(DISTINCT unnest(b.types)) as business_types,
    AVG(b.rating) as avg_rating,
    AVG(b.distance_to_road) as avg_distance
FROM roads r
LEFT JOIN businesses b ON r.linearid = b.road_linearid
GROUP BY r.linearid, r.fullname, r.road_category, r.county_fips, r.state_code;

-- Function to get nearby roads for a location
CREATE OR REPLACE FUNCTION get_nearby_roads(
    lat DECIMAL,
    lng DECIMAL, 
    radius_meters INTEGER DEFAULT 100
)
RETURNS TABLE (
    linearid VARCHAR,
    fullname TEXT,
    distance_meters DECIMAL
) AS $$
BEGIN
    -- This is a placeholder - would need PostGIS for actual implementation
    -- For now, return roads in the same county
    RETURN QUERY
    SELECT 
        r.linearid,
        r.fullname,
        0::DECIMAL as distance_meters
    FROM roads r
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;