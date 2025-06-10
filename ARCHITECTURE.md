# Kiến trúc Phân Cấp Dữ Liệu

## Hệ thống 4 cấp

### Cấp 1: State (Bang)
- 50 bang + DC
- Mã: State FIPS code (2 chữ số)
- Ví dụ: 01 = Alabama, 06 = California

### Cấp 2: County (Quận/Huyện)  
- Mỗi bang có nhiều county
- Mã: County FIPS code (3 chữ số)
- Full code: State + County (5 chữ số)
- Ví dụ: 01001 = Autauga County, Alabama

### Cấp 3: Road Type (Loại đường) - OSM Highway Types
```
├── motorway                   # Cao tốc liên bang
├── trunk/primary             # Quốc lộ, đường chính
├── secondary/tertiary        # Đường cấp 2, cấp 3
├── residential               # Đường dân cư
└── service                   # Đường dịch vụ
```

### Cấp 4: Individual Roads (Đường cụ thể)
- Tên đầy đủ (name from OSM)
- ID duy nhất (osm_id)
- Metadata: highway type, lanes, surface, độ dài, tọa độ

## Ví dụ Navigation Flow
```
1. User chọn: California
2. System hiện: Danh sách counties có data
3. User chọn: Los Angeles County (06037)
4. System hiện: 4 loại đường
5. User chọn: Primary Roads
6. System hiện: I-5, I-10, US-101...
7. User chọn: I-405
8. System hiện: Chi tiết I-405 trên bản đồ
```

## Lưu ý quan trọng
1. **Primary, Secondary, Local** là 3 LOẠI đường song song, KHÔNG PHẢI cấp bậc
2. Mỗi city có thể nằm trong 1 hoặc nhiều county
3. Cần mapping city → county(s) để hiển thị đúng

## Database Structure (Self-hosted PostgreSQL)

### Table: states (49 records)
```sql
state_code  VARCHAR(2) PRIMARY KEY  -- AL, CA...
state_name  VARCHAR(50) NOT NULL
total_roads INTEGER DEFAULT 0
created_at  TIMESTAMP WITH TIME ZONE
```

### Table: counties (323 records)
```sql
county_fips VARCHAR(5) PRIMARY KEY   -- 01001, 06037...
county_name VARCHAR(100)
state_code  VARCHAR(2) REFERENCES states(state_code)
total_roads INTEGER DEFAULT 0
created_at  TIMESTAMP WITH TIME ZONE
```

### Table: city_boundaries (OSM boundaries)
```sql
osm_id      BIGINT PRIMARY KEY
name        TEXT NOT NULL
state_code  VARCHAR(2)
admin_level INTEGER                 -- 8 for cities
geometry    GEOMETRY(Geometry, 4326)
tags        JSONB
created_at  TIMESTAMP DEFAULT NOW()
```

### Table: road_city_mapping (Accurate boundary-based mapping)
```sql
osm_id      BIGINT REFERENCES osm_roads_main(osm_id)
city_name   TEXT
state_code  VARCHAR(2)
mapping_type VARCHAR(20)  -- 'within' or 'nearest'
distance_km NUMERIC
PRIMARY KEY (osm_id)
```

### Table: osm_roads_main (27M+ records)
```sql
osm_id      BIGINT PRIMARY KEY      -- OSM unique ID
name        TEXT                    -- Road name (26.3% have names)
highway     VARCHAR(100)            -- OSM road type
ref         VARCHAR(150)            -- Road reference (I-5, US-101)
state_code  VARCHAR(2)
county_fips VARCHAR(10)
geometry    GEOMETRY(LINESTRING, 4326)
tags        JSONB                   -- Additional OSM metadata
lanes       INTEGER
maxspeed    VARCHAR(100)
surface     VARCHAR(200)
oneway      VARCHAR(50)
created_at  TIMESTAMP WITH TIME ZONE
```

### Indexes for Performance
```sql
-- Spatial indexes
CREATE INDEX idx_osm_roads_geom ON osm_roads_main USING GIST(geometry);
CREATE INDEX idx_city_boundaries_geom ON city_boundaries USING GIST(geometry);

-- Regular indexes
CREATE INDEX idx_osm_roads_name ON osm_roads_main(name);
CREATE INDEX idx_osm_roads_county ON osm_roads_main(county_fips);
CREATE INDEX idx_osm_roads_state ON osm_roads_main(state_code);
CREATE INDEX idx_osm_roads_highway ON osm_roads_main(highway);
CREATE INDEX idx_osm_roads_name_trgm ON osm_roads_main USING gin(name gin_trgm_ops);
```

### Views
```sql
-- city_roads: Easy access to roads by city (using accurate boundaries)
CREATE VIEW city_roads AS
SELECT rcm.city_name, rcm.state_code, r.*
FROM osm_roads_main r
JOIN road_city_mapping rcm ON r.osm_id = rcm.osm_id;

-- road_statistics: Fast stats using cache table
CREATE TABLE osm_stats_cache (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_segments BIGINT,
    segments_with_names BIGINT,
    unique_roads_with_names BIGINT,
    last_updated TIMESTAMP
);
```

## API Endpoints
```
GET /states                    # List all states
GET /states/{state}/counties   # Counties in state
GET /counties/{fips}/roads     # Roads in county
GET /cities/{city}/roads       # Roads within city boundaries
GET /roads/{osm_id}            # Road details
GET /api/analyze-location      # Business potential analysis
```