#!/bin/bash

# Test script - Download only a few cities first
# This helps you test the process before downloading all 325 files

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== TIGER Roads Test Download ===${NC}"
echo -e "${YELLOW}This will download 5 test files from major cities${NC}"
echo ""

# Test URLs (5 major cities)
urls=(
    "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36061_roads.zip"  # Manhattan, NY
    "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06037_roads.zip"  # Los Angeles, CA
    "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_17031_roads.zip"  # Chicago, IL
    "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_48201_roads.zip"  # Houston, TX
    "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_04013_roads.zip"  # Phoenix, AZ
)

cities=(
    "Manhattan (New York County)"
    "Los Angeles County"
    "Cook County (Chicago)"
    "Harris County (Houston)"
    "Maricopa County (Phoenix)"
)

echo "Will download:"
for i in "${!cities[@]}"; do
    echo -e "  ${BLUE}${cities[$i]}${NC}"
done
echo ""

read -p "Press Enter to start test download..."

# Download loop
for i in "${!urls[@]}"; do
    echo -e "${GREEN}[$(($i+1))/${#urls[@]}]${NC} Opening: ${cities[$i]}"
    open "${urls[$i]}"
    
    if [ $i -lt $((${#urls[@]} - 1)) ]; then
        echo "Waiting 3 seconds before next..."
        sleep 3
    fi
done

echo -e "${GREEN}✓ Test downloads completed!${NC}"
echo ""
echo "If the downloads worked correctly, you can run the full script:"
echo "  ./download_tiger_browser_full.sh"