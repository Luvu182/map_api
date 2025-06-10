-- Smart Business Schema with Extended Fields for Google Maps Crawler Integration
-- Optimized for commercial POIs only with smart crawling features

-- Drop old tables if needed
-- DROP TABLE IF EXISTS osm_businesses CASCADE;
-- DROP TABLE IF EXISTS osm_business_payments CASCADE;
-- DROP TABLE IF EXISTS osm_business_tags CASCADE;

-- Main business table with extended fields
CREATE TABLE IF NOT EXISTS osm_businesses (
    -- Primary key
    osm_id BIGINT,
    osm_type VARCHAR(10), -- 'node' or 'way'
    
    -- Basic info
    name TEXT,
    brand TEXT,
    brand_wikidata TEXT,
    
    -- Business classification  
    business_type VARCHAR(20), -- shop, amenity, office, tourism, healthcare, craft
    business_subtype VARCHAR(50), -- supermarket, restaurant, bank, etc.
    
    -- Contact information
    phone TEXT,
    website TEXT,
    email TEXT,
    
    -- Full address
    housenumber TEXT,
    street TEXT,
    unit TEXT,
    city TEXT,
    state_code VARCHAR(2),
    postcode VARCHAR(10),
    county_fips VARCHAR(10),
    
    -- Operating info
    operator TEXT,
    operator_type VARCHAR(20), -- private, public, government
    opening_hours TEXT,
    is_24_7 BOOLEAN DEFAULT FALSE,
    
    -- Services (for restaurants/shops)
    drive_through BOOLEAN,
    takeaway BOOLEAN,
    delivery BOOLEAN,
    outdoor_seating BOOLEAN,
    
    -- Food specific
    cuisine TEXT, -- For restaurants: pizza, burger, chinese, etc.
    diet_vegetarian BOOLEAN,
    diet_vegan BOOLEAN,
    
    -- Facilities
    building_type VARCHAR(50),
    building_levels INTEGER,
    has_parking BOOLEAN,
    parking_type VARCHAR(50),
    capacity INTEGER,
    wheelchair_access VARCHAR(10), -- yes, no, limited
    has_wifi BOOLEAN,
    wifi_fee BOOLEAN, -- true = free wifi
    
    -- Verification & Quality
    check_date DATE,
    data_source TEXT DEFAULT 'OpenStreetMap',
    wikidata_id TEXT,
    business_score INTEGER DEFAULT 0, -- 0-100 importance score
    
    -- Alternative names
    alt_name TEXT,
    old_name TEXT,
    
    -- Spatial data
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geometry GEOMETRY(Point, 4326),
    
    -- Road association (for smart crawling)
    nearest_road_id BIGINT,
    nearest_road_name TEXT,
    distance_to_road_m FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (osm_id, osm_type)
);

-- Payment methods table (many-to-many)
CREATE TABLE IF NOT EXISTS osm_business_payments (
    osm_id BIGINT,
    osm_type VARCHAR(10),
    payment_method VARCHAR(50), -- cash, visa, mastercard, amex, apple_pay, bitcoin, etc.
    PRIMARY KEY (osm_id, osm_type, payment_method),
    FOREIGN KEY (osm_id, osm_type) REFERENCES osm_businesses(osm_id, osm_type) ON DELETE CASCADE
);

-- Additional tags storage for future use
CREATE TABLE IF NOT EXISTS osm_business_tags (
    osm_id BIGINT,
    osm_type VARCHAR(10),
    tags JSONB,
    PRIMARY KEY (osm_id, osm_type)
);

-- Brand aggregation table for fast lookups
CREATE TABLE IF NOT EXISTS osm_brands (
    brand TEXT PRIMARY KEY,
    brand_wikidata TEXT,
    business_type VARCHAR(20),
    business_subtype VARCHAR(50),
    total_locations INTEGER DEFAULT 0,
    states_present TEXT[], -- Array of state codes
    avg_score FLOAT,
    has_website_pct FLOAT, -- Percentage with websites
    has_hours_pct FLOAT,   -- Percentage with opening hours
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create optimized indexes
CREATE INDEX IF NOT EXISTS idx_osm_businesses_name ON osm_businesses(name);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_brand ON osm_businesses(brand);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_type ON osm_businesses(business_type, business_subtype);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_state ON osm_businesses(state_code);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_county ON osm_businesses(county_fips);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_city ON osm_businesses(state_code, city);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_postcode ON osm_businesses(postcode);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_geom ON osm_businesses USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_operator ON osm_businesses(operator);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_cuisine ON osm_businesses(cuisine) WHERE cuisine IS NOT NULL;

-- Smart indexes for crawler integration
CREATE INDEX IF NOT EXISTS idx_osm_businesses_score ON osm_businesses(business_score DESC);
CREATE INDEX IF NOT EXISTS idx_osm_businesses_24_7 ON osm_businesses(is_24_7) WHERE is_24_7 = TRUE;
CREATE INDEX IF NOT EXISTS idx_osm_businesses_has_parking ON osm_businesses(has_parking) WHERE has_parking = TRUE;
CREATE INDEX IF NOT EXISTS idx_osm_businesses_brand_state ON osm_businesses(brand, state_code) WHERE brand IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_osm_businesses_check_date ON osm_businesses(check_date DESC) WHERE check_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_osm_businesses_no_phone ON osm_businesses(business_type) WHERE phone IS NULL;
CREATE INDEX IF NOT EXISTS idx_osm_businesses_road ON osm_businesses(nearest_road_id) WHERE nearest_road_id IS NOT NULL;

-- Spatial indexes for performance
CREATE INDEX IF NOT EXISTS idx_osm_businesses_geog ON osm_businesses USING GIST(geography(geometry));

-- Function to calculate business density for an area
CREATE OR REPLACE FUNCTION calculate_business_density(
    center_point GEOMETRY,
    radius_m INTEGER DEFAULT 1000
) RETURNS TABLE(
    total_businesses INTEGER,
    chain_stores INTEGER,
    restaurants INTEGER,
    shops INTEGER,
    avg_score FLOAT,
    with_hours_pct FLOAT,
    recently_verified INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_businesses,
        COUNT(CASE WHEN brand IS NOT NULL THEN 1 END)::INTEGER as chain_stores,
        COUNT(CASE WHEN business_type = 'amenity' AND business_subtype IN ('restaurant', 'cafe', 'fast_food') THEN 1 END)::INTEGER as restaurants,
        COUNT(CASE WHEN business_type = 'shop' THEN 1 END)::INTEGER as shops,
        AVG(business_score)::FLOAT as avg_score,
        (COUNT(CASE WHEN opening_hours IS NOT NULL THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0) * 100)::FLOAT as with_hours_pct,
        COUNT(CASE WHEN check_date > CURRENT_DATE - INTERVAL '6 months' THEN 1 END)::INTEGER as recently_verified
    FROM osm_businesses
    WHERE ST_DWithin(geometry::geography, center_point::geography, radius_m);
END;
$$ LANGUAGE plpgsql;

-- Function to find best roads for crawling
CREATE OR REPLACE FUNCTION find_high_potential_roads(
    p_state_code VARCHAR DEFAULT NULL,
    p_min_businesses INTEGER DEFAULT 5,
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE(
    road_osm_id BIGINT,
    road_name TEXT,
    business_count INTEGER,
    chain_count INTEGER,
    avg_business_score FLOAT,
    needs_crawl_pct FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.osm_id as road_osm_id,
        r.name as road_name,
        COUNT(DISTINCT b.osm_id)::INTEGER as business_count,
        COUNT(DISTINCT b.osm_id) FILTER (WHERE b.brand IS NOT NULL)::INTEGER as chain_count,
        AVG(b.business_score)::FLOAT as avg_business_score,
        (COUNT(DISTINCT b.osm_id) FILTER (WHERE b.phone IS NULL)::FLOAT / 
         NULLIF(COUNT(DISTINCT b.osm_id), 0) * 100)::FLOAT as needs_crawl_pct
    FROM osm_roads_main r
    JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
    WHERE (p_state_code IS NULL OR r.state_code = p_state_code)
    GROUP BY r.osm_id, r.name
    HAVING COUNT(DISTINCT b.osm_id) >= p_min_businesses
    ORDER BY 
        COUNT(DISTINCT b.osm_id) DESC,
        AVG(b.business_score) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get brand locations for chain analysis
CREATE OR REPLACE FUNCTION get_brand_locations(
    p_brand TEXT,
    p_state_code VARCHAR DEFAULT NULL
) RETURNS TABLE(
    osm_id BIGINT,
    name TEXT,
    full_address TEXT,
    city TEXT,
    state_code VARCHAR,
    phone TEXT,
    website TEXT,
    opening_hours TEXT,
    has_drive_through BOOLEAN,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    nearest_road TEXT,
    business_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.osm_id,
        b.name,
        CONCAT_WS(' ', b.housenumber, b.street, b.unit) as full_address,
        b.city,
        b.state_code,
        b.phone,
        b.website,
        b.opening_hours,
        b.drive_through as has_drive_through,
        b.lat,
        b.lon,
        b.nearest_road_name as nearest_road,
        b.business_score
    FROM osm_businesses b
    WHERE b.brand = p_brand
    AND (p_state_code IS NULL OR b.state_code = p_state_code)
    ORDER BY b.state_code, b.city, b.business_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update brand stats
CREATE OR REPLACE FUNCTION update_brand_stats() RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert brand stats
    INSERT INTO osm_brands (
        brand, 
        brand_wikidata, 
        business_type, 
        business_subtype, 
        total_locations, 
        states_present,
        avg_score,
        has_website_pct,
        has_hours_pct
    )
    SELECT 
        NEW.brand,
        NEW.brand_wikidata,
        NEW.business_type,
        NEW.business_subtype,
        1,
        ARRAY[NEW.state_code],
        NEW.business_score,
        CASE WHEN NEW.website IS NOT NULL THEN 100.0 ELSE 0.0 END,
        CASE WHEN NEW.opening_hours IS NOT NULL THEN 100.0 ELSE 0.0 END
    WHERE NEW.brand IS NOT NULL
    ON CONFLICT (brand) DO UPDATE SET
        total_locations = osm_brands.total_locations + 1,
        states_present = CASE 
            WHEN NEW.state_code = ANY(osm_brands.states_present) 
            THEN osm_brands.states_present
            ELSE array_append(osm_brands.states_present, NEW.state_code)
        END,
        avg_score = (osm_brands.avg_score * osm_brands.total_locations + NEW.business_score) / (osm_brands.total_locations + 1),
        has_website_pct = (osm_brands.has_website_pct * osm_brands.total_locations + 
                          CASE WHEN NEW.website IS NOT NULL THEN 100.0 ELSE 0.0 END) / (osm_brands.total_locations + 1),
        has_hours_pct = (osm_brands.has_hours_pct * osm_brands.total_locations + 
                        CASE WHEN NEW.opening_hours IS NOT NULL THEN 100.0 ELSE 0.0 END) / (osm_brands.total_locations + 1),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for brand stats (only on insert to avoid double counting)
DROP TRIGGER IF EXISTS trigger_update_brand_stats ON osm_businesses;
CREATE TRIGGER trigger_update_brand_stats
AFTER INSERT ON osm_businesses
FOR EACH ROW
EXECUTE FUNCTION update_brand_stats();

-- Add columns for road association if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'osm_businesses' 
                   AND column_name = 'nearest_road_id') THEN
        ALTER TABLE osm_businesses ADD COLUMN nearest_road_id BIGINT;
        ALTER TABLE osm_businesses ADD COLUMN nearest_road_name TEXT;
        ALTER TABLE osm_businesses ADD COLUMN distance_to_road_m FLOAT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'osm_businesses' 
                   AND column_name = 'business_score') THEN
        ALTER TABLE osm_businesses ADD COLUMN business_score INTEGER DEFAULT 0;
    END IF;
END $$;