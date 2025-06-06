#!/bin/bash

# Script to open TIGER road files in browser with delay
# This helps bypass Cloudflare protection by using your authenticated browser

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DELAY_SECONDS=5  # Delay between opening URLs (adjust as needed)
BATCH_SIZE=10    # Number of tabs to open before longer pause
LONG_PAUSE=30    # Longer pause after each batch

# Counter
count=0
batch_count=0

echo -e "${GREEN}TIGER Roads Browser Download Script${NC}"
echo -e "${YELLOW}This script will open each download link in your default browser${NC}"
echo -e "${YELLOW}Delay between URLs: ${DELAY_SECONDS} seconds${NC}"
echo -e "${YELLOW}Batch size: ${BATCH_SIZE} URLs${NC}"
echo -e "${YELLOW}Pause after batch: ${LONG_PAUSE} seconds${NC}"
echo ""
echo -e "${RED}Press Ctrl+C to stop at any time${NC}"
echo ""
read -p "Press Enter to start downloading..."

# Array of all URLs from TIGER_ROADS_DOWNLOAD.md
urls=(
# New York Metropolitan Area
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36061_roads.zip" # Manhattan
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36047_roads.zip" # Brooklyn
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36081_roads.zip" # Queens
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36005_roads.zip" # Bronx
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36085_roads.zip" # Staten Island
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_34013_roads.zip" # Essex County NJ
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_34017_roads.zip" # Hudson County NJ
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_34031_roads.zip" # Passaic County NJ
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36059_roads.zip" # Nassau County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36103_roads.zip" # Suffolk County

# Los Angeles Metropolitan Area
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06037_roads.zip" # Los Angeles County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06059_roads.zip" # Orange County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06065_roads.zip" # Riverside County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06071_roads.zip" # San Bernardino County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06111_roads.zip" # Ventura County

# San Francisco Bay Area
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06075_roads.zip" # San Francisco County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06001_roads.zip" # Alameda County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06085_roads.zip" # Santa Clara County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06013_roads.zip" # Contra Costa County
"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_06081_roads.zip" # San Mateo County

# Add more URLs here... (truncated for space - you'll need to add all 324 URLs)
)

# Function to open URL in browser
open_url() {
    local url=$1
    local filename=$(basename "$url")
    
    echo -e "${GREEN}[$count/${#urls[@]}]${NC} Opening: $filename"
    
    # Open in default browser (works on macOS)
    open "$url"
    
    # For Linux, use: xdg-open "$url"
    # For Windows WSL, use: cmd.exe /c start "$url"
}

# Main download loop
for url in "${urls[@]}"; do
    count=$((count + 1))
    batch_count=$((batch_count + 1))
    
    open_url "$url"
    
    # Check if we've completed a batch
    if [ $batch_count -eq $BATCH_SIZE ]; then
        echo -e "${YELLOW}Completed batch of $BATCH_SIZE downloads. Pausing for $LONG_PAUSE seconds...${NC}"
        echo -e "${YELLOW}You may want to move downloaded files to a folder before continuing${NC}"
        sleep $LONG_PAUSE
        batch_count=0
        echo -e "${GREEN}Continuing...${NC}"
    else
        # Regular delay between URLs
        sleep $DELAY_SECONDS
    fi
done

echo -e "${GREEN}✓ All downloads completed!${NC}"
echo -e "Total files: $count"