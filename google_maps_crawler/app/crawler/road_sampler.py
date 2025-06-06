"""
Sample points along roads for crawling
"""
from typing import List, Tuple
import logging
from geopy.distance import distance
from shapely.geometry import LineString, Point
import random

logger = logging.getLogger(__name__)

class RoadSampler:
    """Generate sample points along a road for searching businesses"""
    
    @staticmethod
    def generate_sample_points_by_name(
        road_name: str, 
        county_fips: str,
        num_points: int = 5
    ) -> List[Tuple[float, float]]:
        """
        Generate sample points along a road based on its name
        For now, this returns dummy coordinates - in production would use:
        - Google Geocoding API to get road coordinates
        - Or PostGIS spatial queries if we had geometry data
        """
        # TODO: Implement actual road geometry sampling
        # For now, return center point of county
        
        # County center coordinates (simplified)
        county_centers = {
            '06037': (34.0522, -118.2437),  # Los Angeles
            '36061': (40.7831, -73.9712),   # Manhattan
            '17031': (41.8781, -87.6298),   # Cook County (Chicago)
            # Add more as needed
        }
        
        center = county_centers.get(county_fips, (39.8283, -98.5795))  # Default to US center
        
        # Generate points in a small radius around center
        points = []
        for i in range(num_points):
            # Random offset within ~1km
            lat_offset = (random.random() - 0.5) * 0.01
            lon_offset = (random.random() - 0.5) * 0.01
            points.append((
                center[0] + lat_offset,
                center[1] + lon_offset
            ))
        
        return points
    
    @staticmethod
    def generate_grid_points(
        bounds: Tuple[float, float, float, float],  # min_lat, min_lon, max_lat, max_lon
        spacing_meters: int = 100
    ) -> List[Tuple[float, float]]:
        """Generate a grid of points within bounds"""
        min_lat, min_lon, max_lat, max_lon = bounds
        points = []
        
        # Calculate approximate degree spacing
        lat_spacing = spacing_meters / 111000  # ~111km per degree latitude
        lon_spacing = spacing_meters / (111000 * abs(cos(radians((min_lat + max_lat) / 2))))
        
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                points.append((lat, lon))
                lon += lon_spacing
            lat += lat_spacing
        
        return points
    
    @staticmethod
    def interpolate_line(
        start: Tuple[float, float],
        end: Tuple[float, float],
        num_points: int = 10
    ) -> List[Tuple[float, float]]:
        """Interpolate points along a line between start and end"""
        points = []
        
        for i in range(num_points):
            ratio = i / (num_points - 1) if num_points > 1 else 0
            lat = start[0] + (end[0] - start[0]) * ratio
            lon = start[1] + (end[1] - start[1]) * ratio
            points.append((lat, lon))
        
        return points