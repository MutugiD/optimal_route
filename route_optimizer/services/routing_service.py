"""
RoutingService wraps OpenRouteService API functionality with caching and local distance calculations.
It provides methods to:
  - Fetch and cache routes between two geographic points (returning geometry and distance in miles)
  - Compute point-to-point distances via the Haversine formula
  - Calculate segment distances along a stored route geometry without extra API calls
  - Encode and decode polylines for compact route data exchange
Configuration (API key, profile, cache TTL) is loaded from environment variables.
Call ORS-self.client.directions(...) issues one HTTP request.
Process Response
    Extracts the first feature’s geometry (list of [lon,lat]), converts back to (lat,lon) tuples.
    Reads the route’s total distance (in meters) and converts to miles (÷ 1609.34).
Cache & Return
    Stores the {'geometry':…, 'distance_mi':…} dict with a timestamp for future
Point-to-Point Distance (get_distance_between_points)
    Implements the Haversine formula to compute great-circle distance
Point-to-Point Distance (get_distance_between_points)
"""

import openrouteservice
from openrouteservice import convert
import polyline
from typing import Dict, List, Tuple, Optional
import logging
import os
from dotenv import load_dotenv
from ..utils.cache_config import CacheManager
import hashlib
import json
import math

# Load environment variables
load_dotenv()

# Get environment variables
OPENROUTE_API_KEY = os.getenv('OPENROUTE_API_KEY')
ORS_ROUTE_PROFILE = os.getenv('ORS_ROUTE_PROFILE', 'driving-car')
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def latlon_to_lonlat(coord: Tuple[float, float]) -> List[float]:
    """Convert (lat, lon) to [lon, lat] for OpenRouteService."""
    return [coord[1], coord[0]]

class RoutingService:
    def __init__(self):
        """Initialize the routing service."""
        if not OPENROUTE_API_KEY:
            raise ValueError("OpenRoute API key not found in environment variables")

        self.client = openrouteservice.Client(key=OPENROUTE_API_KEY)
        self.profile = ORS_ROUTE_PROFILE
        self.cache = CacheManager.get_cache('route')
        self.cache_expire = CACHE_TTL

    def _get_cache_key(self, *args) -> str:
        """Generate a cache key from the arguments."""
        key_str = json.dumps(args, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_route(self, start_point: Tuple[float, float], end_point: Tuple[float, float]) -> Dict:
        """
        Get a route between two points.

        Args:
            start_point: (lat, lon) tuple of start location
            end_point: (lat, lon) tuple of end location

        Returns:
            Dictionary containing:
                - geometry: List of (lat, lon) tuples
                - distance_mi: Distance in miles
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key('route', start_point, end_point)
            cached_route = CacheManager.get_with_timestamp('route', cache_key)

            if cached_route:
                logger.info("Using cached route")
                cache_info = CacheManager.get_cache_info('route', cache_key)
                logger.debug(f"Cache age: {cache_info['age_seconds']:.1f} seconds")
                return cached_route

            # Get route from OpenRouteService
            logger.info("Fetching route from OpenRouteService")
            route = self.client.directions(
                coordinates=[latlon_to_lonlat(start_point), latlon_to_lonlat(end_point)],
                profile=self.profile,
                format='geojson'
            )

            # Extract geometry and convert to (lat, lon) tuples
            geometry = [(coord[1], coord[0]) for coord in route['features'][0]['geometry']['coordinates']]

            # Calculate total distance in miles
            distance_mi = route['features'][0]['properties']['segments'][0]['distance'] / 1609.34  # Convert meters to miles

            result = {
                'geometry': geometry,
                'distance_mi': distance_mi
            }

            # Cache the result with timestamp
            CacheManager.set_with_timestamp('route', cache_key, result, self.cache_expire)
            logger.info("Route cached successfully")

            return result

        except Exception as e:
            logger.error(f"Error getting route: {str(e)}")
            raise

    def get_distance_between_points(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calculate the distance between two points using the Haversine formula.

        Args:
            point1: First point (lat, lon)
            point2: Second point (lat, lon)

        Returns:
            Distance in miles
        """
        try:
            # Convert latitude and longitude to radians
            lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
            lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

            # Haversine formula
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = 3959 * c  # Earth's radius in miles

            return distance

        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            raise

    def get_distance_along_route(self, route_geometry: List[Tuple[float, float]], start_idx: int, end_idx: int) -> float:
        """
        Calculate distance along a route between two points using the route geometry.
        This avoids making API calls by using the route's built-in distance information.

        Args:
            route_geometry: List of (lat, lon) tuples forming the route
            start_idx: Index of start point
            end_idx: Index of end point

        Returns:
            Distance in miles
        """
        try:
            total_distance = 0
            for i in range(start_idx, end_idx):
                total_distance += self.get_distance_between_points(
                    route_geometry[i],
                    route_geometry[i + 1]
                )
            return total_distance

        except Exception as e:
            logger.error(f"Error calculating route distance: {str(e)}")
            raise

    def decode_polyline(self, encoded_polyline: str) -> List[Tuple[float, float]]:
        """
        Decode a polyline string into a list of coordinates.

        Args:
            encoded_polyline: Encoded polyline string

        Returns:
            List of (latitude, longitude) tuples
        """
        return polyline.decode(encoded_polyline)

    def encode_polyline(self, coordinates: List[Tuple[float, float]]) -> str:
        """
        Encode a list of coordinates into a polyline string.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            Encoded polyline string
        """
        return polyline.encode(coordinates)