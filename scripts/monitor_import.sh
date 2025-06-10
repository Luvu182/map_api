#!/bin/bash
# Monitor POI import progress

STATE=$1
if [ -z "$STATE" ]; then
    echo "Usage: ./monitor_import.sh STATE_CODE"
    exit 1
fi

echo "🔍 Monitoring import for $STATE..."
echo "================================"

while true; do
    # Get counts
    TOTAL=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "SELECT COUNT(*) FROM osm_businesses WHERE state_code = '$STATE'")
    WITH_CITY=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "SELECT COUNT(*) FROM osm_businesses WHERE state_code = '$STATE' AND city IS NOT NULL")
    WITH_ROAD=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "SELECT COUNT(*) FROM osm_businesses WHERE state_code = '$STATE' AND nearest_road_id IS NOT NULL")
    
    # Check if python process is still running
    PYTHON_PID=$(docker exec osm-python pgrep -f "import_osm_pois_smart.py $STATE")
    
    clear
    echo "📊 Import Progress for $STATE"
    echo "================================"
    echo "Total POIs imported: $TOTAL"
    echo "Mapped to city: $WITH_CITY"
    echo "Mapped to road: $WITH_ROAD"
    echo ""
    
    if [ -z "$PYTHON_PID" ]; then
        echo "✅ Import completed!"
        break
    else
        echo "🔄 Still processing... (PID: $PYTHON_PID)"
        # Show current SQL query
        CURRENT_QUERY=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "SELECT LEFT(query, 60) FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%' LIMIT 1")
        if [ ! -z "$CURRENT_QUERY" ]; then
            echo "Current step: $CURRENT_QUERY"
        fi
    fi
    
    sleep 5
done

# Final stats
echo ""
echo "📈 Final Statistics:"
docker exec roads-postgres psql -U postgres -d roads_db -c "
SELECT 
    business_type,
    COUNT(*) as count,
    COUNT(DISTINCT brand) as brands
FROM osm_businesses
WHERE state_code = '$STATE'
GROUP BY business_type
ORDER BY count DESC;"