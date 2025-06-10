# US Roads & Business Data Explorer

A comprehensive system for exploring US road networks and business data, focusing on 346 target cities with 100k+ population. Built with OpenStreetMap (OSM) data and Google Maps API integration.

## Quick Stats
- **346** target cities (>100k population)
- **340** cities mapped (98.3% coverage)
- **10.57M** road segments in target cities
- **2.77M** unique roads (grouped by name)
- **12** roads crawled via Google Maps
- **420** businesses found
- **335** OSM POIs imported

## Current Architecture
- **Database**: PostgreSQL 15 + PostGIS 3.3 (18 GB)
- **Tables**: osm_roads_main (10.57M), road_city_mapping (10.57M)
- **Frontend**: React with city-based filtering
- **Backend**: FastAPI with grouped road names
- **Performance**: <50ms city-based queries

## Key Features

### 1. City-Based Architecture
- Roads mapped directly to 346 target cities
- No county-level complexity
- 98.3% city coverage (340/346)
- Missing: 6 Texas cities (no OSM data)

### 2. Smart Road Grouping
- Groups road segments by name
- "Azalea Road" = 1 entry (not 8 segments)
- Prevents duplicate crawling
- Shows total length and segment count

### 3. Google Maps Crawler
- **NEW**: Text Search API with 60 results per search
- Pagination support (3 API calls = 60 results)
- Session-based tracking with real-time status
- Crawl history management
- Multi-language support (EN/VI)
- API usage tracking & cost estimation

### 4. Optimized Database
- Reduced from 27.16M to 10.57M segments
- Only roads in target cities kept
- Indexed for fast city queries
- 18 GB total (was 27 GB)

## Project Structure
```
Data_US_100k_pop/
├── README.md                    # This file
├── docker-compose.yml          # PostgreSQL + PostGIS
├── scripts/
│   ├── create_crawl_status_table.sql  # Google Maps tracking
│   ├── backup_database_full.sh        # Comprehensive backup
│   └── remove_non_target_roads.sql    # Cleanup script
├── google_maps_crawler/
│   ├── app/
│   │   ├── main.py             # FastAPI server
│   │   ├── api/
│   │   │   └── roads_api.py    # City-based endpoints
│   │   └── database/
│   │       └── postgres_client.py
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── CrawlControl.js   # Main UI
│       │   │   ├── CitySelector.js  # 346 cities dropdown
│       │   │   └── Dashboard.js     # Statistics
│       │   └── api/
│       │       └── crawler.js       # API client
└── postgres-data/              # Database files (18 GB)
```

## Quick Start

### 1. Start Database
```bash
docker-compose up -d
```

### 2. Create Required Tables
```bash
# Create crawl tracking tables
docker exec -i roads-postgres psql -U postgres -d roads_db < scripts/create_crawl_status_table.sql
```

### 3. Start Application
```bash
# Backend API
cd google_maps_crawler
pip install -r requirements.txt
python -m app.main

# Frontend (new terminal)
cd google_maps_crawler/frontend
npm install
npm start
```

### 4. Access
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (user: postgres, db: roads_db)

## API Endpoints

### City-Based Endpoints
- `GET /api/roads/target-cities` - List 346 cities with road counts
- `GET /api/roads/by-city` - Get roads for specific city (grouped by name)
- `GET /api/roads/city-stats` - City statistics
- `GET /api/roads/search-with-coords` - Search with map coordinates

### Crawl Endpoints
- `POST /crawl/road/{osm_id}` - Crawl single road for businesses
- `GET /api/crawl-sessions` - List all crawl sessions
- `GET /api/crawl-sessions/{id}` - Get session details
- `POST /api/crawl-sessions/{id}/export` - Export results (CSV/JSON)

### Statistics & Monitoring
- `GET /stats` - Overall statistics
- `GET /api/usage` - API usage tracking
- `GET /roads/search` - Search roads by name

## Database Schema

### Core Tables
```sql
-- Main road data (10.57M records)
osm_roads_main (
    id BIGINT PRIMARY KEY,
    osm_id BIGINT,
    name TEXT,
    highway VARCHAR(100),
    geometry GEOMETRY(LineString, 4326)
)

-- Road-to-city mapping (10.57M records)
road_city_mapping (
    road_id BIGINT,
    city_name TEXT,
    state_code VARCHAR(2),
    PRIMARY KEY (road_id, city_name, state_code)
)

-- Target cities (346 records)
target_cities_346 (
    city_name TEXT,
    state_code VARCHAR(2),
    PRIMARY KEY (city_name, state_code)
)

-- Crawl sessions (20 records)
crawl_sessions (
    id VARCHAR(255) PRIMARY KEY,
    road_osm_id BIGINT,
    road_name TEXT,
    city_name TEXT,
    state_code VARCHAR(2),
    keyword VARCHAR(255),
    status VARCHAR(50),
    businesses_found INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
)

-- Businesses found (420 records)
businesses (
    place_id VARCHAR(255) PRIMARY KEY,
    name TEXT,
    formatted_address TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    types TEXT[],
    rating DECIMAL,
    user_ratings_total INTEGER,
    phone_number VARCHAR(50),
    website TEXT,
    road_osm_id BIGINT,
    session_id VARCHAR(255)
)
```

## Usage Flow

1. **Select State** → Shows cities in that state
2. **Select City** → Shows roads in that city (grouped)
3. **Enter Business Type** → e.g., "restaurant"
4. **Click Search** → Shows roads with business potential
5. **Click Crawl** → Searches Google Maps for businesses

## Road Statistics

### By Type (in database)
- Service roads: 44.8% (mostly unnamed)
- Footways: 22.2% (pedestrian only)
- Residential: 16.8% (best for businesses)
- Secondary: 2.8%
- Tertiary: 2.4%

### Name Coverage
- Total segments: 10.57M
- With names: 26.3%
- Unique names: ~4,000 per city average

## Performance

### Query Times
- City list: <10ms
- Roads by city: <50ms
- Grouped by name: <100ms
- Spatial queries: Indexed

### Database Size
- Total: 18 GB
- osm_roads_main: 15 GB
- road_city_mapping: 2.4 GB
- Indexes: ~600 MB

## Backup & Maintenance

### Daily Backup
```bash
./scripts/backup_database_full.sh
# Creates:
# - schema_TIMESTAMP.sql
# - backup_TIMESTAMP.sql.gz
# - backup_TIMESTAMP.custom
```

### Restore
```bash
# From compressed SQL
gunzip -c backup_TIMESTAMP.sql.gz | docker exec -i roads-postgres psql -U postgres -d roads_db

# From custom format (faster)
docker exec -i roads-postgres pg_restore -U postgres -d roads_db backup_TIMESTAMP.custom
```

## Missing Cities (6)
- Abilene, TX
- Amarillo, TX  
- Beaumont, TX
- Killeen, TX
- Waco, TX
- Stamford, CT (boundary created but no roads)

These cities have no road data in OpenStreetMap Texas files.

## Recent Updates (June 2025)

### Google Maps Integration
- ✅ Upgraded to Text Search API (60 results per search)
- ✅ Added pagination support (maxResultCount)
- ✅ Session-based crawl tracking
- ✅ Real-time crawl status persistence
- ✅ API usage tracking & cost estimation

### UI Improvements
- ✅ Crawl History tab with session management
- ✅ Export to CSV/JSON functionality
- ✅ Map view with real search integration
- ✅ Sort by POI count (primary) then potential
- ✅ Improved dashboard with API usage metrics

### Performance
- ✅ Materialized views for instant stats
- ✅ <50ms query response time
- ✅ Optimized indexes for city-based queries

## Google Maps API Pricing
- Text Search (New): $32.00 per 1,000 requests
- Each crawl with 60 results = 3 API requests
- Current usage: 60 requests ($1.92)
- No monthly free tier - pay as you go

## Future Enhancements
- [ ] Bulk crawl by city
- [ ] Implement crawl queue management
- [ ] Add business analytics dashboard
- [ ] Business data deduplication
- [ ] Auto-refresh materialized views

## License
MIT License - See LICENSE file for details