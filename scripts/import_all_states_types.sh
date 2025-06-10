#!/bin/bash
# Import POI types for all states and map to roads
# Consolidated version with all fixes

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# State list as pairs (no associative arrays for compatibility)
STATES=(
    "alabama:AL"
    "alaska:AK"
    "arizona:AZ"
    "arkansas:AR"
    "california:CA"
    "colorado:CO"
    "connecticut:CT"
    "delaware:DE"
    "district-of-columbia:DC"
    "florida:FL"
    "georgia:GA"
    "hawaii:HI"
    "idaho:ID"
    "illinois:IL"
    "indiana:IN"
    "iowa:IA"
    "kansas:KS"
    "kentucky:KY"
    "louisiana:LA"
    "maine:ME"
    "maryland:MD"
    "massachusetts:MA"
    "michigan:MI"
    "minnesota:MN"
    "mississippi:MS"
    "missouri:MO"
    "montana:MT"
    "nebraska:NE"
    "nevada:NV"
    "new-hampshire:NH"
    "new-jersey:NJ"
    "new-mexico:NM"
    "new-york:NY"
    "north-carolina:NC"
    "north-dakota:ND"
    "ohio:OH"
    "oklahoma:OK"
    "oregon:OR"
    "pennsylvania:PA"
    "rhode-island:RI"
    "south-carolina:SC"
    "south-dakota:SD"
    "tennessee:TN"
    "texas:TX"
    "utah:UT"
    "vermont:VT"
    "virginia:VA"
    "washington:WA"
    "west-virginia:WV"
    "wisconsin:WI"
    "wyoming:WY"
)

# Check which states already have data
echo -e "${GREEN}Checking existing imports...${NC}"
EXISTING=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "
    SELECT state_code FROM osm_businesses 
    GROUP BY state_code 
    HAVING COUNT(*) > 100
")

echo "Already imported: $EXISTING"
echo ""

# Process each state
for state_pair in "${STATES[@]}"; do
    IFS=':' read -r state_name STATE_CODE <<< "$state_pair"
    
    # Check if already imported
    if [[ $EXISTING =~ $STATE_CODE ]]; then
        echo -e "${YELLOW}⏭️  Skipping $STATE_CODE - already imported${NC}"
        continue
    fi
    
    # Check if file exists in raw_data
    LOCAL_FILE="/Users/luvu/Data_US_100k_pop/raw_data/data_osm/${state_name}-latest.osm.pbf"
    CONTAINER_FILE="/data/${state_name}-latest.osm.pbf"
    
    if [ ! -f "$LOCAL_FILE" ]; then
        echo -e "${RED}❌ No file for $STATE_CODE ($state_name)${NC}"
        continue
    fi
    
    echo -e "${GREEN}Processing $STATE_CODE ($state_name)...${NC}"
    
    # Check if state has roads before processing
    ROAD_COUNT=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "
        SELECT COUNT(*) FROM osm_roads_main WHERE state_code = '$STATE_CODE'
    " | tr -d ' ')
    
    if [ "$ROAD_COUNT" -eq "0" ]; then
        echo -e "  ${YELLOW}⚠️  No roads found for $STATE_CODE - skipping${NC}"
        continue
    fi
    
    # 1. Import POI types
    echo "  → Importing POIs..."
    if docker exec osm-python python3 /scripts/import_poi_types_only.py "$STATE_CODE" "$CONTAINER_FILE"; then
        
        # 2. Map to roads
        echo "  → Mapping to roads..."
        # Create temporary SQL with state code embedded
        cat > /tmp/map_${STATE_CODE}.sql << EOF
-- Map POIs to roads for $STATE_CODE
UPDATE osm_businesses b
SET nearest_road_id = sub.road_id
FROM (
    SELECT DISTINCT ON (b.osm_id)
        b.osm_id,
        r.osm_id as road_id
    FROM osm_businesses b
    CROSS JOIN LATERAL (
        SELECT osm_id
        FROM osm_roads_main r
        WHERE r.state_code = b.state_code
        ORDER BY r.geometry <-> b.geometry
        LIMIT 1
    ) r
    WHERE b.state_code = '$STATE_CODE'
    AND b.nearest_road_id IS NULL
) sub
WHERE b.osm_id = sub.osm_id;

-- Show results
SELECT 
    'State: $STATE_CODE' as info,
    COUNT(*) as total_pois,
    COUNT(nearest_road_id) as mapped_pois,
    ROUND(COUNT(nearest_road_id)::numeric / COUNT(*) * 100, 1) as percent_mapped
FROM osm_businesses
WHERE state_code = '$STATE_CODE';
EOF
        docker cp /tmp/map_${STATE_CODE}.sql roads-postgres:/tmp/
        docker exec roads-postgres psql -U postgres -d roads_db -f /tmp/map_${STATE_CODE}.sql
        rm -f /tmp/map_${STATE_CODE}.sql
        
        echo -e "${GREEN}✅ $STATE_CODE complete${NC}"
    else
        echo -e "${RED}❌ $STATE_CODE import failed${NC}"
    fi
    
    echo ""
    sleep 1  # Small pause between states
done

# Map the 3 states that have POIs but are not mapped yet
echo -e "${GREEN}Mapping states with unmapped POIs...${NC}"
for state in MI MD MA; do
    # Check if state has POIs and unmapped ones
    UNMAPPED=$(docker exec roads-postgres psql -U postgres -d roads_db -t -c "
        SELECT COUNT(*) FROM osm_businesses 
        WHERE state_code = '$state' AND nearest_road_id IS NULL
    " | tr -d ' ')
    
    if [ "$UNMAPPED" -gt "0" ]; then
        echo "  → Mapping $state ($UNMAPPED unmapped POIs)..."
        cat > /tmp/map_${state}.sql << EOF
UPDATE osm_businesses b
SET nearest_road_id = sub.road_id
FROM (
    SELECT DISTINCT ON (b.osm_id)
        b.osm_id,
        r.osm_id as road_id
    FROM osm_businesses b
    CROSS JOIN LATERAL (
        SELECT osm_id
        FROM osm_roads_main r
        WHERE r.state_code = b.state_code
        ORDER BY r.geometry <-> b.geometry
        LIMIT 1
    ) r
    WHERE b.state_code = '$state'
    AND b.nearest_road_id IS NULL
) sub
WHERE b.osm_id = sub.osm_id;

SELECT 
    'State: $state' as info,
    COUNT(*) as total_pois,
    COUNT(nearest_road_id) as mapped_pois,
    ROUND(COUNT(nearest_road_id)::numeric / COUNT(*) * 100, 1) as percent_mapped
FROM osm_businesses
WHERE state_code = '$state';
EOF
        docker cp /tmp/map_${state}.sql roads-postgres:/tmp/
        docker exec roads-postgres psql -U postgres -d roads_db -f /tmp/map_${state}.sql
        rm -f /tmp/map_${state}.sql
    fi
done

# Final summary
echo -e "${GREEN}=== FINAL SUMMARY ===${NC}"
docker exec roads-postgres psql -U postgres -d roads_db -c "
    SELECT 
        state_code,
        COUNT(*) as total_pois,
        COUNT(nearest_road_id) as mapped,
        ROUND(COUNT(nearest_road_id)::numeric / COUNT(*) * 100, 1) as pct_mapped,
        COUNT(DISTINCT business_type) as types,
        COUNT(DISTINCT business_subtype) as subtypes
    FROM osm_businesses
    GROUP BY state_code
    ORDER BY total_pois DESC
"

# Create business score view
echo -e "${GREEN}Creating business potential scores...${NC}"
docker exec roads-postgres psql -U postgres -d roads_db -f /scripts/create_road_business_score.sql

echo -e "${GREEN}✅ All done!${NC}"