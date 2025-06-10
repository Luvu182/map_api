-- Table to track API calls
CREATE TABLE IF NOT EXISTS api_calls (
    id SERIAL PRIMARY KEY,
    api_type VARCHAR(50) NOT NULL, -- 'text_search', 'place_details', 'geocoding', etc.
    endpoint VARCHAR(255),
    request_count INTEGER DEFAULT 1, -- For Text Search with 60 results = 3 requests
    session_id VARCHAR(255),
    road_osm_id BIGINT,
    keyword VARCHAR(255),
    response_count INTEGER, -- Number of results returned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX idx_api_calls_created_at ON api_calls(created_at);
CREATE INDEX idx_api_calls_api_type ON api_calls(api_type);
CREATE INDEX idx_api_calls_session_id ON api_calls(session_id);

-- View for API call statistics
CREATE OR REPLACE VIEW api_usage_stats AS
SELECT 
    api_type,
    COUNT(*) as total_calls,
    SUM(request_count) as total_requests,
    SUM(response_count) as total_results,
    DATE(created_at) as date
FROM api_calls
GROUP BY api_type, DATE(created_at);