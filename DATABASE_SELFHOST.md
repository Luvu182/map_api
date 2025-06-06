# Self-Hosting Database Guide

## Overview
Hướng dẫn tự host PostgreSQL database thay vì dùng Supabase để tránh giới hạn quota.

## Option 1: PostgreSQL với Docker

### 1. Install Docker
```bash
# macOS
brew install docker

# Start Docker Desktop
open -a Docker
```

### 2. Run PostgreSQL Container
```bash
# Create data directory
mkdir -p ~/postgres-data

# Run PostgreSQL
docker run -d \
  --name roads-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=roads_db \
  -p 5432:5432 \
  -v ~/postgres-data:/var/lib/postgresql/data \
  postgres:15
```

### 3. Create Database Schema
```bash
# Connect to database
docker exec -it roads-postgres psql -U postgres -d roads_db

# Or use any PostgreSQL client (TablePlus, pgAdmin, etc.)
```

### 4. Import Schema
Run all SQL files in order:
1. `/scripts/supabase_schema.sql` - Main tables
2. `/google_maps_crawler/app/database/schemas.sql` - Business tables
3. `/google_maps_crawler/app/database/schemas_crawl_status.sql` - Crawl tracking

## Option 2: PostgreSQL Native Installation

### 1. Install PostgreSQL
```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb roads_db
```

### 2. Configure Access
Edit `postgresql.conf`:
```
listen_addresses = 'localhost'
port = 5432
```

### 3. Create User
```sql
CREATE USER crawler_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE roads_db TO crawler_user;
```

## Option 3: Cloud PostgreSQL Alternatives

### 1. Neon (Recommended)
```bash
# Sign up at neon.tech
# Create project
# Get connection string:
postgresql://user:password@host/database?sslmode=require
```

### 2. Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway init
railway add postgresql

# Get connection URL
railway connect postgresql
```

### 3. Render
- Free tier: 90 days
- Connection pooling included
- Automatic backups

## Update Application Configuration

### 1. Backend Connection
Update `google_maps_crawler/app/config.py`:
```python
# Instead of Supabase
DATABASE_URL = "postgresql://user:password@localhost:5432/roads_db"

# Or use environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 2. Direct PostgreSQL Client
Create `google_maps_crawler/app/database/postgres_client.py`:
```python
import psycopg2
from psycopg2.extras import RealDictCursor
import os

class PostgresClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            os.getenv("DATABASE_URL"),
            cursor_factory=RealDictCursor
        )
    
    def get_roads(self, state_code=None, county_fips=None, limit=1000):
        cursor = self.conn.cursor()
        query = "SELECT * FROM roads WHERE 1=1"
        params = []
        
        if state_code:
            query += " AND state_code = %s"
            params.append(state_code)
        
        if county_fips:
            query += " AND county_fips = %s"
            params.append(county_fips)
        
        query += " LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
```

### 3. Import Existing Data

If you have export from Supabase:
```bash
# Export from Supabase
pg_dump postgres://[SUPABASE_URL] > roads_backup.sql

# Import to local
psql -d roads_db -f roads_backup.sql
```

## API Layer Options

### 1. PostgREST (Like Supabase)
```bash
# Install PostgREST
brew install postgrest

# Configure
cat > postgrest.conf <<EOF
db-uri = "postgres://user:password@localhost:5432/roads_db"
db-schema = "public"
db-anon-role = "web_anon"
server-host = "127.0.0.1"
server-port = 3001
EOF

# Run
postgrest postgrest.conf
```

### 2. Hasura GraphQL
```bash
# Run with Docker
docker run -d \
  --name hasura \
  -p 8080:8080 \
  -e HASURA_GRAPHQL_DATABASE_URL=postgres://user:pass@host:5432/roads_db \
  -e HASURA_GRAPHQL_ENABLE_CONSOLE=true \
  hasura/graphql-engine:latest
```

### 3. Keep FastAPI
Continue using existing FastAPI backend with direct PostgreSQL connection.

## Backup Strategy

### 1. Automated Backups
```bash
# Create backup script
cat > backup_db.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump roads_db > backups/roads_backup_$DATE.sql
# Keep only last 7 days
find backups -name "*.sql" -mtime +7 -delete
EOF

# Schedule with cron
crontab -e
# Add: 0 2 * * * /path/to/backup_db.sh
```

### 2. Point-in-Time Recovery
Enable in `postgresql.conf`:
```
wal_level = replica
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

## Performance Optimization

### 1. Connection Pooling
Use `pgbouncer`:
```bash
brew install pgbouncer

# Configure pgbouncer.ini
[databases]
roads_db = host=localhost port=5432 dbname=roads_db

[pgbouncer]
listen_port = 6432
listen_addr = localhost
auth_type = md5
pool_mode = session
max_client_conn = 100
default_pool_size = 25
```

### 2. Indexes
Ensure these indexes exist:
```sql
CREATE INDEX idx_roads_state ON roads(state_code);
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_fullname ON roads(fullname);
CREATE INDEX idx_roads_linearid ON roads(linearid);
```

### 3. Monitoring
- Use `pg_stat_statements` for query analysis
- Monitor with Grafana + Prometheus
- Set up alerts for slow queries

## Migration Checklist

- [ ] Choose hosting option
- [ ] Install/Setup PostgreSQL
- [ ] Create database and user
- [ ] Import schema
- [ ] Import data (if available)
- [ ] Update connection strings
- [ ] Test application
- [ ] Setup backups
- [ ] Configure monitoring