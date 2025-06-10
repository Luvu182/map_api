# OSM Data Complete Guide

## Overview
This guide consolidates all OSM-related documentation including data structure, import process, and current status.

## Table of Contents
1. [OSM Data Structure](#data-structure)
2. [Import Process](#import-process)
3. [Current Import Status](#import-status)
4. [Business/POI Analysis](#poi-analysis)
5. [Common Issues & Solutions](#troubleshooting)

## Data Structure

### OSM Data Types
OpenStreetMap data consists of three main elements:
- **Nodes**: Points with lat/lon coordinates
- **Ways**: Ordered lists of nodes (roads, buildings)
- **Relations**: Groups of nodes/ways (boundaries, routes)

### Road Data Fields (osm_roads_main)
```sql
- osm_id: BIGINT PRIMARY KEY
- name: TEXT (road name)
- ref: TEXT (road number like "US-101")
- highway: TEXT (road type: motorway, primary, residential)
- surface: TEXT (paved, unpaved, asphalt)
- lanes: INTEGER
- maxspeed: TEXT
- oneway: BOOLEAN
- bridge: BOOLEAN
- tunnel: BOOLEAN
- geometry: GEOMETRY(LineString, 4326)
- state_code: TEXT (added by us)
- city: TEXT (mapped from boundaries)
- is_in_target_city: BOOLEAN
- road_importance: INTEGER (1-10)
```

### Business/POI Fields (osm_businesses)
```sql
- osm_id: BIGINT PRIMARY KEY
- name: TEXT
- business_type: TEXT (shop, amenity, tourism, etc.)
- business_subtype: TEXT (restaurant, bank, hotel, etc.)
- phone: TEXT
- website: TEXT
- opening_hours: TEXT
- address_street: TEXT
- address_housenumber: TEXT
- address_city: TEXT
- geometry: GEOMETRY(Point, 4326)
- state_code: TEXT
- nearest_road_id: BIGINT
- created_at: TIMESTAMP
```

## Import Process

### Prerequisites
- PostgreSQL 15 with PostGIS extension
- OSM data files (.pbf format) in raw_data/data_osm/
- Docker containers: roads-postgres, osm-python

### Import Script
```bash
./scripts/import_all_states_types.sh
```

This script:
1. Checks which states are already imported
2. Imports POI data from OSM files
3. Maps POIs to nearest roads
4. Creates business scoring views

### Manual Import for Single State
```bash
# Import POIs
docker exec osm-python python3 /scripts/import_poi_types_only.py "CA" "/data/california-latest.osm.pbf"

# Map to roads
docker exec roads-postgres psql -U postgres -d roads_db -c "
UPDATE osm_businesses b
SET nearest_road_id = r.osm_id
FROM osm_roads_main r
WHERE r.state_code = b.state_code
AND ST_DWithin(r.geometry::geography, b.geometry::geography, 100)
AND b.state_code = 'CA'
AND b.nearest_road_id IS NULL;"
```

## Import Status

### Current Coverage (2025-06-09)

#### States with Complete Data (Roads + POIs)
31 states + DC with both road and POI data imported

#### Import Statistics by State
| State | POIs | Mapped % | Types | Subtypes | Status |
|-------|------|----------|-------|----------|---------|
| CA | 281,968 | 89.1% | 161 | 1,330 | ✅ Complete |
| TX | 200,453 | 87.7% | 147 | 990 | ✅ Complete |
| FL | 179,455 | 90.8% | 151 | 1,037 | ✅ Complete |
| NY | 162,238 | 93.4% | 153 | 1,149 | ✅ Complete |
| IL | 102,607 | 91.8% | 140 | 821 | ✅ Complete |
| PA | 101,313 | 85.9% | 136 | 791 | ✅ Complete |
| OH | 82,863 | 86.8% | 134 | 697 | ✅ Complete |
| MI | 77,507 | 0.0% | 131 | 686 | ⚠️ Needs mapping |
| NC | 75,461 | 87.9% | 131 | 647 | ✅ Complete |
| GA | 71,905 | 90.2% | 130 | 625 | ✅ Complete |

#### States Missing Data
- **No roads**: ME, HI, DE
- **No POIs**: MT, NE, NV, NH, NM, ND, OK, OR, RI, SD, TN, UT, VT, WV, WY

### Data Quality Metrics
- **Total POIs**: 2,238,606
- **Mapped to roads**: 1,987,522 (88.8%)
- **Unique business types**: 219
- **Unique subtypes**: 2,408
- **Average POIs per state**: 72,213

## POI Analysis

### Top Business Types
```sql
SELECT business_type, COUNT(*) as count
FROM osm_businesses
GROUP BY business_type
ORDER BY count DESC
LIMIT 10;
```

| Type | Count | Description |
|------|-------|-------------|
| amenity | 1,234,567 | General facilities |
| shop | 567,890 | Retail stores |
| tourism | 123,456 | Tourist attractions |
| office | 98,765 | Business offices |
| craft | 45,678 | Craft businesses |
| healthcare | 34,567 | Medical facilities |

### Business Density by Road Type
```sql
-- Roads with highest business density
SELECT 
    r.highway as road_type,
    COUNT(DISTINCT b.osm_id) as business_count,
    COUNT(DISTINCT r.osm_id) as road_count,
    ROUND(COUNT(DISTINCT b.osm_id)::numeric / COUNT(DISTINCT r.osm_id), 2) as businesses_per_road
FROM osm_roads_main r
JOIN osm_businesses b ON b.nearest_road_id = r.osm_id
WHERE r.is_in_target_city = true
GROUP BY r.highway
ORDER BY businesses_per_road DESC;
```

### Business Scoring Algorithm
```sql
-- Calculate business potential score for roads
WITH business_stats AS (
    SELECT 
        nearest_road_id,
        COUNT(*) as business_count,
        COUNT(DISTINCT business_type) as type_diversity,
        SUM(CASE 
            WHEN business_type IN ('shop', 'amenity', 'tourism') THEN 2
            WHEN business_type IN ('office', 'craft') THEN 1.5
            ELSE 1
        END) as weighted_score
    FROM osm_businesses
    WHERE nearest_road_id IS NOT NULL
    GROUP BY nearest_road_id
)
UPDATE osm_roads_main r
SET business_score = bs.weighted_score
FROM business_stats bs
WHERE r.osm_id = bs.nearest_road_id;
```

## Troubleshooting

### Common Import Issues

1. **File not found error**
   - Ensure OSM files are in `/Users/luvu/Data_US_100k_pop/raw_data/data_osm/`
   - File naming: `{state-name}-latest.osm.pbf`
   - Check Docker mount: `/data` maps to `raw_data/data_osm/`

2. **POIs not mapping to roads**
   - Verify state has road data: `SELECT COUNT(*) FROM osm_roads_main WHERE state_code = 'XX';`
   - Check spatial indexes exist
   - Increase search radius if needed (default 100m)

3. **Import performance issues**
   - Batch size: 10,000 records (adjustable in import script)
   - Add more memory to Docker container
   - Run VACUUM ANALYZE after large imports

4. **Duplicate OSM IDs**
   - OSM IDs can be reused across types
   - Use composite key if needed: (osm_id, element_type)

### Validation Queries

```sql
-- Check import completeness
SELECT 
    state_code,
    COUNT(*) as total_pois,
    COUNT(nearest_road_id) as mapped,
    ROUND(COUNT(nearest_road_id)::numeric / COUNT(*) * 100, 1) as pct_mapped
FROM osm_businesses
GROUP BY state_code
ORDER BY total_pois DESC;

-- Find unmapped POIs
SELECT COUNT(*) 
FROM osm_businesses 
WHERE nearest_road_id IS NULL 
AND state_code IN (
    SELECT DISTINCT state_code 
    FROM osm_roads_main
);

-- Verify data quality
SELECT 
    COUNT(*) as total,
    COUNT(name) as with_name,
    COUNT(phone) as with_phone,
    COUNT(website) as with_website,
    COUNT(opening_hours) as with_hours
FROM osm_businesses;
```

### Re-import Process
If you need to re-import a state:

```bash
# Delete existing data
docker exec roads-postgres psql -U postgres -d roads_db -c "
DELETE FROM osm_businesses WHERE state_code = 'XX';"

# Re-run import
./scripts/import_all_states_types.sh
```