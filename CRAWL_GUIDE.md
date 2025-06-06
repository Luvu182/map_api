# Hướng dẫn Crawl Data TIGER/Line

## Tổng quan
TIGER/Line Roads data được tổ chức theo county. Mỗi county có 1 file shapefile riêng.

## URL Pattern
```
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_{STATE_FIPS}{COUNTY_FIPS}_roads.zip
```
Ví dụ: `tl_2024_01001_roads.zip` cho Autauga County, Alabama

## Bước 1: Xác định Counties cần crawl

### Script Python để tìm counties cho 346 cities
```python
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Load city list
cities_df = pd.read_csv('cities_100k.csv')

# Function to find county for city
def find_county(city, state):
    # Sử dụng Census Geocoding API hoặc
    # Download file PLACE để mapping
    pass

# Map cities to counties
city_county_mapping = {}
for idx, row in cities_df.iterrows():
    counties = find_county(row['City'], row['State'])
    city_county_mapping[row['City']] = counties
```

## Bước 2: Download Shapefiles

### Script download với retry logic
```python
import os
import time
import zipfile
import requests
from tqdm import tqdm

BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2024/ROADS/"
OUTPUT_DIR = "raw_data/shapefiles/"

def download_county_roads(county_fips, max_retries=3):
    filename = f"tl_2024_{county_fips}_roads.zip"
    url = BASE_URL + filename
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract zip file
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                extract_dir = output_path.replace('.zip', '')
                zip_ref.extractall(extract_dir)
            
            return True
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(5)
    
    return False

# Download all counties
counties_to_download = list(set(city_county_mapping.values()))
for county_fips in tqdm(counties_to_download):
    download_county_roads(county_fips)
    time.sleep(1)  # Be nice to the server
```
## Bước 3: Verify Downloads

### Script kiểm tra tính toàn vẹn
```python
import geopandas as gpd
import os

def verify_shapefile(shapefile_path):
    try:
        gdf = gpd.read_file(shapefile_path)
        return {
            'valid': True,
            'rows': len(gdf),
            'columns': list(gdf.columns),
            'crs': gdf.crs
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}

# Verify all downloads
for county_dir in os.listdir(OUTPUT_DIR):
    if os.path.isdir(os.path.join(OUTPUT_DIR, county_dir)):
        shp_file = os.path.join(OUTPUT_DIR, county_dir, f"{county_dir}.shp")
        result = verify_shapefile(shp_file)
        print(f"{county_dir}: {result}")
```

## Lưu ý quan trọng
1. **Kích thước**: Mỗi file zip ~1-50MB tùy county
2. **Tổng dung lượng**: Ước tính ~5-10GB cho 346 cities
3. **Rate limiting**: Delay 1 giây giữa các request
4. **Missing counties**: Một số small cities có thể không có data riêng

## Alternative: Bulk Download
Nếu cần nhiều counties, có thể download theo state:
- Pattern: `tl_2024_{STATE_FIPS}_roads.zip`
- Chứa TẤT CẢ roads trong state (file lớn hơn nhiều)