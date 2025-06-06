-- Drop existing tables if they exist
DROP TABLE IF EXISTS roads CASCADE;
DROP TABLE IF EXISTS counties CASCADE;
DROP TABLE IF EXISTS cities CASCADE;
DROP TABLE IF EXISTS states CASCADE;

-- States table
CREATE TABLE states (
    state_code VARCHAR(2) PRIMARY KEY,
    state_name VARCHAR(50) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Counties table
CREATE TABLE counties (
    county_fips VARCHAR(5) PRIMARY KEY,
    county_name VARCHAR(100),
    state_code VARCHAR(2) REFERENCES states(state_code),
    total_roads INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cities table
CREATE TABLE cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    state_code VARCHAR(2) REFERENCES states(state_code),
    population INTEGER,
    total_roads INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- City-County mapping table (many-to-many)
CREATE TABLE city_counties (
    city_id INTEGER REFERENCES cities(city_id),
    county_fips VARCHAR(5) REFERENCES counties(county_fips),
    PRIMARY KEY (city_id, county_fips)
);

-- Main roads table
CREATE TABLE roads (
    id BIGSERIAL PRIMARY KEY,
    linearid VARCHAR(30) UNIQUE NOT NULL,
    fullname TEXT,
    rttyp VARCHAR(1),
    mtfcc VARCHAR(5),
    road_category VARCHAR(20),
    county_fips VARCHAR(5) REFERENCES counties(county_fips),
    state_code VARCHAR(2) REFERENCES states(state_code),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable trigram extension for fuzzy search FIRST
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create indexes for performance
CREATE INDEX idx_roads_fullname ON roads(fullname);
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_state ON roads(state_code);
CREATE INDEX idx_roads_category ON roads(road_category);
CREATE INDEX idx_roads_mtfcc ON roads(mtfcc);

-- Create full-text search index for road names (AFTER enabling pg_trgm)
CREATE INDEX idx_roads_fullname_trgm ON roads USING gin(fullname gin_trgm_ops);

-- Create view for easy city roads access
CREATE VIEW city_roads AS
SELECT 
    c.city_name,
    c.state_code,
    r.linearid,
    r.fullname,
    r.rttyp,
    r.mtfcc,
    r.road_category,
    r.county_fips
FROM roads r
JOIN city_counties cc ON r.county_fips = cc.county_fips
JOIN cities c ON cc.city_id = c.city_id;

-- Create materialized view for road statistics
CREATE MATERIALIZED VIEW road_statistics AS
SELECT 
    s.state_code,
    s.state_name,
    COUNT(DISTINCT c.county_fips) as county_count,
    COUNT(r.id) as total_roads,
    COUNT(CASE WHEN r.mtfcc = 'S1100' THEN 1 END) as primary_roads,
    COUNT(CASE WHEN r.mtfcc = 'S1200' THEN 1 END) as secondary_roads,
    COUNT(CASE WHEN r.mtfcc = 'S1400' THEN 1 END) as local_streets,
    COUNT(CASE WHEN r.mtfcc NOT IN ('S1100', 'S1200', 'S1400') THEN 1 END) as special_roads
FROM states s
LEFT JOIN counties c ON s.state_code = c.state_code
LEFT JOIN roads r ON c.county_fips = r.county_fips
GROUP BY s.state_code, s.state_name;

-- Create function to search roads by name
CREATE OR REPLACE FUNCTION search_roads(search_term TEXT, limit_count INTEGER DEFAULT 100)
RETURNS TABLE (
    linearid VARCHAR,
    fullname TEXT,
    road_category VARCHAR,
    county_fips VARCHAR,
    state_code VARCHAR,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.linearid,
        r.fullname,
        r.road_category,
        r.county_fips,
        r.state_code,
        similarity(r.fullname, search_term) AS similarity
    FROM roads r
    WHERE r.fullname % search_term  -- trigram similarity
    ORDER BY similarity DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create RLS (Row Level Security) policies if needed
ALTER TABLE roads ENABLE ROW LEVEL SECURITY;
ALTER TABLE counties ENABLE ROW LEVEL SECURITY;
ALTER TABLE cities ENABLE ROW LEVEL SECURITY;
ALTER TABLE states ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous access (read-only)
CREATE POLICY "Enable read access for all users" ON roads FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON counties FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON cities FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON states FOR SELECT USING (true);