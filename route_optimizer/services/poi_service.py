"""
POIService loads configuration from environment variables and uses a RoutingService to locate gas stations along each route leg.
It computes a bounding box around the leg geometry, generates or queries station data (including names from a CSV),
calculates each station’s distance from the route, filters by a buffer distance, and caches results for fast reuse.
Helper methods handle cache key creation, bounding box calculation, route sampling, and distance computation.
"""

from typing import List, Dict, Tuple
import logging
import os
from dotenv import load_dotenv
from .routing_service import RoutingService
from ..utils.cache_config import CacheManager
import hashlib
import json
import csv
from pathlib import Path

# Load environment variables
load_dotenv()

# Get environment variables
STATION_SEARCH_RADIUS = int(os.getenv('STATION_SEARCH_RADIUS', '5000'))
BUFFER_DISTANCE = int(os.getenv('BUFFER_DISTANCE', '1000'))
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
FUEL_PRICES_CSV = os.getenv('FUEL_PRICES_CSV', 'data/fuel-prices.csv')

logger = logging.getLogger(__name__)

class POIService:
    def __init__(self, routing_service: RoutingService):
        """
        Initialize the POI service for gas station search.

        Args:
            routing_service: Instance of RoutingService for distance calculations
        """
        self.routing_service = routing_service
        self.search_radius = STATION_SEARCH_RADIUS
        self.buffer_distance = BUFFER_DISTANCE
        self.cache = CacheManager.get_cache('poi')
        self.cache_expire = CACHE_TTL

    def _get_cache_key(self, *args) -> str:
        """Generate a cache key from the arguments."""
        key_str = json.dumps(args, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def find_stations_along_leg(self, leg: Dict) -> List[Dict]:
        """
        Find gas stations along a route leg using a single API call.

        Args:
            leg: Route leg dictionary containing geometry and distance

        Returns:
            List of gas stations, each containing:
                - name: str
                - location: (lat, lon) tuple
                - distance_from_route: float (miles)
                - price: float (to be filled by pricing service)
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key('stations', leg['start_point'], leg['end_point'])
            cached_stations = self.cache.get(cache_key)
            if cached_stations:
                logger.info("Using cached stations")
                return cached_stations

            # Calculate bounding box for the leg
            bbox = self._calculate_bounding_box(leg['geometry'])

            # Search for stations within the bounding box
            stations = self._search_stations_in_bbox(bbox, leg['geometry'])

            # Cache the results
            self.cache.set(cache_key, stations, timeout=self.cache_expire)
            return sorted(stations, key=lambda x: x['distance_from_route'])

        except Exception as e:
            logger.error(f"Error finding stations: {str(e)}")
            raise

    def _calculate_bounding_box(self, geometry: List[Tuple[float, float]]) -> Dict:
        """
        Calculate the bounding box for a route geometry.

        Args:
            geometry: List of (lat, lon) tuples

        Returns:
            Dictionary containing:
                - min_lat: float
                - max_lat: float
                - min_lon: float
                - max_lon: float
        """
        lats = [point[0] for point in geometry]
        lons = [point[1] for point in geometry]

        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons)
        }

    def _search_stations_in_bbox(self, bbox: Dict, route_geometry: List[Tuple[float, float]]) -> List[Dict]:
        """
        Search for gas stations within a bounding box using OpenRouteService.

        Args:
            bbox: Bounding box dictionary
            route_geometry: List of route points for distance calculation

        Returns:
            List of station dictionaries
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key('bbox_stations', bbox)
            cached_stations = self.cache.get(cache_key)
            if cached_stations:
                return cached_stations

            # Load real gas station names from the pricing service's CSV file
            station_names = []
            price_file = Path(FUEL_PRICES_CSV)
            if price_file.exists():
                with open(price_file, 'r') as f:
                    reader = csv.DictReader(f)
                    station_names = [row['Truckstop Name'] for row in reader]

            # Use OpenRouteService to find POIs within bbox
            # Note: This is a placeholder - actual implementation will depend on the API
            # For now, return mock data
            stations = []

            # Generate stations along the route with some variation
            num_stations = 5  # Number of stations to generate
            for i in range(num_stations):
                # Calculate a point along the route
                idx = int(i * (len(route_geometry) - 1) / (num_stations - 1))
                base_point = route_geometry[idx]

                # Add some random variation to create realistic station locations
                import random
                lat_variation = random.uniform(-0.01, 0.01)
                lon_variation = random.uniform(-0.01, 0.01)

                # Use a real gas station name if available, otherwise use a generic name
                station_name = random.choice(station_names) if station_names else f"Gas Station {i+1}"

                station = {
                    'name': station_name,
                    'location': (base_point[0] + lat_variation, base_point[1] + lon_variation),
                    'brand': f"Brand {i+1}",
                    'price': None  # Will be filled by pricing service
                }

                # Calculate distance from route
                station['distance_from_route'] = self._calculate_distance_from_route(
                    station['location'], route_geometry
                )

                # Only include stations within buffer distance
                if station['distance_from_route'] <= self.buffer_distance:
                    stations.append(station)

            # Cache the results
            self.cache.set(cache_key, stations, timeout=self.cache_expire)
            return stations

        except Exception as e:
            logger.error(f"Error searching stations in bbox: {str(e)}")
            raise

    def _calculate_distance_from_route(self,
                                    station_point: Tuple[float, float],
                                    route_geometry: List[Tuple[float, float]]
                                    ) -> float:
        """
        Calculate the minimum distance from a station to the route.

        Args:
            station_point: (lat, lon) tuple of station location
            route_geometry: List of (lat, lon) tuples forming the route

        Returns:
            Minimum distance in miles
        """
        try:
            # Use the route's built-in distance information
            # Sample points from route geometry to reduce calculations
            sampled_points = self._sample_route_points(route_geometry, max_points=5)

            min_distance = float('inf')
            for route_point in sampled_points:
                distance = self.routing_service.get_distance_between_points(
                    station_point, route_point
                )
                min_distance = min(min_distance, distance)
            return min_distance
        except Exception as e:
            logger.error(f"Error calculating distance from route: {str(e)}")
            raise

    def _sample_route_points(self, geometry: List[Tuple[float, float]], max_points: int = 5) -> List[Tuple[float, float]]:
        """
        Sample points along the route to reduce calculations.

        Args:
            geometry: List of route points
            max_points: Maximum number of points to sample

        Returns:
            List of sampled points
        """
        if len(geometry) <= max_points:
            return geometry

        # Calculate step size to get max_points
        step = len(geometry) // max_points
        return [geometry[i] for i in range(0, len(geometry), step)]