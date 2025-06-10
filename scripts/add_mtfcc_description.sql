-- Add MTFCC description table for better filtering

CREATE TABLE IF NOT EXISTS mtfcc_descriptions (
    mtfcc VARCHAR(5) PRIMARY KEY,
    feature_class VARCHAR(100),
    description TEXT,
    business_likelihood VARCHAR(20) -- 'high', 'medium', 'low', 'none'
);

-- Insert MTFCC descriptions for roads
INSERT INTO mtfcc_descriptions (mtfcc, feature_class, description, business_likelihood) VALUES
-- High business likelihood
('S1100', 'Primary Road', 'Limited-access highways, Interstate highways, toll roads', 'high'),
('S1200', 'Secondary Road', 'Main arteries, US/State/County highways with at-grade intersections', 'high'),
('S1400', 'Local Neighborhood Road', 'Paved city streets, neighborhood roads, scenic park roads', 'high'),

-- Medium business likelihood  
('S1640', 'Service Drive', 'Roads parallel to limited access highways', 'medium'),
('S1780', 'Parking Lot Road', 'Main routes through parking areas, apartment/office complexes', 'medium'),

-- Low business likelihood
('S1730', 'Alley', 'Service roads behind buildings for deliveries, usually unnamed', 'low'),
('S1740', 'Private Road', 'Private property roads for logging, oil fields, ranches', 'low'),
('S1750', 'Internal Census Use', 'Internal U.S. Census Bureau use', 'low'),

-- No business (don't crawl)
('S1500', 'Vehicular Trail (4WD)', 'Unpaved dirt trails requiring 4WD vehicles', 'none'),
('S1630', 'Ramp', 'Highway on/off ramps, cloverleaf interchanges', 'none'),
('S1710', 'Walkway/Pedestrian Trail', 'Walking paths restricted from vehicles', 'none'),
('S1720', 'Stairway', 'Pedestrian stairways between levels', 'none'),
('S1810', 'Winter Trail', 'Seasonal snow trails for snowmobiles/dog sleds', 'none'),
('S1820', 'Bike Path or Trail', 'Bicycle paths restricted from vehicles', 'none'),
('S1830', 'Bridle Path', 'Horse paths restricted from vehicles', 'none');

-- Create view for road statistics with MTFCC descriptions
CREATE OR REPLACE VIEW road_statistics_by_type AS
SELECT 
    r.mtfcc,
    m.feature_class,
    m.description,
    m.business_likelihood,
    r.state_code,
    COUNT(*) as road_count,
    COUNT(DISTINCT r.fullname) as unique_road_names
FROM roads r
LEFT JOIN mtfcc_descriptions m ON r.mtfcc = m.mtfcc
GROUP BY r.mtfcc, m.feature_class, m.description, m.business_likelihood, r.state_code
ORDER BY r.state_code, m.business_likelihood DESC, road_count DESC;

-- Example queries:
-- Get road types in Jefferson County, AL
/*
SELECT 
    r.mtfcc,
    m.feature_class,
    m.business_likelihood,
    COUNT(DISTINCT r.fullname) as unique_roads,
    COUNT(*) as total_segments
FROM roads r
LEFT JOIN mtfcc_descriptions m ON r.mtfcc = m.mtfcc
WHERE r.county_fips = '01073'
GROUP BY r.mtfcc, m.feature_class, m.business_likelihood
ORDER BY m.business_likelihood DESC, total_segments DESC;
*/