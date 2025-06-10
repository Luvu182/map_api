"""
Smart Crawl API - Integrates OSM POI data with Google Maps
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/smart-crawl/road/{road_id}")
async def smart_crawl_road(road_id: int, db):
    """
    Smart crawl a road using POI data to optimize Google API calls
    """
    
    # 1. Get road info
    road = await db.fetch_one("""
        SELECT osm_id, name, state_code, county_fips,
               ST_AsGeoJSON(geometry) as geometry_json
        FROM osm_roads_main
        WHERE osm_id = :road_id
    """, {"road_id": road_id})
    
    if not road:
        raise HTTPException(404, "Road not found")
    
    # 2. Get POIs along this road from OSM
    pois = await db.fetch_all("""
        SELECT 
            osm_id, name, brand,
            business_type, business_subtype,
            phone, website, opening_hours,
            lat, lon, business_score,
            housenumber, street, city, postcode
        FROM osm_businesses
        WHERE nearest_road_id = :road_id
        ORDER BY business_score DESC
    """, {"road_id": road_id})
    
    # 3. Analyze what we have vs what we need
    crawl_strategy = analyze_crawl_needs(pois)
    
    # 4. Generate optimized crawl points
    crawl_points = []
    
    if crawl_strategy['mode'] == 'targeted':
        # Mode 1: Target specific POIs missing data
        for poi in pois:
            if needs_enrichment(poi):
                crawl_points.append({
                    'lat': poi['lat'],
                    'lon': poi['lon'],
                    'radius': 50,  # Small radius - we know exact location
                    'target_name': poi['name'],
                    'target_brand': poi['brand'],
                    'osm_id': poi['osm_id'],
                    'priority': calculate_priority(poi)
                })
                
    elif crawl_strategy['mode'] == 'discovery':
        # Mode 2: Find businesses not in OSM
        # Create points between known POIs
        crawl_points = generate_discovery_points(road, pois)
        
    elif crawl_strategy['mode'] == 'verification':
        # Mode 3: Verify existing data
        for poi in pois[:20]:  # Top 20 by score
            crawl_points.append({
                'lat': poi['lat'],
                'lon': poi['lon'],
                'radius': 30,
                'verify_name': poi['name'],
                'verify_phone': poi['phone'],
                'osm_id': poi['osm_id']
            })
    
    # 5. Return crawl plan
    return {
        'road': {
            'id': road['osm_id'],
            'name': road['name']
        },
        'osm_stats': {
            'total_pois': len(pois),
            'with_phone': sum(1 for p in pois if p['phone']),
            'with_website': sum(1 for p in pois if p['website']),
            'with_hours': sum(1 for p in pois if p['opening_hours']),
            'brands': len(set(p['brand'] for p in pois if p['brand']))
        },
        'crawl_strategy': crawl_strategy,
        'crawl_points': crawl_points[:50],  # Limit to 50 points
        'estimated_api_calls': len(crawl_points)
    }

def analyze_crawl_needs(pois: List[Dict]) -> Dict:
    """Analyze POIs to determine best crawl strategy"""
    
    if not pois:
        return {
            'mode': 'discovery',
            'reason': 'No POIs found - full discovery needed',
            'priority': 'high'
        }
    
    # Calculate data completeness
    total = len(pois)
    with_phone = sum(1 for p in pois if p['phone'])
    with_website = sum(1 for p in pois if p['website'])
    with_hours = sum(1 for p in pois if p['opening_hours'])
    
    phone_pct = with_phone / total * 100
    website_pct = with_website / total * 100
    hours_pct = with_hours / total * 100
    
    # Determine strategy
    if phone_pct < 30:
        return {
            'mode': 'targeted',
            'reason': f'Low phone coverage ({phone_pct:.0f}%)',
            'focus': 'contact_info',
            'priority': 'high'
        }
    elif hours_pct < 40:
        return {
            'mode': 'targeted',
            'reason': f'Low hours coverage ({hours_pct:.0f}%)',
            'focus': 'operating_hours',
            'priority': 'medium'
        }
    elif total < 5:
        return {
            'mode': 'discovery',
            'reason': 'Few POIs - likely missing businesses',
            'priority': 'high'
        }
    else:
        return {
            'mode': 'verification',
            'reason': 'Good coverage - verify accuracy',
            'priority': 'low'
        }

def needs_enrichment(poi: Dict) -> bool:
    """Check if POI needs data enrichment"""
    # High priority: Missing critical data
    if not poi.get('phone') and poi.get('business_score', 0) > 30:
        return True
    if not poi.get('opening_hours') and poi.get('brand'):
        return True
    if not poi.get('website') and poi.get('business_type') in ['shop', 'amenity']:
        return True
    return False

def calculate_priority(poi: Dict) -> int:
    """Calculate crawl priority for a POI"""
    priority = 0
    
    # Brand bonus
    if poi.get('brand'):
        priority += 20
        
    # Missing data penalty
    if not poi.get('phone'):
        priority += 15
    if not poi.get('opening_hours'):
        priority += 10
    if not poi.get('website'):
        priority += 5
        
    # Business type bonus
    if poi.get('business_subtype') in ['restaurant', 'fuel', 'bank', 'pharmacy']:
        priority += 10
        
    return priority

def generate_discovery_points(road: Dict, existing_pois: List[Dict]) -> List[Dict]:
    """Generate points to discover new businesses"""
    import json
    from shapely.geometry import LineString, Point
    
    # Parse road geometry
    geom = json.loads(road['geometry_json'])
    line = LineString(geom['coordinates'])
    
    # Generate points every 200m along road
    points = []
    distance = 0
    
    while distance < line.length:
        point = line.interpolate(distance)
        
        # Check if point is far from existing POIs
        min_distance = float('inf')
        for poi in existing_pois:
            poi_point = Point(poi['lon'], poi['lat'])
            dist = point.distance(poi_point) * 111000  # Convert to meters
            min_distance = min(min_distance, dist)
            
        # Only add if >100m from known POIs
        if min_distance > 100:
            points.append({
                'lat': point.y,
                'lon': point.x,
                'radius': 200,  # Larger radius for discovery
                'mode': 'discovery'
            })
            
        distance += 0.002  # ~200m
        
    return points[:30]  # Limit discovery points

@router.get("/api/smart-crawl/suggestions/{state_code}")
async def get_crawl_suggestions(state_code: str, db, limit: int = 20):
    """
    Get road suggestions for crawling based on POI analysis
    """
    
    suggestions = await db.fetch_all("""
        SELECT 
            road_id,
            road_name,
            total_businesses,
            chain_stores,
            missing_phone,
            missing_website,
            crawl_priority_score
        FROM road_business_density
        WHERE state_code = :state_code
        AND total_businesses >= 3
        ORDER BY crawl_priority_score DESC
        LIMIT :limit
    """, {"state_code": state_code, "limit": limit})
    
    return {
        'state_code': state_code,
        'suggestions': [
            {
                'road_id': s['road_id'],
                'road_name': s['road_name'],
                'metrics': {
                    'total_businesses': s['total_businesses'],
                    'chain_stores': s['chain_stores'],
                    'missing_phone': s['missing_phone'],
                    'missing_website': s['missing_website']
                },
                'priority_score': s['crawl_priority_score'],
                'recommended_action': get_recommendation(s)
            }
            for s in suggestions
        ]
    }

def get_recommendation(road_stats: Dict) -> str:
    """Get crawl recommendation for a road"""
    missing_pct = (road_stats['missing_phone'] / road_stats['total_businesses'] * 100
                   if road_stats['total_businesses'] > 0 else 0)
    
    if missing_pct > 70:
        return "High priority - Many businesses missing contact info"
    elif road_stats['chain_stores'] > 5:
        return "Target chain stores for consistent data"
    elif road_stats['total_businesses'] > 20:
        return "High density area - batch crawl recommended"
    else:
        return "Standard crawl recommended"

@router.post("/api/smart-crawl/execute")
async def execute_smart_crawl(request: Dict, db):
    """
    Execute crawl with Google Maps API using smart strategy
    """
    crawl_points = request['crawl_points']
    results = []
    
    for point in crawl_points:
        # Call Google Places API with optimized parameters
        if point.get('target_name'):
            # Targeted search for specific business
            google_results = await search_specific_business(
                point['lat'], point['lon'],
                point['target_name'],
                point.get('target_brand')
            )
        else:
            # Discovery search
            google_results = await search_nearby_businesses(
                point['lat'], point['lon'],
                point['radius']
            )
            
        # Process results
        for place in google_results:
            # Check if already in OSM
            osm_match = await find_osm_match(place, db)
            
            if osm_match:
                # Update existing POI
                await update_osm_business(osm_match['osm_id'], place, db)
                results.append({
                    'action': 'updated',
                    'osm_id': osm_match['osm_id'],
                    'name': place['name']
                })
            else:
                # New business found
                await insert_google_business(place, db)
                results.append({
                    'action': 'created',
                    'name': place['name'],
                    'address': place.get('formatted_address')
                })
                
    return {
        'crawl_summary': {
            'points_processed': len(crawl_points),
            'businesses_found': len(results),
            'updated': sum(1 for r in results if r['action'] == 'updated'),
            'created': sum(1 for r in results if r['action'] == 'created')
        },
        'results': results[:100]  # Limit response size
    }