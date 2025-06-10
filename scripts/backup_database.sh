#!/bin/bash
# Automated backup script for PostgreSQL roads database

# Configuration
BACKUP_DIR="/Users/luvu/Data_US_100k_pop/backups"
DB_CONTAINER="roads-postgres"
DB_NAME="roads_db"
DB_USER="postgres"
KEEP_DAYS=7
LOG_FILE="$BACKUP_DIR/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start backup
log_message "Starting database backup..."

# Check if Docker container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    log_message "ERROR: Docker container $DB_CONTAINER is not running!"
    exit 1
fi

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="roads_backup_$TIMESTAMP.sql.gz"

log_message "Creating backup: $BACKUP_FILE"

# Perform backup
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"; then
    # Get backup size
    BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    log_message "Backup completed successfully. Size: $BACKUP_SIZE"
    
    # Verify backup integrity
    if gunzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
        log_message "Backup integrity verified."
    else
        log_message "WARNING: Backup file may be corrupted!"
    fi
else
    log_message "ERROR: Backup failed!"
    exit 1
fi

# Clean up old backups
log_message "Cleaning up backups older than $KEEP_DAYS days..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "roads_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete -print | wc -l)
log_message "Deleted $DELETED_COUNT old backup(s)."

# Show current backups
log_message "Current backups:"
ls -lht "$BACKUP_DIR"/roads_backup_*.sql.gz 2>/dev/null | head -10 | while read line; do
    log_message "  $line"
done

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
log_message "Total backup directory size: $TOTAL_SIZE"

log_message "Backup process completed."
echo ""