# City to County Mapping Guide

## Thách thức
- Một city có thể nằm trong nhiều counties
- City boundaries không khớp hoàn toàn với county boundaries
- Cần xác định chính xác counties nào chứa roads của city

## Phương pháp Mapping

### 1. Sử dụng Census PLACE files
```python
# Download PLACE boundaries
place_url = "https://www2.census.gov/geo/tiger/TIGER2024/PLACE/"
# Contains city boundaries as polygons

# Spatial join với county boundaries
county_url = "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/"
```

### 2. Census Geocoding API
```python
import requests

def get_county_for_city(city, state, lat, lon):
    base_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        'x': lon,
        'y': lat,
        'benchmark': '2020',
        'vintage': '2020',
        'layers': 'Counties',
        'format': 'json'
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if data['result']['geographies']['Counties']:
        county = data['result']['geographies']['Counties'][0]
        return {
            'county_fips': county['STATE'] + county['COUNTY'],
            'county_name': county['NAME']
        }
    return None
```

### 3. Pre-built Mapping cho 346 cities
```python
# Major cities và counties tương ứng
city_county_map = {
    ('New York', 'NY'): ['36061', '36047', '36081', '36005', '36085'],  # 5 boroughs
    ('Los Angeles', 'CA'): ['06037'],  # Los Angeles County
    ('Chicago', 'IL'): ['17031'],  # Cook County
    ('Houston', 'TX'): ['48201', '48157', '48039'],  # Harris, Fort Bend, Montgomery
    # ... thêm cities khác
}
```

## Script Tự động Mapping
```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load data
cities_df = pd.read_csv('cities_100k.csv')
counties_gdf = gpd.read_file('counties.shp')
places_gdf = gpd.read_file('places.shp')

# Method 1: Point in Polygon (cho city centers)
city_points = gpd.GeoDataFrame(
    cities_df,
    geometry=[Point(xy) for xy in zip(cities_df.lon, cities_df.lat)]
)
city_county_join = gpd.sjoin(city_points, counties_gdf, how='left', predicate='within')

# Method 2: Polygon overlap (cho city boundaries)
city_boundaries = places_gdf[places_gdf['NAME'].isin(cities_df['City'])]
city_county_overlap = gpd.overlay(city_boundaries, counties_gdf, how='intersection')

# Combine results
final_mapping = combine_mapping_results(city_county_join, city_county_overlap)
```

## Output Format
```csv
city,state_code,primary_county_fips,all_county_fips
"New York","NY","36061","36061|36047|36081|36005|36085"
"Los Angeles","CA","06037","06037"
"Chicago","IL","17031","17031"
```