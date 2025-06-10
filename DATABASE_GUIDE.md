# Complete Database Guide

## Overview
This guide consolidates all database-related documentation including setup, migration, statistics, and maintenance.

## Table of Contents
1. [Database Setup & Configuration](#setup)
2. [Migration from Supabase](#migration)
3. [Current Database State](#current-state)
4. [Maintenance & Backup](#maintenance)
5. [Performance Optimization](#optimization)

## Setup

### Self-hosting PostgreSQL 15 with PostGIS

#### Using Docker Compose
```yaml
version: '3.8'
services:
  postgres:
    container_name: roads-postgres
    image: postgis/postgis:15-3.3-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: roads_db
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5436:5432"
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./scripts:/scripts
      - ./postgres-backups:/backups
    shm_size: 2g
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=1GB"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "effective_cache_size=3GB"
      - "-c"
      - "maintenance_work_mem=512MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
```

### Connection String
```
postgresql://postgres:password@localhost:5436/roads_db
```

## Migration

### From Supabase to Self-hosted PostgreSQL

1. **Export from Supabase**:
```bash
pg_dump -h db.xxxxxx.supabase.co -U postgres -d postgres -f backup.sql
```

2. **Import to self-hosted**:
```bash
psql -U postgres -d roads_db -f backup.sql
```

## Current State

### Database Statistics (as of 2025-06-08)

#### OSM Roads Data
- **Total roads**: 10,518,570
- **Coverage**: All US states except ME, HI, DE
- **With city mapping**: 1,475,606 roads (14%)
- **Target roads**: 962,855 (roads in 346 cities)

#### OSM Business/POI Data
- **Total POIs**: 2,238,606
- **States with POIs**: 31 states + DC
- **Mapped to roads**: 1,987,522 (88.8%)
- **Business types**: 219 unique types
- **Business subtypes**: 2,408 unique subtypes

#### Data by State (Top 10)
| State | Roads | POIs | POIs Mapped % |
|-------|-------|------|---------------|
| CA | 733,640 | 281,968 | 89.1% |
| TX | 991,936 | 200,453 | 87.7% |
| FL | 558,036 | 179,455 | 90.8% |
| NY | 350,124 | 162,238 | 93.4% |
| IL | 412,780 | 102,607 | 91.8% |
| PA | 455,260 | 101,313 | 85.9% |
| OH | 411,676 | 82,863 | 86.8% |
| MI | 396,084 | 77,507 | 0.0% (needs mapping) |
| NC | 415,796 | 75,461 | 87.9% |
| GA | 377,396 | 71,905 | 90.2% |

#### Database Size
- Total database: 12.5 GB
- Roads table: 8.2 GB
- POIs table: 1.8 GB
- Indexes: 2.5 GB

## Maintenance

### Backup Strategy

#### Automated Daily Backups
```bash
#!/bin/bash
# scripts/backup_postgres.sh
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create compressed backup
docker exec roads-postgres pg_dump -U postgres -d roads_db | gzip > "$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

# Keep only last 7 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
```

#### Manual Backup Commands
```bash
# Full backup with custom format
docker exec roads-postgres pg_dump -U postgres -d roads_db -Fc -f /backups/backup.custom

# Schema only
docker exec roads-postgres pg_dump -U postgres -d roads_db --schema-only > schema.sql

# Data only specific tables
docker exec roads-postgres pg_dump -U postgres -d roads_db -t osm_roads_main --data-only > roads_data.sql
```

### Health Monitoring
```bash
# Check database health
./scripts/check_db_health.sh

# Monitor connections
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check table sizes
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC;"
```

## Optimization

### Key Indexes
```sql
-- Spatial indexes (most important)
CREATE INDEX idx_roads_geometry ON osm_roads_main USING gist(geometry);
CREATE INDEX idx_businesses_geometry ON osm_businesses USING gist(geometry);

-- Lookup indexes
CREATE INDEX idx_roads_osm_id ON osm_roads_main(osm_id);
CREATE INDEX idx_roads_state_city ON osm_roads_main(state_code, city);
CREATE INDEX idx_businesses_state ON osm_businesses(state_code);
CREATE INDEX idx_businesses_road ON osm_businesses(nearest_road_id);

-- Performance indexes
CREATE INDEX idx_roads_importance ON osm_roads_main(is_in_target_city, road_importance);
CREATE INDEX idx_businesses_type ON osm_businesses(business_type, business_subtype);
```

### Query Optimization Tips
1. Always use spatial indexes for geometry operations
2. Filter by state_code first when possible
3. Use LIMIT for large result sets
4. Consider materialized views for complex aggregations
5. Run VACUUM ANALYZE regularly

### Maintenance Tasks
```sql
-- Weekly maintenance
VACUUM ANALYZE osm_roads_main;
VACUUM ANALYZE osm_businesses;

-- Monthly reindex
REINDEX TABLE osm_roads_main;
REINDEX TABLE osm_businesses;

-- Check for bloat
SELECT schemaname, tablename, 
       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
       (pgstattuple(schemaname||'.'||tablename)).dead_tuple_percent AS dead_percent
FROM pg_tables 
WHERE schemaname = 'public';
```

## Troubleshooting

### Common Issues

1. **Slow spatial queries**
   - Check if spatial indexes exist
   - Use EXPLAIN ANALYZE to verify index usage
   - Consider increasing work_mem for complex queries

2. **High memory usage**
   - Check shared_buffers setting
   - Monitor active connections
   - Review long-running queries

3. **Disk space issues**
   - Run VACUUM FULL on large tables
   - Check for unnecessary indexes
   - Archive old backup files

### Performance Monitoring Queries
```sql
-- Long running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Table statistics
SELECT schemaname, tablename, n_live_tup, n_dead_tup, 
       last_vacuum, last_autovacuum
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```