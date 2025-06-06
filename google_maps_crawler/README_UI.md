# Google Maps Crawler - UI Setup

## Features
- **Dashboard**: Real-time statistics and progress monitoring
- **Crawl Control**: Start and manage crawling jobs
- **Map View**: Visualize businesses on Google Maps
- **Business List**: Browse and export crawled data

## Installation

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Create `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### 3. Start Development Servers

Terminal 1 - Backend API:
```bash
# From project root
uvicorn app.main:app --reload
```

Terminal 2 - Frontend:
```bash
cd frontend
npm start
```

Access UI at: http://localhost:3000

## UI Components

### Dashboard
- Total roads in database
- Crawling progress
- Business statistics
- Cost tracking

### Crawl Control
- Select state to crawl
- Set number of roads
- View cost estimation
- Monitor active jobs

### Map View
- Interactive Google Maps
- Business markers
- Road visualization
- Search functionality

### Business List
- Filter by type
- Sort by rating/distance
- Export to CSV/JSON
- Detailed business info

## Production Build
```bash
cd frontend
npm run build
# Deploy build folder to your hosting service
```

## Screenshots

### Dashboard View
Shows real-time statistics with charts for:
- Crawl coverage (processed vs unprocessed roads)
- Business types distribution
- Progress tracking

### Map Integration
- Businesses displayed as markers
- Click for details
- Filter by business type
- Search roads by name

### Data Export
- CSV format for Excel
- JSON for developers
- Filtered exports