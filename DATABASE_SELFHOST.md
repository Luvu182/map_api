# Self-Hosted PostgreSQL Database Guide

## Overview
Complete guide for self-hosting PostgreSQL with PostGIS for the US Roads database, migrated from Supabase to save costs.

## Current Database Statistics
- **Target Counties**: 323 (with 100k+ population cities)
- **OSM Roads Available**: 21 million (full dataset)
- **Filtered Roads**: ~3.7 million (in target counties)
- **Coverage**: 97% of roads in high-density areas
- **States**: 49 US states
- **Database Size**: ~14GB (can be optimized by removing duplicate tables)

## Architecture

### Docker Setup (Recommended)
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: roads-postgres
    environment:
      POSTGRES_DB: roads_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: roadsdb2024secure
    ports:
      - "5432:5432"
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=256MB
      -c work_mem=16MB
      -c max_connections=100
      -c random_page_cost=1.1
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Database Schema

#### Core Tables
1. **states** (49 records) - US states information
2. **counties** (323 records) - Target counties with 100k+ cities
3. **county_boundaries** (323 records) - Spatial boundaries for filtering
4. **osm_roads_filtered** - OSM roads within target counties
5. **businesses** - Crawled business data from Google Maps
6. **crawl_jobs** - Track crawl jobs
7. **crawl_status** - Track crawl status by road/keyword
8. **spatial_ref_sys** - PostGIS coordinate systems

#### Key Features
- PostGIS spatial filtering with county boundaries
- OSM data with rich metadata (JSONB format)
- Focus on high-density population areas
- Optimized spatial and JSONB indexes
- Efficient storage by filtering unnecessary areas

## Installation & Setup

### 1. Start PostgreSQL
```bash
cd /Users/luvu/Data_US_100k_pop
docker-compose up -d

# Verify it's running
docker ps
docker logs roads-postgres
```

### 2. Create County Boundaries
```bash
# Required for spatial filtering
python scripts/create_county_boundaries.py
```

### 3. Import OSM Data
```bash
# Import California (example)
python scripts/import_osm_filtered.py

# Import all states
python scripts/import_all_osm_states.py
```

### 4. Create Production Indexes
```bash
# Create optimized indexes for production
cat > scripts/create_production_indexes.sql << 'EOF'
-- Indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_roads_state_county ON roads(state_code, county_fips);
CREATE INDEX IF NOT EXISTS idx_roads_fullname_pattern ON roads USING gin(fullname gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_roads_mtfcc ON roads(mtfcc);
CREATE INDEX IF NOT EXISTS idx_roads_county_name ON roads(county_fips, fullname);

-- Indexes for crawl management
CREATE INDEX IF NOT EXISTS idx_crawl_status_road_keyword ON crawl_status(road_linearid, keyword);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status_date ON crawl_jobs(status, created_at DESC);

-- Analyze tables for query planner
ANALYZE roads;
ANALYZE crawl_status;
ANALYZE crawl_jobs;
EOF

docker exec roads-postgres psql -U postgres -d roads_db -f - < scripts/create_production_indexes.sql
```

### 5. Import Geometry (Optional - for road lengths)
```bash
# Only if you need road length calculations
# Takes 30-60 minutes
python scripts/import_geometry.py
```

## Road Type Guide (MTFCC)

### 🟢 High Business Density (Prioritize)
- **S1100**: Interstate/Limited-access highways (I-5, I-95)
- **S1200**: US/State highways (US-101, SR-1)  
- **S1400**: Local streets, city roads (Main St, Broadway)

### 🟡 Medium Business Density
- **S1640**: Service drives parallel to highways
- **S1780**: Parking lot roads (may have surrounding shops)

### 🔴 Low Business Density (Consider skipping)
- **S1730**: Alleys (residential, behind buildings)
- **S1740**: Private roads (logging, oil fields, ranches)
- **S1750**: Internal Census Bureau use roads

### ⛔ No Businesses (Skip)
- **S1500**: 4WD trails
- **S1630**: Highway on/off ramps
- **S1710**: Pedestrian walkways
- **S1720**: Stairways
- **S1820**: Bike paths
- **S1830**: Bridle paths

## Performance Optimization

### 1. Database Maintenance
```bash
# Run during off-hours (requires ~30 min downtime)
docker exec roads-postgres psql -U postgres -d roads_db << 'EOF'
-- Update statistics
ANALYZE;

-- Clean up dead tuples (run monthly)
VACUUM ANALYZE;

-- Full optimization (run quarterly, requires more downtime)
-- VACUUM FULL ANALYZE;
EOF
```

### 2. Query Performance Tips
```sql
-- Check slow queries
SELECT query, calls, mean_exec_time, max_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

### 3. Connection Pooling
Already configured in `scripts/database_config.py`:
- Pool size: 5-20 connections
- Overflow: 10 connections
- Timeout: 30 seconds

## Backup & Recovery

### Automated Backup Script
```bash
cat > scripts/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/Users/luvu/Data_US_100k_pop/backups"
mkdir -p $BACKUP_DIR

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec roads-postgres pg_dump -U postgres -d roads_db | gzip > $BACKUP_DIR/roads_backup_$TIMESTAMP.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "roads_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: roads_backup_$TIMESTAMP.sql.gz"
EOF

chmod +x scripts/backup_database.sh

# Add to crontab for daily 2 AM backups
# crontab -e
# 0 2 * * * /Users/luvu/Data_US_100k_pop/scripts/backup_database.sh
```

### Manual Backup/Restore
```bash
# Backup
docker exec roads-postgres pg_dump -U postgres -d roads_db | gzip > backup_manual.sql.gz

# Restore
gunzip -c backup_manual.sql.gz | docker exec -i roads-postgres psql -U postgres -d roads_db
```

## API Configuration

### Backend (FastAPI)
```python
# config.py - Already configured
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "roads_db"
DB_USER = "postgres"
DB_PASSWORD = "roadsdb2024secure"
```

### Frontend
- Connects via backend API at http://localhost:8000
- No direct database access needed
- CORS configured for localhost:3000

## Monitoring

### Database Health Check
```bash
# Create monitoring script
cat > scripts/check_db_health.sh << 'EOF'
#!/bin/bash
echo "=== Database Health Check ==="
echo "1. Database Size:"
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT pg_database_size('roads_db')/1024/1024 || ' MB' as size;"

echo -e "\n2. Table Sizes:"
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(tablename::regclass) DESC LIMIT 5;"

echo -e "\n3. Active Connections:"
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT count(*) as connections FROM pg_stat_activity;"

echo -e "\n4. Road Statistics:"
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT COUNT(*) as total_roads, COUNT(CASE WHEN fullname IS NOT NULL THEN 1 END) as named_roads FROM roads;"
EOF

chmod +x scripts/check_db_health.sh
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
```bash
# Check if container is running
docker ps | grep roads-postgres

# Check logs
docker logs roads-postgres --tail 50

# Restart if needed
docker-compose restart
```

2. **Out of Memory**
```bash
# Increase Docker memory
docker update roads-postgres --memory="4g"

# Or update docker-compose.yml and recreate
```

3. **Slow Queries**
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second
SELECT pg_reload_conf();

-- Check slow query log
docker exec roads-postgres tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

4. **Disk Space**
```bash
# Check disk usage
docker exec roads-postgres df -h /var/lib/postgresql/data

# Clean up if needed
docker exec roads-postgres psql -U postgres -d roads_db -c "VACUUM FULL;"
```

## Production Checklist

- [x] PostgreSQL with PostGIS installed
- [x] 5.2M roads imported successfully  
- [x] Indexes created for performance
- [x] Connection pooling configured
- [x] Backup strategy implemented
- [ ] Import MTFCC descriptions (run script above)
- [ ] Create production indexes (run script above)
- [ ] Set up automated backups (crontab)
- [ ] Import geometry data (when needed for lengths)
- [ ] Run VACUUM FULL (during maintenance window)

## Cost Comparison
- **Supabase**: $25+/month for 1.2GB
- **Self-hosted**: $0 (existing hardware) + maintenance time
- **Savings**: $300+/year

## Next Steps
1. Run the production setup scripts above
2. Configure automated backups
3. Set up monitoring alerts
4. Import geometry when map features needed
5. Document any custom queries for your team