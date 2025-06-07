# OpenStreetMap Data Guide

## Overview
This guide explains how to use OpenStreetMap (OSM) data for the US Roads & Business Data project.

## Why OSM Over TIGER?

### Road Names
| TIGER | OSM | Google Maps |
|-------|-----|-------------|
| US Hwy 101 | Bayshore Freeway | Bayshore Freeway ✓ |
| I- 5 | Golden State Freeway | Golden State Freeway ✓ |
| State Rte 1 | Pacific Coast Highway | Pacific Coast Highway ✓ |

### Classification System
- **TIGER**: 15 numeric codes (S1100, S1200, etc.)
- **OSM**: 47+ descriptive types (residential, primary, motorway, etc.)

### Additional Data
- Speed limits (33% coverage)
- Number of lanes (52% coverage)
- Surface type (paved/unpaved)
- Alternative names

## OSM Data Structure

### Key Fields
```python
{
    "osm_id": 12345,              # Unique OSM way ID
    "name": "Main Street",         # Primary name
    "highway": "residential",      # Road type
    "ref": "US 101",              # Highway reference
    "lanes": 2,                   # Number of lanes
    "maxspeed": "35 mph",         # Speed limit
    "surface": "asphalt",         # Road surface
    "alt_name": "Old Main St"     # Alternative name
}
```

### Road Types for Business Crawling

#### High Value (Most businesses)
- `residential` - Neighborhood streets with local shops
- `tertiary` - Minor roads with businesses
- `secondary` - Major local roads, strip malls
- `primary` - Main roads through towns

#### Medium Value
- `trunk` - Major highways with some exits
- `unclassified` - Minor roads, may have rural businesses

#### Low Value
- `motorway` - Interstate highways (gas stations only)
- `service` - Parking lots, driveways
- `*_link` - Highway ramps (no businesses)

#### No Value (Skip these)
- `footway`, `cycleway`, `path` - No vehicle access
- `track` - Unpaved rural tracks
- `bridleway` - Horse trails
- `steps` - Stairs

## Data Processing Workflow

### 1. Download OSM Data
```bash
# State-level data already downloaded to:
/raw_data/data_osm/
├── california-latest.osm.pbf    # 1.2GB
├── texas-latest-free.shp.zip
├── florida-latest-free.shp.zip
└── ... (48 more states)
```

### 2. Extract Roads
```bash
# Using Docker container
docker-compose -f docker-compose-osm.yml up -d

# Extract roads from PBF
docker exec osm-processor osmium tags-filter \
  /data/california-latest.osm.pbf \
  w/highway \
  -o /output/california-roads.osm.pbf

# Convert to GeoJSON
docker exec osm-processor osmium export \
  /output/california-roads.osm.pbf \
  -o /output/california-roads.geojson
```

### 3. Import to Database
```python
import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine

# Read GeoJSON
gdf = gpd.read_file('california-roads.geojson')

# Filter business-relevant roads
business_roads = gdf[
    gdf['highway'].isin([
        'residential', 'tertiary', 'secondary', 
        'primary', 'trunk', 'unclassified'
    ]) & 
    gdf['name'].notna()
]

# Import to PostgreSQL
engine = create_engine('postgresql://user:pass@localhost/roads_db')
business_roads.to_postgis('osm_roads', engine)
```

### 4. Deduplicate Roads
```sql
-- Group segments by name
CREATE TABLE osm_unique_roads AS
SELECT 
    name,
    highway as road_type,
    COUNT(*) as segment_count,
    STRING_AGG(DISTINCT ref, ', ') as highway_refs,
    AVG(CAST(regexp_replace(maxspeed, '[^0-9]', '', 'g') AS INT)) as avg_speed_mph,
    MAX(lanes::INT) as max_lanes,
    county_fips,
    state_code
FROM osm_roads
WHERE name IS NOT NULL
GROUP BY name, highway, county_fips, state_code;
```

## Query Examples

### Find Business-Friendly Roads
```sql
-- Roads good for crawling
SELECT * FROM osm_unique_roads
WHERE road_type IN ('residential', 'tertiary', 'secondary', 'primary')
AND (avg_speed_mph IS NULL OR avg_speed_mph <= 45)
ORDER BY segment_count DESC;
```

### Find Major Commercial Corridors
```sql
-- Multi-lane roads with businesses
SELECT * FROM osm_unique_roads
WHERE max_lanes >= 4
AND road_type IN ('primary', 'secondary')
ORDER BY name;
```

### Skip These Roads
```sql
-- Roads unlikely to have businesses
SELECT * FROM osm_roads
WHERE highway IN ('motorway', 'service', 'footway', 'cycleway')
OR highway LIKE '%_link'
OR surface IN ('unpaved', 'dirt', 'gravel');
```

## Frontend Integration

### Display Road Info
```javascript
const RoadItem = ({ road }) => (
  <div className="road-item">
    <h3>{road.name}</h3>
    <div className="road-meta">
      <span className="road-type">{road.road_type}</span>
      {road.highway_refs && (
        <span className="highway-ref">{road.highway_refs}</span>
      )}
      {road.max_lanes && (
        <span className="lanes">{road.max_lanes} lanes</span>
      )}
      {road.avg_speed_mph && (
        <span className="speed">{road.avg_speed_mph} mph avg</span>
      )}
    </div>
    <div className="segments">
      {road.segment_count} segments
    </div>
  </div>
);
```

### Filter Options
```javascript
const filters = {
  roadTypes: [
    { value: 'residential', label: 'Residential Streets', checked: true },
    { value: 'tertiary', label: 'Local Roads', checked: true },
    { value: 'secondary', label: 'Major Roads', checked: true },
    { value: 'primary', label: 'Primary Roads', checked: true },
    { value: 'trunk', label: 'Highways', checked: false },
    { value: 'motorway', label: 'Interstates', checked: false }
  ],
  maxSpeed: 45,  // mph
  minLanes: 2,
  mustHaveName: true
};
```

## Best Practices

### 1. Always Filter Named Roads
```sql
WHERE name IS NOT NULL AND name != ''
```

### 2. Group by Name to Avoid Duplicates
OSM splits roads into many segments. Always group by name for display.

### 3. Use Speed Limits for Filtering
Roads with speed > 45 mph typically have fewer walkable businesses.

### 4. Prioritize by Road Type
1. First: residential, tertiary
2. Second: secondary, primary  
3. Last: trunk, motorway

### 5. Handle Name Variations
```python
# Common suffixes to normalize
replacements = {
    ' St': ' Street',
    ' Ave': ' Avenue',
    ' Blvd': ' Boulevard',
    ' Hwy': ' Highway',
    ' Rd': ' Road'
}
```

## Troubleshooting

### Issue: Too Many Segments
**Solution**: Always use `GROUP BY name` when displaying

### Issue: Missing Roads
**Solution**: Check if filtering too aggressively. Some rural areas have businesses on 'unclassified' roads.

### Issue: Wrong Names for Google
**Solution**: Use the primary `name` field, not `ref`. OSM names match Google better.

### Issue: Slow Queries
**Solution**: Create indexes:
```sql
CREATE INDEX idx_osm_roads_name ON osm_roads(name);
CREATE INDEX idx_osm_roads_highway ON osm_roads(highway);
CREATE INDEX idx_osm_roads_county ON osm_roads(county_fips);
```