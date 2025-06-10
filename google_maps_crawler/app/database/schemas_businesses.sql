-- Businesses table to store crawled data
CREATE TABLE IF NOT EXISTS businesses (
    place_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    formatted_address TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    types TEXT[],
    rating DECIMAL(2,1),
    user_ratings_total INTEGER,
    price_level INTEGER,
    phone_number VARCHAR(50),
    website TEXT,
    opening_hours JSONB,
    road_osm_id BIGINT,
    road_name VARCHAR(255),
    distance_to_road FLOAT DEFAULT 0,
    city VARCHAR(100),
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    crawl_session_id UUID,
    FOREIGN KEY (crawl_session_id) REFERENCES crawl_sessions(id)
);

-- Indexes for performance
CREATE INDEX idx_businesses_road ON businesses(road_osm_id);
CREATE INDEX idx_businesses_session ON businesses(crawl_session_id);
CREATE INDEX idx_businesses_city ON businesses(city);
CREATE INDEX idx_businesses_rating ON businesses(rating DESC);
CREATE INDEX idx_businesses_crawled ON businesses(crawled_at DESC);