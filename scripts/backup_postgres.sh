#!/bin/bash
# PostgreSQL Backup Script

BACKUP_DIR="./postgres-backups"
DB_NAME="roads_db"
DB_USER="postgres"
CONTAINER_NAME="roads-postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Starting PostgreSQL backup..."

# Create full backup (compressed)
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

if [ $? -eq 0 ]; then
    echo "✓ Backup completed: backup_$DATE.sql.gz"
    
    # Get backup size
    SIZE=$(ls -lh $BACKUP_DIR/backup_$DATE.sql.gz | awk '{print $5}')
    echo "✓ Backup size: $SIZE"
    
    # Keep only last 7 days of backups
    find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
    echo "✓ Old backups cleaned up (kept last 7 days)"
    
    # Count remaining backups
    COUNT=$(ls -1 $BACKUP_DIR/backup_*.sql.gz 2>/dev/null | wc -l)
    echo "✓ Total backups: $COUNT"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Optional: Create schema-only backup
docker exec $CONTAINER_NAME pg_dump -U $DB_USER -d $DB_NAME --schema-only > $BACKUP_DIR/schema_latest.sql
echo "✓ Schema backup updated"

echo "Backup process completed!"