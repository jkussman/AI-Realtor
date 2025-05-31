"""
Map utilities for handling bounding boxes and coordinate operations.
"""

from typing import Dict, List, Tuple, Any
import math
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon


class MapUtils:
    """
    Utility class for map and geospatial operations.
    """
    
    @staticmethod
    def validate_bounding_box(bbox: Dict[str, float]) -> bool:
        """
        Validate that a bounding box has valid coordinates.
        
        Args:
            bbox: Dictionary with 'north', 'south', 'east', 'west' keys
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['north', 'south', 'east', 'west']
        
        # Check all required keys exist
        if not all(key in bbox for key in required_keys):
            return False
        
        # Check coordinate ranges
        if not (-90 <= bbox['south'] <= 90 and -90 <= bbox['north'] <= 90):
            return False
            
        if not (-180 <= bbox['west'] <= 180 and -180 <= bbox['east'] <= 180):
            return False
        
        # Check that north > south and east > west (for most cases)
        if bbox['north'] <= bbox['south']:
            return False
            
        # Handle date line crossing for longitude
        if bbox['west'] > bbox['east']:
            # This could be valid if crossing the date line, but for NYC it shouldn't happen
            return False
        
        return True
    
    @staticmethod
    def bounding_box_area(bbox: Dict[str, float]) -> float:
        """
        Calculate the area of a bounding box in square kilometers.
        
        Args:
            bbox: Dictionary with 'north', 'south', 'east', 'west' keys
            
        Returns:
            Area in square kilometers
        """
        if not MapUtils.validate_bounding_box(bbox):
            return 0.0
        
        # Calculate distances
        north_west = (bbox['north'], bbox['west'])
        north_east = (bbox['north'], bbox['east'])
        south_west = (bbox['south'], bbox['west'])
        
        # Width and height
        width_km = geodesic(north_west, north_east).kilometers
        height_km = geodesic(north_west, south_west).kilometers
        
        return width_km * height_km
    
    @staticmethod
    def point_in_bounding_box(point: Tuple[float, float], bbox: Dict[str, float]) -> bool:
        """
        Check if a point (lat, lon) is within a bounding box.
        
        Args:
            point: Tuple of (latitude, longitude)
            bbox: Dictionary with 'north', 'south', 'east', 'west' keys
            
        Returns:
            True if point is inside bounding box
        """
        lat, lon = point
        
        return (bbox['south'] <= lat <= bbox['north'] and 
                bbox['west'] <= lon <= bbox['east'])
    
    @staticmethod
    def expand_bounding_box(bbox: Dict[str, float], distance_km: float) -> Dict[str, float]:
        """
        Expand a bounding box by a given distance in kilometers.
        
        Args:
            bbox: Original bounding box
            distance_km: Distance to expand in kilometers
            
        Returns:
            Expanded bounding box
        """
        if not MapUtils.validate_bounding_box(bbox):
            return bbox
        
        # Calculate center point
        center_lat = (bbox['north'] + bbox['south']) / 2
        center_lon = (bbox['east'] + bbox['west']) / 2
        
        # Calculate offset in degrees (approximate)
        # 1 degree latitude ≈ 111 km
        lat_offset = distance_km / 111.0
        
        # 1 degree longitude varies by latitude
        lon_offset = distance_km / (111.0 * math.cos(math.radians(center_lat)))
        
        return {
            'north': bbox['north'] + lat_offset,
            'south': bbox['south'] - lat_offset,
            'east': bbox['east'] + lon_offset,
            'west': bbox['west'] - lon_offset
        }
    
    @staticmethod
    def bounding_boxes_overlap(bbox1: Dict[str, float], bbox2: Dict[str, float]) -> bool:
        """
        Check if two bounding boxes overlap.
        
        Args:
            bbox1: First bounding box
            bbox2: Second bounding box
            
        Returns:
            True if bounding boxes overlap
        """
        # Check if they don't overlap (easier to check)
        if (bbox1['east'] < bbox2['west'] or bbox2['east'] < bbox1['west'] or
            bbox1['north'] < bbox2['south'] or bbox2['north'] < bbox1['south']):
            return False
        
        return True
    
    @staticmethod
    def merge_bounding_boxes(bboxes: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Merge multiple bounding boxes into one that contains all of them.
        
        Args:
            bboxes: List of bounding boxes
            
        Returns:
            Merged bounding box
        """
        if not bboxes:
            return {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        
        # Find extremes
        north = max(bbox['north'] for bbox in bboxes)
        south = min(bbox['south'] for bbox in bboxes)
        east = max(bbox['east'] for bbox in bboxes)
        west = min(bbox['west'] for bbox in bboxes)
        
        return {
            'north': north,
            'south': south,
            'east': east,
            'west': west
        }
    
    @staticmethod
    def bounding_box_to_polygon(bbox: Dict[str, float]) -> Polygon:
        """
        Convert a bounding box to a Shapely Polygon.
        
        Args:
            bbox: Bounding box dictionary
            
        Returns:
            Shapely Polygon object
        """
        coordinates = [
            (bbox['west'], bbox['south']),  # SW
            (bbox['east'], bbox['south']),  # SE
            (bbox['east'], bbox['north']),  # NE
            (bbox['west'], bbox['north']),  # NW
            (bbox['west'], bbox['south'])   # Close polygon
        ]
        
        return Polygon(coordinates)
    
    @staticmethod
    def is_in_nyc_area(bbox: Dict[str, float]) -> bool:
        """
        Check if a bounding box is within the greater NYC area.
        
        Args:
            bbox: Bounding box to check
            
        Returns:
            True if within NYC area
        """
        # NYC rough bounding box
        nyc_bounds = {
            'north': 40.9176,   # Bronx
            'south': 40.4774,   # Staten Island
            'east': -73.7004,   # Eastern Queens
            'west': -74.2591    # Western Staten Island
        }
        
        # Check if the bbox overlaps with NYC bounds
        return MapUtils.bounding_boxes_overlap(bbox, nyc_bounds)
    
    @staticmethod
    def get_neighborhood_from_coordinates(lat: float, lon: float) -> str:
        """
        Get approximate NYC neighborhood from coordinates.
        This is a simplified version - in production, use a proper geocoding service.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Neighborhood name
        """
        # Simplified neighborhood detection based on coordinates
        neighborhoods = [
            {"name": "Manhattan", "bounds": {"north": 40.8176, "south": 40.7489, "east": -73.9441, "west": -74.0479}},
            {"name": "Brooklyn", "bounds": {"north": 40.7394, "south": 40.5755, "east": -73.8333, "west": -74.0479}},
            {"name": "Queens", "bounds": {"north": 40.8026, "south": 40.5755, "east": -73.7004, "west": -73.8333}},
            {"name": "Bronx", "bounds": {"north": 40.9176, "south": 40.7855, "east": -73.7654, "west": -73.9339}},
            {"name": "Staten Island", "bounds": {"north": 40.6514, "south": 40.4774, "east": -74.0479, "west": -74.2591}},
        ]
        
        for neighborhood in neighborhoods:
            bounds = neighborhood["bounds"]
            if (bounds["south"] <= lat <= bounds["north"] and 
                bounds["west"] <= lon <= bounds["east"]):
                return neighborhood["name"]
        
        return "Unknown"
    
    @staticmethod
    def calculate_center(bbox: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculate the center point of a bounding box.
        
        Args:
            bbox: Bounding box dictionary
            
        Returns:
            Tuple of (latitude, longitude) for center point
        """
        center_lat = (bbox['north'] + bbox['south']) / 2
        center_lon = (bbox['east'] + bbox['west']) / 2
        
        return (center_lat, center_lon)
    
    @staticmethod
    def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
        """
        Format coordinates as a string.
        
        Args:
            lat: Latitude
            lon: Longitude
            precision: Number of decimal places
            
        Returns:
            Formatted coordinate string
        """
        return f"{lat:.{precision}f}, {lon:.{precision}f}" 