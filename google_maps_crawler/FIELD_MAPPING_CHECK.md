# Field Mapping Check - Backend to Frontend

## Backend API Returns (from get_unique_road_names)
```javascript
{
  osm_id: 123456,                    // OSM road ID (BIGINT)
  name: "Main Street",               // Road name
  highway: "residential",            // OSM highway type
  road_category: "Local Streets",    // Mapped category for frontend
  county_fips: "06037",              // County FIPS code
  state_code: "CA",                  // State code
  segment_count: 5,                  // Number of segments
  total_length_km: 2.5,              // Total length in km
  feature_class: "local road",       // Feature classification
  business_likelihood: "medium"      // Business likelihood
}
```

## Frontend Expects (in CrawlControl.js)
- `road.osm_id` - Used as key and for crawling
- `road.name` - Displayed as road name
- `road.highway` - Raw OSM type (displayed in table)
- `road.road_category` - Used for styling (Primary Roads, Secondary Roads, Local Streets, Special Roads)
- `road.county_fips` - County FIPS
- `road.state_code` - State code
- `road.segment_count` - Number of segments
- `road.total_length_km` - Road length
- `road.feature_class` - Feature classification
- `road.business_likelihood` - Business likelihood (high, medium, low)

## Road Category Mapping
Backend maps OSM highway types to frontend categories:
- `motorway, trunk` → "Primary Roads" (red styling)
- `primary, secondary, tertiary` → "Secondary Roads" (yellow styling)
- `residential, unclassified` → "Local Streets" (green styling)
- All others → "Special Roads" (gray styling)

## Road Type Filter Values
Frontend filter dropdown values:
- "all" - All Road Types
- "Primary Roads" - Motorways and trunk roads
- "Secondary Roads" - Primary, secondary and tertiary roads
- "Local Streets" - Residential and unclassified streets
- "Special Roads" - Service roads and others

## Status: ✅ All fields are properly mapped

The backend now returns exactly what the frontend expects. The field names, values, and categories all match correctly.