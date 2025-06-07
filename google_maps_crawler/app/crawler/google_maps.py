"""
Google Maps API wrapper
"""
import googlemaps
from typing import List, Dict, Optional, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import GOOGLE_MAPS_API_KEY, MAX_RESULTS_PER_LOCATION, SEARCH_RADIUS_METERS
from ..models import Business
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleMapsClient:
    def __init__(self):
        if GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY != 'your_google_maps_api_key_here':
            self.client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        else:
            self.client = None
            logger.warning("Google Maps API key not configured - crawling disabled")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_nearby_places(
        self, 
        location: Tuple[float, float], 
        place_type: Optional[str] = None,
        radius: int = SEARCH_RADIUS_METERS
    ) -> List[Dict]:
        """Search for places near a location"""
        if not self.client:
            logger.warning("Google Maps client not initialized")
            return []
            
        try:
            results = []
            
            # Search parameters
            params = {
                'location': location,
                'radius': radius,
                'language': 'en'
            }
            
            if place_type:
                params['type'] = place_type
            
            # Initial search
            response = self.client.places_nearby(**params)
            results.extend(response.get('results', []))
            
            # Get additional pages if available
            while 'next_page_token' in response and len(results) < MAX_RESULTS_PER_LOCATION:
                import time
                time.sleep(2)  # Required delay for next_page_token
                response = self.client.places_nearby(page_token=response['next_page_token'])
                results.extend(response.get('results', []))
            
            return results[:MAX_RESULTS_PER_LOCATION]
            
        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        try:
            fields = [
                'name', 'formatted_address', 'geometry',
                'rating', 'user_ratings_total', 'price_level',
                'formatted_phone_number', 'website', 'opening_hours',
                'types'
            ]
            
            result = self.client.place(
                place_id=place_id,
                fields=fields,
                language='en'
            )
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates"""
        try:
            results = self.client.geocode(address)
            if results:
                location = results[0]['geometry']['location']
                return (location['lat'], location['lng'])
            return None
        except Exception as e:
            logger.error(f"Error geocoding address: {e}")
            return None
    
    def parse_business(self, place_data: Dict, road_osm_id: int, road_name: str = None) -> Business:
        """Parse Google Maps place data into Business model"""
        
        # Get location
        location = place_data.get('geometry', {}).get('location', {})
        lat = location.get('lat', 0)
        lng = location.get('lng', 0)
        
        # Parse opening hours if available
        opening_hours = None
        if 'opening_hours' in place_data:
            opening_hours = {
                'open_now': place_data['opening_hours'].get('open_now'),
                'weekday_text': place_data['opening_hours'].get('weekday_text', [])
            }
        
        return Business(
            place_id=place_data['place_id'],
            name=place_data['name'],
            formatted_address=place_data.get('formatted_address'),
            lat=lat,
            lng=lng,
            types=place_data.get('types', []),
            rating=place_data.get('rating'),
            user_ratings_total=place_data.get('user_ratings_total'),
            price_level=place_data.get('price_level'),
            phone_number=place_data.get('formatted_phone_number'),
            website=place_data.get('website'),
            opening_hours=opening_hours,
            road_osm_id=road_osm_id,
            road_name=road_name,
            distance_to_road=0,  # TODO: Calculate actual distance
            crawled_at=datetime.utcnow()
        )