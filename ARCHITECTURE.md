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

### Cấp 3: Road Type (Loại đường) - TẤT CẢ NGANG CẤP
```
├── Primary Roads (S1100)      # Cao tốc, quốc lộ chính
├── Secondary Roads (S1200)    # Tỉnh lộ, đường phụ
├── Local Streets (S1400)      # Đường địa phương
└── Special Roads (S1500+)     # Đường đặc biệt
```

### Cấp 4: Individual Roads (Đường cụ thể)
- Tên đầy đủ (FULLNAME)
- ID duy nhất (LINEARID)
- Metadata: RTTYP, độ dài, tọa độ

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

## Database Structure (Implemented in Supabase)

### Table: states (51 records)
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

### Table: cities (15 major cities)
```sql
city_id    SERIAL PRIMARY KEY
city_name  VARCHAR(100) NOT NULL
state_code VARCHAR(2) REFERENCES states(state_code)
population INTEGER
total_roads INTEGER DEFAULT 0
created_at  TIMESTAMP WITH TIME ZONE
```

### Table: city_counties (21 mappings)
```sql
city_id     INTEGER REFERENCES cities(city_id)
county_fips VARCHAR(5) REFERENCES counties(county_fips)
PRIMARY KEY (city_id, county_fips)
```

### Table: roads (5,155,787 records)
```sql
id          BIGSERIAL PRIMARY KEY
linearid    VARCHAR(30) UNIQUE NOT NULL
fullname    TEXT                    -- 33.5% are NULL
rttyp       VARCHAR(1)              -- Route type
mtfcc       VARCHAR(5)              -- Feature class
road_category VARCHAR(20)           -- Derived category
county_fips VARCHAR(5) REFERENCES counties(county_fips)
state_code  VARCHAR(2) REFERENCES states(state_code)
created_at  TIMESTAMP WITH TIME ZONE
```

### Indexes for Performance
```sql
CREATE INDEX idx_roads_fullname ON roads(fullname);
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_state ON roads(state_code);
CREATE INDEX idx_roads_category ON roads(road_category);
CREATE INDEX idx_roads_mtfcc ON roads(mtfcc);
CREATE INDEX idx_roads_fullname_trgm ON roads USING gin(fullname gin_trgm_ops);
```

### Views
```sql
-- city_roads: Easy access to roads by city
CREATE VIEW city_roads AS
SELECT c.city_name, c.state_code, r.*
FROM roads r
JOIN city_counties cc ON r.county_fips = cc.county_fips
JOIN cities c ON cc.city_id = c.city_id;

-- road_statistics: Materialized view for fast stats
CREATE MATERIALIZED VIEW road_statistics AS
SELECT state_code, COUNT(*) as total_roads, 
       COUNT(CASE WHEN mtfcc = 'S1100' THEN 1 END) as primary_roads,
       COUNT(CASE WHEN mtfcc = 'S1200' THEN 1 END) as secondary_roads,
       COUNT(CASE WHEN mtfcc = 'S1400' THEN 1 END) as local_streets,
       COUNT(CASE WHEN mtfcc NOT IN ('S1100','S1200','S1400') THEN 1 END) as special_roads
FROM roads GROUP BY state_code;
```

## API Endpoints đề xuất
```
GET /states                    # List all states
GET /states/{state}/counties   # Counties in state
GET /counties/{fips}/roads     # Road types in county
GET /counties/{fips}/roads/{type}  # Roads by type
GET /roads/{linearid}          # Road details
```