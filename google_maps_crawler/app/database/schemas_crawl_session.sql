-- Crawl sessions table to track each crawl attempt
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    road_osm_id BIGINT NOT NULL,
    road_name VARCHAR(255),
    city_name VARCHAR(100),
    state_code VARCHAR(2),
    keyword VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, crawling, completed, failed
    businesses_found INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    api_calls_made INTEGER DEFAULT 0,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Index for fast lookups
CREATE INDEX idx_crawl_sessions_road ON crawl_sessions(road_osm_id);
CREATE INDEX idx_crawl_sessions_status ON crawl_sessions(status);
CREATE INDEX idx_crawl_sessions_created ON crawl_sessions(started_at DESC);

-- Update businesses table to link to crawl session
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS crawl_session_id UUID;
ALTER TABLE businesses ADD CONSTRAINT fk_crawl_session 
    FOREIGN KEY (crawl_session_id) REFERENCES crawl_sessions(id);

-- Index for fast session lookups
CREATE INDEX idx_businesses_session ON businesses(crawl_session_id);