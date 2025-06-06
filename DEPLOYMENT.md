# Deployment Guide

## System Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   API Server │────▶│  PostgreSQL │
│  (React/GM) │     │   (Node.js)  │     │  + PostGIS  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Redis Cache │
                    └──────────────┘
```

## Database Setup

### PostgreSQL + PostGIS
```bash
# Install PostGIS extension
CREATE EXTENSION postgis;

# Create tables (see ARCHITECTURE.md)
psql -U postgres -d roads_db -f schema.sql

# Import processed data
ogr2ogr -f PostgreSQL PG:"dbname=roads_db user=postgres" roads_hierarchy.geojson -nln roads
```

### Create Indexes
```sql
-- Spatial indexes
CREATE INDEX idx_roads_geom ON roads USING GIST(geometry);
CREATE INDEX idx_counties_geom ON counties USING GIST(geometry);

-- Regular indexes
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_category ON roads(category);
CREATE INDEX idx_roads_name ON roads(fullname);
```

## API Server (Node.js/Express)

### Basic Setup
```javascript
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  host: process.env.DB_HOST,
  database: 'roads_db',
  user: process.env.DB_USER,
  password: process.env.DB_PASS
});

// Endpoints
app.get('/api/states', async (req, res) => {
  const result = await pool.query('SELECT * FROM states ORDER BY name');
  res.json(result.rows);
});

app.get('/api/counties/:stateFips', async (req, res) => {
  const result = await pool.query(
    'SELECT * FROM counties WHERE state_fips = $1 ORDER BY name',
    [req.params.stateFips]
  );
  res.json(result.rows);
});
```
### Road Query Endpoints
```javascript
app.get('/api/roads/:countyFips/:category', async (req, res) => {
  const { countyFips, category } = req.params;
  const { limit = 100, offset = 0 } = req.query;
  
  const result = await pool.query(`
    SELECT 
      linearid, fullname, rttyp, length_m,
      ST_AsGeoJSON(ST_Simplify(geometry, 0.0001)) as geojson
    FROM roads 
    WHERE county_fips = $1 AND category = $2
    ORDER BY length_m DESC
    LIMIT $3 OFFSET $4
  `, [countyFips, category, limit, offset]);
  
  res.json(result.rows);
});
```

## Frontend Integration

### Google Maps Setup
```javascript
// Initialize map
const map = new google.maps.Map(document.getElementById('map'), {
  zoom: 10,
  center: { lat: 34.0522, lng: -118.2437 } // LA
});

// Load roads data
async function loadRoads(countyFips, category) {
  const response = await fetch(`/api/roads/${countyFips}/${category}`);
  const roads = await response.json();
  
  roads.forEach(road => {
    const path = JSON.parse(road.geojson).coordinates;
    new google.maps.Polyline({
      path: path.map(coord => ({ lat: coord[1], lng: coord[0] })),
      map: map,
      strokeColor: getCategoryColor(category),
      strokeWeight: getCategoryWeight(category)
    });
  });
}
```

## Performance Optimization

### Redis Caching
```javascript
const redis = require('redis');
const client = redis.createClient();

// Cache middleware
async function cacheMiddleware(req, res, next) {
  const key = req.originalUrl;
  const cached = await client.get(key);
  
  if (cached) {
    return res.json(JSON.parse(cached));
  }
  
  res.sendResponse = res.json;
  res.json = (body) => {
    client.setex(key, 3600, JSON.stringify(body));
    res.sendResponse(body);
  };
  next();
}
```

## Deployment Steps

1. **Database**
   ```bash
   # Create database
   createdb roads_db
   
   # Run migrations
   npm run migrate
   
   # Import data
   npm run import-data
   ```

2. **API Server**
   ```bash
   # Install dependencies
   npm install
   
   # Build
   npm run build
   
   # Start with PM2
   pm2 start server.js -i max
   ```

3. **Frontend**
   ```bash
   # Build React app
   npm run build
   
   # Deploy to CDN/S3
   aws s3 sync build/ s3://your-bucket
   ```

## Monitoring
- Use PM2 for process management
- Set up CloudWatch or Datadog for metrics
- Monitor database performance with pg_stat_statements
- Set up alerts for high latency or errors