#!/bin/bash

echo "Monitoring POI import progress..."
echo "================================"

while true; do
    # Get current counts
    RESULT=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE nearest_road_id IS NOT NULL) as mapped,
            COUNT(*) FILTER (WHERE nearest_road_id IS NULL) as not_mapped
        FROM osm_businesses 
        WHERE state_code = 'DC';
    ")
    
    # Parse results
    TOTAL=$(echo $RESULT | awk '{print $1}')
    MAPPED=$(echo $RESULT | awk '{print $3}')
    NOT_MAPPED=$(echo $RESULT | awk '{print $5}')
    
    # Calculate percentage
    if [ $TOTAL -gt 0 ]; then
        PERCENT=$((MAPPED * 100 / TOTAL))
    else
        PERCENT=0
    fi
    
    # Get active query info
    ACTIVE_QUERY=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "
        SELECT COUNT(*) FROM pg_stat_activity 
        WHERE state = 'active' 
        AND query LIKE '%UPDATE osm_businesses%';
    " | tr -d ' ')
    
    # Display progress
    echo -ne "\r[$(date +'%H:%M:%S')] Total: $TOTAL | Mapped: $MAPPED | Remaining: $NOT_MAPPED | Progress: $PERCENT%"
    
    if [ "$ACTIVE_QUERY" = "0" ] && [ $NOT_MAPPED -eq 0 ]; then
        echo -e "\n\nImport completed!"
        break
    fi
    
    sleep 5
done