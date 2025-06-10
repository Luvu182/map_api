#!/bin/bash

# Full database backup script with compression and verification
# Usage: ./backup_database_full.sh

set -e  # Exit on error

# Configuration
DB_NAME="roads_db"
DB_USER="postgres"
CONTAINER_NAME="roads-postgres"
BACKUP_DIR="/Users/luvu/Data_US_100k_pop/postgres-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="backup_${TIMESTAMP}.sql.gz"

echo "==========================================="
echo "PostgreSQL Database Backup"
echo "==========================================="
echo "Database: $DB_NAME"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# 1. Get database statistics before backup
echo "1. Getting database statistics..."
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
SELECT 
    'Database Size' as metric,
    pg_size_pretty(pg_database_size('$DB_NAME')) as value
UNION ALL
SELECT 
    'Total Tables',
    COUNT(*)::text
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
UNION ALL
SELECT 
    'Total Roads',
    COUNT(*)::text
FROM osm_roads_main
UNION ALL
SELECT 
    'Cities Mapped',
    COUNT(DISTINCT city_name || '|' || state_code)::text
FROM road_city_mapping;"

# 2. Backup schema only (structure)
echo ""
echo "2. Backing up database schema..."
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME \
    --schema-only \
    --no-owner \
    --no-privileges \
    -f /tmp/schema_${TIMESTAMP}.sql

# Copy schema to host
docker cp $CONTAINER_NAME:/tmp/schema_${TIMESTAMP}.sql "$BACKUP_DIR/schema_${TIMESTAMP}.sql"

# 3. Full backup with data
echo ""
echo "3. Creating full database backup (this may take several minutes)..."
echo "   Please wait..."

# Using custom format for faster restore and better compression
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME \
    --format=custom \
    --verbose \
    --no-owner \
    --no-privileges \
    --file=/tmp/${BACKUP_FILE}.custom \
    2>&1 | grep -E "(dumping|backing)" || true

# Also create SQL format backup
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME \
    --no-owner \
    --no-privileges \
    --file=/tmp/${BACKUP_FILE}

# 4. Compress the SQL backup
echo ""
echo "4. Compressing backup..."
docker exec $CONTAINER_NAME gzip -9 /tmp/${BACKUP_FILE}

# 5. Copy backups to host
echo ""
echo "5. Copying backups to host..."
docker cp $CONTAINER_NAME:/tmp/${COMPRESSED_FILE} "$BACKUP_DIR/"
docker cp $CONTAINER_NAME:/tmp/${BACKUP_FILE}.custom "$BACKUP_DIR/backup_${TIMESTAMP}.custom"

# 6. Clean up container temp files
docker exec $CONTAINER_NAME rm -f /tmp/schema_${TIMESTAMP}.sql /tmp/${COMPRESSED_FILE} /tmp/${BACKUP_FILE}.custom

# 7. Create backup info file
echo ""
echo "6. Creating backup info..."
cat > "$BACKUP_DIR/backup_${TIMESTAMP}.info" << EOF
Backup Information
==================
Date: $(date)
Database: $DB_NAME
Container: $CONTAINER_NAME

Files created:
- schema_${TIMESTAMP}.sql (Schema only)
- backup_${TIMESTAMP}.sql.gz (Compressed full backup)
- backup_${TIMESTAMP}.custom (PostgreSQL custom format)

Database Statistics:
$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT 'Size: ' || pg_size_pretty(pg_database_size('$DB_NAME'))")
$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT 'Tables: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT 'Roads: ' || COUNT(*) FROM osm_roads_main")
$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "
SELECT 'Cities: ' || COUNT(DISTINCT city_name || state_code) FROM road_city_mapping")

To restore from backup:
=======================
# From compressed SQL:
gunzip -c backup_${TIMESTAMP}.sql.gz | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

# From custom format (faster):
docker exec -i $CONTAINER_NAME pg_restore -U $DB_USER -d $DB_NAME -v /path/to/backup_${TIMESTAMP}.custom

# Schema only:
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < schema_${TIMESTAMP}.sql
EOF

# 8. List all backups
echo ""
echo "7. Backup completed successfully!"
echo ""
echo "Backup files created in $BACKUP_DIR:"
ls -lh "$BACKUP_DIR" | grep "$TIMESTAMP"

# 9. Show disk usage
echo ""
echo "Backup sizes:"
du -h "$BACKUP_DIR"/*${TIMESTAMP}*

echo ""
echo "==========================================="
echo "Backup completed at $(date)"
echo "==========================================="

# Optional: Keep only last N backups (uncomment to enable)
# echo ""
# echo "Cleaning old backups (keeping last 5)..."
# cd "$BACKUP_DIR"
# ls -t backup_*.sql.gz | tail -n +6 | xargs -r rm -v
# ls -t backup_*.custom | tail -n +6 | xargs -r rm -v
# ls -t schema_*.sql | tail -n +6 | xargs -r rm -v
# ls -t backup_*.info | tail -n +6 | xargs -r rm -v