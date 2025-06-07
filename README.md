# US Roads & Business Data Project

## Overview
Complete system for managing US road data from OpenStreetMap (OSM) and crawling business data from Google Maps. Focused on **323 counties with cities having 100k+ population**. Self-hosted PostgreSQL database with PostGIS support, optimized for production use.

## Quick Stats
- **323** target counties (with cities having 100k+ population)
- **21 million** OSM road records available
- **~3.7 million** roads after filtering to target counties
- **97.3%** of California roads fall within target counties
- **Database**: Self-hosted PostgreSQL 15 + PostGIS 3.3
- **Performance**: Spatial filtering with county boundaries

## Tech Stack
- **Database**: PostgreSQL 15 + PostGIS 3.3 (Docker)
- **Backend**: FastAPI + Python
- **Frontend**: React + Google Maps API
- **Data Source**: OpenStreetMap (OSM) PBF files

## Project Structure
```
Data_US_100k_pop/
├── README.md                    # This file
├── OSM_IMPORT_FINAL_STATUS.md  # Current import status
├── DATABASE_SELFHOST.md        # Complete database guide
├── ARCHITECTURE.md             # System architecture
├── docker-compose.yml          # PostgreSQL setup
├── scripts/
│   ├── import_all_osm_direct.py   # Main OSM import script
│   ├── reimport_minnesota_only.py # Minnesota re-import script
│   ├── create_county_boundaries.py # Create spatial boundaries
│   ├── create_production_indexes.sql # Performance indexes
│   ├── backup_postgres.sh         # Automated backups
│   └── database_config.py         # DB connection config
├── google_maps_crawler/
│   ├── app/                    # FastAPI backend (OSM-ready)
│   └── frontend/               # React UI (OSM-ready)
└── raw_data/
    └── data_osm/               # OSM PBF files by state
```

## Quick Start

### 1. Start Database
```bash
# Start PostgreSQL with PostGIS
docker-compose up -d

# Verify connection
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT version();"
```

### 2. Import OSM Data
```bash
# Create county boundaries (required for spatial filtering)
python scripts/create_county_boundaries.py

# Import California OSM data (filtered to target counties)
python scripts/import_osm_filtered.py

# Import all states (batch process)
python scripts/import_all_osm_states.py
```

### 3. Start Application
```bash
# Backend API
cd google_maps_crawler
pip install -r requirements.txt
python -m app.main

# Frontend UI (new terminal)
cd google_maps_crawler/frontend
npm install
npm start
```

### 4. Access Points
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## Database Schema

### Core Tables
- **osm_roads_filtered** - OSM roads within target counties
- **counties** (323 records) - Target counties with 100k+ population cities
- **county_boundaries** (323 records) - Spatial boundaries for filtering
- **states** (49 records) - US states reference
- **businesses** - Crawled Google Maps data (to be populated)
- **crawl_status** - Track crawling progress
- **mtfcc_descriptions** - Road type classifications

### OSM Highway Types
- **motorway**: Interstate highways (high business density)
- **trunk/primary**: US/State highways (high business density)
- **secondary/tertiary**: Major streets (medium-high density)
- **residential**: Local streets (medium density)
- **service**: Service roads, parking (low density)

## Key Features

### 1. Targeted Data Collection
- Focus on 323 counties with 100k+ population cities
- Spatial filtering using county boundaries
- ~97% coverage for high-density areas
- Significant storage savings vs full dataset

### 2. OSM Data Advantages
- More detailed road attributes (lanes, speed limits, surface)
- Better name coverage and accuracy
- Regular updates from community
- Rich metadata in JSONB format

### 3. Performance Optimized
- Spatial indexes for fast geographic queries
- JSONB indexes for metadata searches
- County-based partitioning
- Efficient import process

### 4. Production Ready
- Automated daily backups
- Health monitoring scripts
- Docker deployment
- Scalable architecture

## Google Maps Integration

### Crawling Strategy
```javascript
// Smart query building
"restaurant on Main Street, Jefferson County, AL"  // For streets
"gas station near Highway 101, CA"                 // For highways
```

### Prioritize These Roads
1. **motorway** - Interstates (gas stations, restaurants)
2. **trunk/primary** - Major highways (diverse businesses)
3. **secondary/tertiary** - Main streets (local businesses)

### Skip These
1. **footway/cycleway** - Pedestrian only
2. **service** with access=private - Private roads
3. **track** - Unpaved/agricultural roads

## Maintenance

### Daily Tasks (Automated)
```bash
# Backup runs at 2 AM via cron
/Users/luvu/Data_US_100k_pop/scripts/backup_database.sh
```

### Monthly Tasks
```bash
# Update statistics and clean up
docker exec roads-postgres psql -U postgres -d roads_db -c "VACUUM ANALYZE;"
```

### Health Check
```bash
./scripts/check_db_health.sh
# Shows: database size, table sizes, connections, road statistics
```

## Storage Efficiency
| Data Source | Total Size | Filtered Size | Coverage |
|-------------|------------|---------------|----------|
| Full OSM | 21M roads | 3.7M roads | 97% of target areas |
| All US | 50 states | 323 counties | 100k+ population |
| California | 3.8M roads | 3.7M roads | 29 counties |
| **Savings** | **82% less** | Targeted data | Better performance |

## Troubleshooting

### Common Issues
1. **Connection refused**: Check Docker is running
2. **Slow spatial queries**: Check spatial indexes exist
3. **Import fails**: Ensure county_boundaries table exists
4. **Missing counties**: Verify all 323 counties loaded

### Support Resources
- Database guide: `DATABASE_SELFHOST.md`
- Architecture: `ARCHITECTURE.md`
- Processing guide: `PROCESSING_GUIDE.md`

## Future Enhancements
- [x] Migrate from TIGER to OpenStreetMap data (COMPLETED)
- [x] Implement spatial filtering for target counties (COMPLETED)
- [ ] Add real-time crawl progress dashboard
- [ ] Implement distributed crawling
- [ ] Add business analytics dashboard
- [ ] Integrate traffic data from OSM

## License
MIT License - See LICENSE file for details