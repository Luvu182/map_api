# US Cities Road Database (Population > 100K)

## Overview
Comprehensive road database containing **5.15 million unique roads** from 346 US cities with population >100,000, imported from US Census TIGER/Line shapefiles into Supabase.

## Database Statistics
- **Total Roads**: 5,155,787 (after removing duplicates)
- **Roads with Names**: ~3.4 million (66.5%)
- **Roads without Names**: ~1.7 million (33.5%)
- **Counties Processed**: 323
- **Database Size**: ~2.1GB

### Road Categories
- **Local Streets**: 4,573,456 (88.7%)
- **Special Roads**: 534,952 (10.4%)
- **Secondary Roads**: 34,172 (0.7%)
- **Primary Roads**: 13,207 (0.3%)

## Tech Stack
- **Database**: Supabase (PostgreSQL)
- **Data Source**: US Census TIGER/Line 2024
- **Languages**: Python for data processing
- **Features**: Full-text search with pg_trgm

## Project Structure
```
Data_US_100k_pop/
├── README.md                    # This file
├── ARCHITECTURE.md             # System architecture
├── PROCESSING_GUIDE.md         # Data processing guide
├── TIGER_ROADS_DOWNLOAD.md     # Download URLs (323 files)
├── scripts/
│   ├── import_to_supabase.py   # Main import script
│   ├── fast_import.py          # Optimized import
│   ├── check_import_progress.py # Progress checker
│   └── supabase_schema.sql     # Database schema
├── raw_data/
│   └── shapefiles/TIGER_Roads/
│       └── extracted/          # 323 county shapefiles
└── processed_data/
    ├── hierarchy/              # JSON/CSV summaries
    └── city_roads/             # City-specific extracts
```

## Database Schema
```sql
-- Main tables
roads (5.15M records)
├── linearid (unique identifier)
├── fullname (road name, nullable)
├── mtfcc (road classification code)
├── road_category (Primary/Secondary/Local/Special)
├── rttyp (route type)
├── county_fips
└── state_code

states (51 records)
counties (323 records)
cities (15 major cities mapped)
```

## Quick Start

### 1. Setup Google Maps Crawler
```bash
# Backend
cd google_maps_crawler
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd google_maps_crawler/frontend
npm install
npm start
```

### 2. Access Points
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Environment Setup
Create `.env` files:

**Backend** (`google_maps_crawler/.env`):
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
```

**Frontend** (`google_maps_crawler/frontend/.env`):
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_key
```

## Key Features
- Full-text search with fuzzy matching
- Hierarchical views (State → County → City → Road)
- Road type classification (MTFCC codes)
- Optimized indexes for fast queries

## Import Process Completed
- Started with 5,263,747 roads in raw files
- Removed ~108,000 duplicates (roads crossing county boundaries)
- Final count: 5,155,787 unique roads
- Import time: ~45 minutes

## Notes
- 33.5% of roads have no official name (alleys, ramps, private roads)
- Special roads (85% unnamed) include parking lots, trails, driveways
- All primary/secondary highways have names
- Database uses Row Level Security (disabled for import)