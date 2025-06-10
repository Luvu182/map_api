-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- States table
CREATE TABLE IF NOT EXISTS states (
    state_code CHAR(2) PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    total_counties INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Counties table
CREATE TABLE IF NOT EXISTS counties (
    county_fips CHAR(5) PRIMARY KEY,
    county_name VARCHAR(100) NOT NULL,
    state_code CHAR(2) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code)
);

-- Roads table with PostGIS geometry
CREATE TABLE IF NOT EXISTS roads (
    id BIGSERIAL PRIMARY KEY,
    linearid VARCHAR(22) NOT NULL,
    fullname VARCHAR(100),
    rttyp VARCHAR(1),
    mtfcc VARCHAR(5),
    state_code CHAR(2) NOT NULL,
    county_fips CHAR(5) NOT NULL,
    geom GEOMETRY(LINESTRING, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips)
);

-- Cities table (for future use)
CREATE TABLE IF NOT EXISTS cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    state_code CHAR(2) NOT NULL,
    county_fips CHAR(5),
    population INTEGER,
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips)
);

-- Businesses table (for Google Maps crawler data)
CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    place_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    rating DECIMAL(2, 1),
    user_ratings_total INTEGER,
    types TEXT[],
    phone VARCHAR(50),
    website TEXT,
    opening_hours JSONB,
    price_level INTEGER,
    road_linearid VARCHAR(22),
    county_fips CHAR(5),
    state_code CHAR(2),
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips),
    FOREIGN KEY (state_code) REFERENCES states(state_code)
);

-- Crawl status table
CREATE TABLE IF NOT EXISTS crawl_status (
    id SERIAL PRIMARY KEY,
    county_fips CHAR(5) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    crawled_roads INTEGER DEFAULT 0,
    total_businesses INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips)
);

-- Create indexes
CREATE INDEX idx_roads_linearid ON roads(linearid);
CREATE INDEX idx_roads_fullname ON roads(fullname);
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_state ON roads(state_code);
CREATE INDEX idx_roads_geom ON roads USING GIST(geom);

-- Text search indexes
CREATE INDEX idx_roads_fullname_trgm ON roads USING GIN (fullname gin_trgm_ops);

-- Business indexes
CREATE INDEX idx_businesses_county ON businesses(county_fips);
CREATE INDEX idx_businesses_state ON businesses(state_code);
CREATE INDEX idx_businesses_location ON businesses(latitude, longitude);
CREATE INDEX idx_businesses_road ON businesses(road_linearid);

-- Crawl status indexes
CREATE INDEX idx_crawl_status_county ON crawl_status(county_fips);
CREATE INDEX idx_crawl_status_status ON crawl_status(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_states_updated_at BEFORE UPDATE ON states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_counties_updated_at BEFORE UPDATE ON counties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cities_updated_at BEFORE UPDATE ON cities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crawl_status_updated_at BEFORE UPDATE ON crawl_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();