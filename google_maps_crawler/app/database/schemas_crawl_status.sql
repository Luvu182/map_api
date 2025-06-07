-- Create table to track crawl status for each road-keyword combination
CREATE TABLE IF NOT EXISTS crawl_status (
    id SERIAL PRIMARY KEY,
    road_osm_id BIGINT NOT NULL,
    keyword TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    businesses_found INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint: one status per road-keyword combination
    UNIQUE(road_osm_id, keyword)
);

-- Index for fast lookups
CREATE INDEX idx_crawl_status_road ON crawl_status(road_osm_id);
CREATE INDEX idx_crawl_status_keyword ON crawl_status(keyword);
CREATE INDEX idx_crawl_status_status ON crawl_status(status);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_crawl_status_updated_at 
    BEFORE UPDATE ON crawl_status 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();