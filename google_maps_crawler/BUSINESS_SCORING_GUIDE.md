# Business Location Scoring System

## Overview
The system provides comprehensive analysis of business locations with scores from 0-100 based on multiple factors.

## Scoring Components

### 1. Density Score (0-30 points)
- Road density per km²
- Intersection density
- Higher density = better for business

### 2. Accessibility Score (0-30 points)
- Distance to major roads
- Distance to highways
- Closer = higher score

### 3. Road Quality Score (0-20 points)
- Average number of lanes
- High capacity roads
- One-way streets (traffic flow)

### 4. Area Type Score (0-20 points)
- Penalizes purely residential areas
- Rewards commercial/mixed areas
- Major road presence

### 5. Traffic Flow Score (0-10 points)
- Average speed limits
- High-speed road availability

## Rating System
- **90-100**: Excellent - Highly recommended for business
- **80-89**: Excellent - Strong business potential
- **65-79**: Very Good - Good opportunities
- **50-64**: Good - Suitable for most businesses
- **35-49**: Fair - Limited potential
- **20-34**: Poor - Primarily residential
- **0-19**: Very Poor - Not recommended

## Business Type Recommendations
Based on score, the system recommends suitable business types:
- **High scores (80+)**: Retail, restaurants, services, offices
- **Medium scores (50-79)**: Services, small retail, professional offices
- **Low scores (<50)**: Home services, delivery-based businesses

## Area Classifications
- **Rural**: Very low density, wide search radius needed
- **Suburban Residential**: Primarily homes, low business potential
- **Suburban Mixed**: Balance of residential/commercial
- **Urban Mixed**: High density, good business potential
- **Urban Commercial**: Best for business, high traffic

## Usage in Code

```python
from app.crawler.business_analyzer import BusinessAnalyzer

# Initialize
analyzer = BusinessAnalyzer(db_client)

# Get full analysis
analysis = analyzer.analyze_location(lat, lon, radius_km=0.5)
print(f"Score: {analysis['score']}")
print(f"Best for: {', '.join(analysis['business_insights']['best_for'])}")

# Check if worth crawling
if analyzer.should_crawl_location(lat, lon, min_score=35):
    # Proceed with Google Maps crawling
    pass

# Get optimal search radius
classification = analyzer.get_area_classification(lat, lon)
radius = analyzer.get_recommended_search_radius(classification['area_type'])
```

## Integration with Crawler
The analyzer can be used to:
1. Filter locations before expensive API calls
2. Adjust search radius based on area density
3. Prioritize high-potential areas
4. Skip residential-only zones

## Database Functions
- `calculate_business_score_advanced(lat, lon, radius)` - Full analysis
- `classify_area_type(lat, lon, radius)` - Simple classification
- `analyze_area_details(lat, lon, radius)` - Detailed metrics