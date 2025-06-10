"""
Google Maps Places API (New) wrapper
Migrated to use the new Places API v1 for better performance and cost optimization
"""
import requests
from typing import List, Dict, Optional, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import GOOGLE_MAPS_API_KEY, MAX_RESULTS_PER_LOCATION
from ..models import Business
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class GoogleMapsClient:
    def __init__(self):
        self.api_key = GOOGLE_MAPS_API_KEY
        logger.info(f"Loaded API key from config: {self.api_key}")
        if not self.api_key or self.api_key == 'your_google_maps_api_key_here':
            logger.warning("Google Maps API key not configured - crawling disabled")
            self.api_key = None
        else:
            logger.info(f"Google Maps API key configured: {self.api_key[:8]}...")
        
        # New Places API endpoints
        self.base_url = "https://places.googleapis.com/v1"
        self.text_search_url = f"{self.base_url}/places:searchText"
        self.place_details_url = f"{self.base_url}/places"
        
        # Field masks for different tiers - MUST include nextPageToken for pagination
        self.field_masks = {
            'basic': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,nextPageToken',
            'pro': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.rating,places.userRatingCount,places.priceLevel,nextPageToken',
            'enterprise': (
                'places.id,places.displayName,places.formattedAddress,places.location,places.types,'
                'places.currentOpeningHours,places.currentSecondaryOpeningHours,'
                'places.internationalPhoneNumber,places.nationalPhoneNumber,'
                'places.priceLevel,places.priceRange,places.rating,'
                'places.regularOpeningHours,places.regularSecondaryOpeningHours,'
                'places.userRatingCount,places.websiteUri,nextPageToken'
            ),
            'enterprise_minimal': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.nationalPhoneNumber,nextPageToken'
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_text(
        self, 
        query: str,
        location_bias: Optional[Dict] = None,
        tier: str = 'enterprise'
    ) -> List[Dict]:
        """
        Search for places using text query (New API)
        More efficient than nearby search for road-based searches
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return []
            
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': self.field_masks.get(tier, self.field_masks['enterprise'])
            }
            
            # Build request body
            body = {
                'textQuery': query,
                'pageSize': 20,  # Max per page
                'maxResultCount': 60,  # Maximum total results across all pages
                'languageCode': 'en'
            }
            
            # Add location bias if provided
            if location_bias:
                body['locationBias'] = location_bias
            
            results = []
            next_page_token = None
            page_count = 0
            
            # Get all pages (up to 60 results total - 3 pages of 20 each)
            while len(results) < MAX_RESULTS_PER_LOCATION and page_count < 3:
                if next_page_token:
                    # For pagination, keep all params same except add pageToken
                    body['pageToken'] = next_page_token
                    time.sleep(2)  # Required delay for pagination
                
                logger.info(f"Requesting page {page_count + 1} for query: {query}")
                response = requests.post(
                    self.text_search_url,
                    headers=headers,
                    json=body
                )
                
                if response.status_code == 200:
                    data = response.json()
                    places = data.get('places', [])
                    results.extend(places)
                    logger.info(f"Page {page_count + 1}: Found {len(places)} places, total so far: {len(results)}")
                    
                    # Check for nextPageToken
                    next_page_token = data.get('nextPageToken')
                    if next_page_token:
                        logger.info(f"Next page token available: {next_page_token[:20]}...")
                    else:
                        logger.info("No nextPageToken in response")
                    
                    page_count += 1
                    
                    if not next_page_token or not places:
                        logger.info(f"No more pages available. Total results: {len(results)}")
                        break
                else:
                    logger.error(f"Text search failed: {response.status_code} - {response.text}")
                    if response.status_code == 403:
                        logger.error("API key may be invalid or Places API not enabled")
                    break
            
            logger.info(f"Text search completed. Total results: {len(results)} from {page_count} pages")
            
            # Track API usage
            try:
                from ..database.postgres_client import execute_query
                execute_query("""
                    INSERT INTO api_calls (api_type, endpoint, request_count, response_count, keyword)
                    VALUES ('text_search', 'places:searchText', %s, %s, %s)
                """, (page_count, len(results), query[:255]))
            except Exception as e:
                logger.error(f"Failed to track API call: {e}")
            
            return results[:MAX_RESULTS_PER_LOCATION]
            
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []
    
    def search_businesses_on_road(
        self,
        road_name: str,
        city_name: str,
        state_code: str,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        tier: str = 'enterprise',
        business_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Specialized method to search businesses on a specific road
        Optimization strategies:
        1. Use 'enterprise' to get ALL fields in one request (same cost)
        2. Use 'enterprise_minimal' for initial discovery
        3. Filter by business_type to reduce irrelevant results
        """
        # Build optimized query
        if business_type:
            query = f"{business_type} on {road_name}, {city_name}, {state_code}"
        else:
            query = f"businesses on {road_name}, {city_name}, {state_code}"
        
        # Add location bias if coordinates provided
        location_bias = None
        if center_lat and center_lng:
            location_bias = {
                "circle": {
                    "center": {
                        "latitude": center_lat,
                        "longitude": center_lng
                    },
                    "radius": 5000  # 5km radius along road for more results
                }
            }
        
        return self.search_text(query, location_bias, tier)
    
    def get_place_details(self, place_id: str, tier: str = 'enterprise') -> Optional[Dict]:
        """
        Get place details using new API
        Note: With enterprise tier, most details are already in search results
        """
        if not self.api_key:
            return None
            
        try:
            # New API uses place resource name
            if not place_id.startswith('places/'):
                place_id = f"places/{place_id}"
            
            headers = {
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': self.field_masks.get(tier, self.field_masks['enterprise'])
            }
            
            response = requests.get(
                f"{self.place_details_url}/{place_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Place details failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return None
    
    def parse_business(self, place_data: Dict, road_osm_id: int, road_name: str = None) -> Business:
        """Parse new API place data into Business model"""
        
        # Extract location
        location = place_data.get('location', {})
        lat = location.get('latitude', 0)
        lng = location.get('longitude', 0)
        
        # Extract place ID (remove 'places/' prefix if present)
        place_id = place_data.get('id', '')
        if place_id.startswith('places/'):
            place_id = place_id[7:]
        
        # Parse opening hours if available
        opening_hours = None
        current_hours = place_data.get('currentOpeningHours', {})
        regular_hours = place_data.get('regularOpeningHours', {})
        
        # Prefer current hours, fallback to regular
        hours_data = current_hours or regular_hours
        if hours_data:
            opening_hours = {
                'open_now': hours_data.get('openNow'),
                'weekday_text': hours_data.get('weekdayDescriptions', []),
                'periods': hours_data.get('periods', [])
            }
        
        # Extract price info and convert to numeric
        price_level_str = place_data.get('priceLevel')
        price_level = None
        if price_level_str:
            # Convert Google's price level strings to numeric
            price_level_map = {
                'PRICE_LEVEL_FREE': 0,
                'PRICE_LEVEL_INEXPENSIVE': 1,
                'PRICE_LEVEL_MODERATE': 2,
                'PRICE_LEVEL_EXPENSIVE': 3,
                'PRICE_LEVEL_VERY_EXPENSIVE': 4
            }
            price_level = price_level_map.get(price_level_str)
        
        # If no price level, try to infer from price range
        if price_level is None:
            price_range = place_data.get('priceRange', {})
            if price_range:
                # Count dollar signs in price range
                price_text = price_range.get('startPrice', {}).get('text', '')
                price_level = min(len([c for c in price_text if c == '$']), 4)
        
        # Map new API fields to Business model
        return Business(
            place_id=place_id,
            name=place_data.get('displayName', {}).get('text', ''),
            formatted_address=place_data.get('formattedAddress', ''),
            lat=lat,
            lng=lng,
            types=place_data.get('types', []),
            rating=place_data.get('rating'),
            user_ratings_total=place_data.get('userRatingCount'),
            price_level=price_level,
            phone_number=place_data.get('nationalPhoneNumber') or place_data.get('internationalPhoneNumber'),
            website=place_data.get('websiteUri'),
            opening_hours=opening_hours,
            road_osm_id=road_osm_id,
            road_name=road_name,
            distance_to_road=0,  # TODO: Calculate actual distance
            crawled_at=datetime.utcnow()
        )
    
    # Legacy method compatibility
    def search_nearby_places(
        self, 
        location: Tuple[float, float], 
        place_type: Optional[str] = None,
        radius: int = 500
    ) -> List[Dict]:
        """
        Compatibility wrapper - converts to text search
        Consider using search_businesses_on_road() instead
        """
        lat, lng = location
        query = "businesses"
        if place_type:
            query = f"{place_type} businesses"
            
        location_bias = {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": radius
            }
        }
        
        return self.search_text(query, location_bias)
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode address using new API"""
        if not self.api_key:
            return None
            
        try:
            # Use text search to geocode
            results = self.search_text(address, tier='basic')
            if results:
                location = results[0].get('location', {})
                return (location.get('latitude'), location.get('longitude'))
            return None
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None