# PostgreSQL Self-Host Migration Guide

## Overview
Hướng dẫn này giúp bạn setup PostgreSQL với PostGIS locally và dễ dàng migrate lên VPS sau này.

## 1. Setup Local Development (macOS)

### Option A: Docker (Recommended)

#### Step 1: Install Docker Desktop
```bash
# Download Docker Desktop từ https://www.docker.com/products/docker-desktop/
# Hoặc dùng Homebrew
brew install --cask docker
```

#### Step 2: Create docker-compose.yml
```yaml
version: '3.8'
services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: roads-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_secure_password_here
      POSTGRES_DB: roads_db
    ports:
      - "5432:5432"
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./postgres-backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### Step 3: Start PostgreSQL
```bash
# Create directories
mkdir -p postgres-data postgres-backups

# Start container
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f postgres
```

#### Step 4: Enable PostGIS Extension
```bash
# Connect to database
docker exec -it roads-postgres psql -U postgres -d roads_db

# In psql console
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
\q
```

### Option B: Direct Installation
```bash
# Install PostgreSQL
brew install postgresql@15
brew install postgis

# Start service
brew services start postgresql@15

# Create database
createdb roads_db

# Enable PostGIS
psql -d roads_db -c "CREATE EXTENSION postgis;"
```

## 2. Database Schema Setup

### Create Tables
```sql
-- Connect to database
psql -h localhost -U postgres -d roads_db

-- States table
CREATE TABLE IF NOT EXISTS states (
    state_code CHAR(2) PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    total_counties INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Counties table
CREATE TABLE IF NOT EXISTS counties (
    county_fips CHAR(5) PRIMARY KEY,
    county_name VARCHAR(100) NOT NULL,
    state_code CHAR(2) NOT NULL,
    total_roads INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code)
);

-- Roads table with PostGIS geometry
CREATE TABLE IF NOT EXISTS roads (
    id BIGSERIAL PRIMARY KEY,
    linear_id VARCHAR(22) NOT NULL,
    full_name VARCHAR(100),
    rttyp VARCHAR(1),
    mtfcc VARCHAR(5),
    state_code CHAR(2) NOT NULL,
    county_fips CHAR(5) NOT NULL,
    geom GEOMETRY(LINESTRING, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (county_fips) REFERENCES counties(county_fips)
);

-- Create indexes
CREATE INDEX idx_roads_linear_id ON roads(linear_id);
CREATE INDEX idx_roads_full_name ON roads(full_name);
CREATE INDEX idx_roads_county ON roads(county_fips);
CREATE INDEX idx_roads_state ON roads(state_code);
CREATE INDEX idx_roads_geom ON roads USING GIST(geom);

-- Create text search indexes
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_roads_fullname_trgm ON roads USING GIN (full_name gin_trgm_ops);
```

## 3. Environment Configuration

### Create .env file
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=roads_db
DB_USER=postgres
DB_PASSWORD=your_secure_password_here

# Connection Pool
DB_POOL_MIN=10
DB_POOL_MAX=50

# Application
APP_ENV=development
```

### Python Connection Setup
```python
# config/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv('DB_POOL_MIN', 10)),
    max_overflow=int(os.getenv('DB_POOL_MAX', 50)),
    pool_pre_ping=True,
    echo=False
)
```

## 4. Data Migration from Supabase

### Export from Supabase
```bash
# Export schema and data
pg_dump \
  --no-owner \
  --no-acl \
  --schema=public \
  postgres://[YOUR_SUPABASE_URL] > supabase_export.sql

# Export only data (if schema already exists)
pg_dump \
  --data-only \
  --no-owner \
  --no-acl \
  postgres://[YOUR_SUPABASE_URL] > supabase_data.sql
```

### Import to Local PostgreSQL
```bash
# Import to Docker PostgreSQL
docker exec -i roads-postgres psql -U postgres -d roads_db < supabase_export.sql

# Or import specific tables
docker exec -i roads-postgres psql -U postgres -d roads_db < states.sql
docker exec -i roads-postgres psql -U postgres -d roads_db < counties.sql
docker exec -i roads-postgres psql -U postgres -d roads_db < roads.sql
```

## 5. Backup Strategies

### Manual Backup
```bash
# Full backup
docker exec roads-postgres pg_dump -U postgres -d roads_db > backups/roads_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec roads-postgres pg_dump -U postgres -d roads_db | gzip > backups/roads_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
docker exec roads-postgres pg_dump -U postgres -d roads_db -t roads -t counties -t states > backups/tables_backup.sql
```

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="./postgres-backups"
DB_NAME="roads_db"
DB_USER="postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
docker exec roads-postgres pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### Cron job for automated backups
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh >> /path/to/backup.log 2>&1
```

## 6. VPS Migration Guide

### Prerequisites
- VPS với Ubuntu 20.04+ hoặc Debian 11+
- Minimum 4GB RAM
- 50GB+ SSD storage
- Docker installed

### Step 1: Prepare VPS
```bash
# SSH to VPS
ssh user@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Transfer Files
```bash
# From local machine
# Copy docker-compose.yml
scp docker-compose.yml user@vps-ip:~/

# Copy .env file (edit passwords first!)
scp .env user@vps-ip:~/

# Copy backup file
scp postgres-backups/latest_backup.sql.gz user@vps-ip:~/
```

### Step 3: Setup on VPS
```bash
# On VPS
mkdir -p postgres-data postgres-backups

# Start PostgreSQL
docker-compose up -d

# Wait for PostgreSQL to be ready
sleep 10

# Restore database
gunzip -c latest_backup.sql.gz | docker exec -i roads-postgres psql -U postgres -d roads_db
```

### Step 4: Configure Firewall
```bash
# Allow PostgreSQL only from specific IPs (optional)
sudo ufw allow from YOUR_IP to any port 5432

# Or allow from anywhere (less secure)
sudo ufw allow 5432/tcp
```

## 7. Performance Optimization

### PostgreSQL Configuration
Add to `postgresql.conf` or docker-compose environment:
```yaml
services:
  postgres:
    # ... other config ...
    command: >
      postgres
      -c shared_buffers=1GB
      -c effective_cache_size=3GB
      -c maintenance_work_mem=256MB
      -c work_mem=64MB
      -c max_connections=200
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
```

### Connection Pooling with PgBouncer
```yaml
# Add to docker-compose.yml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    DATABASES_DATABASE: roads_db
    DATABASES_USER: postgres
    DATABASES_PASSWORD: your_secure_password_here
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 50
  ports:
    - "6432:6432"
  depends_on:
    - postgres
```

## 8. Monitoring

### Basic Health Check
```bash
# Check database size
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT pg_database_size('roads_db')/1024/1024 as size_mb;"

# Check table sizes
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"

# Check active connections
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### Monitoring Script
```bash
#!/bin/bash
# monitor.sh
echo "=== PostgreSQL Status ==="
docker exec roads-postgres psql -U postgres -c "SELECT version();"
echo ""
echo "=== Database Size ==="
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT pg_database_size('roads_db')/1024/1024 as size_mb;"
echo ""
echo "=== Top 5 Tables by Size ==="
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 5;"
```

## 9. Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

#### 2. Out of Memory
```bash
# Check memory usage
docker stats roads-postgres

# Adjust shared_buffers in docker-compose.yml
```

#### 3. Slow Queries
```bash
# Enable query logging
docker exec roads-postgres psql -U postgres -d roads_db -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker-compose restart postgres

# Check slow queries
docker exec roads-postgres tail -f /var/log/postgresql/postgresql.log
```

## 10. Security Best Practices

### 1. Change Default Passwords
```bash
# Generate secure password
openssl rand -base64 32
```

### 2. Restrict Network Access
```yaml
# docker-compose.yml
services:
  postgres:
    # Only listen on localhost
    ports:
      - "127.0.0.1:5432:5432"
```

### 3. Regular Updates
```bash
# Update Docker images
docker-compose pull
docker-compose up -d
```

### 4. SSL/TLS for Remote Connections
```bash
# Generate certificates
openssl req -new -text -passout pass:abcd -subj /CN=server -out server.req -keyout privkey.pem
openssl rsa -in privkey.pem -passin pass:abcd -out server.key
openssl req -x509 -in server.req -text -key server.key -out server.crt
chmod 600 server.key

# Configure PostgreSQL for SSL
# Add to postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

## Quick Commands Reference

```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# View logs
docker-compose logs -f postgres

# Connect to database
docker exec -it roads-postgres psql -U postgres -d roads_db

# Backup database
docker exec roads-postgres pg_dump -U postgres -d roads_db > backup.sql

# Restore database
docker exec -i roads-postgres psql -U postgres -d roads_db < backup.sql

# Check database size
docker exec roads-postgres psql -U postgres -d roads_db -c "SELECT pg_database_size('roads_db')/1024/1024 || ' MB' as size;"

# List all tables
docker exec roads-postgres psql -U postgres -d roads_db -c "\dt"

# Restart container
docker-compose restart postgres
```

## Conclusion
Với setup này, bạn có thể:
1. Develop locally với Docker
2. Backup data dễ dàng
3. Migrate lên VPS chỉ trong 10 phút
4. Scale khi cần thiết

Happy coding! 🚀