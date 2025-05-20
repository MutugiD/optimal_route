"""
RouteOptimizer ties together routing, segmentation, POI lookup, pricing, and optimization to produce a complete
trip plan with fuel stops. On each run it:
  1. Retrieves and caches the full driving route between start and end points
  2. Splits the route into legs based on the vehicle’s maximum range
  3. Finds nearby gas stations along each leg
  4. Updates station prices from CSV data
  5. Determines the most cost-effective stop for each leg
  6. Aggregates the route, leg details, fuel stops, total cost, and performance metrics into the final output
All behavior is driven by environment-loaded configuration (API keys, range, MPG, cache settings, etc.).
"""

import logging
import time
from typing import Dict, Tuple
import os
from dotenv import load_dotenv
from .services.routing_service import RoutingService
from .services.segmentation_service import SegmentationService
from .services.poi_service import POIService
from .services.pricing_service import PricingService
from .services.optimization_service import OptimizationService

# Load environment variables
load_dotenv()

# Get environment variables
OPENROUTE_API_KEY = os.getenv('OPENROUTE_API_KEY')
ORS_ROUTE_PROFILE = os.getenv('ORS_ROUTE_PROFILE', 'driving-car')
MAX_RANGE_MILES = int(os.getenv('MAX_RANGE_MILES', '500'))
FUEL_ECONOMY_MPG = int(os.getenv('FUEL_ECONOMY_MPG', '10'))
STATION_SEARCH_RADIUS = int(os.getenv('STATION_SEARCH_RADIUS', '5000'))
BUFFER_DISTANCE = int(os.getenv('BUFFER_DISTANCE', '1000'))
CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
FUEL_PRICES_CSV = os.getenv('FUEL_PRICES_CSV', 'data/fuel-prices.csv')

# Error messages
ERROR_MESSAGES = {
    'no_api_key': 'OpenRoute API key not found. Please set OPENROUTE_API_KEY in .env file',
    'no_route': 'Could not find a valid route between the given points',
    'no_stations': 'No gas stations found along the route',
    'no_prices': 'No fuel prices available for stations along the route',
    'optimization_failed': 'Failed to find optimal fuel stops for the route'
}

logger = logging.getLogger(__name__)

class RouteOptimizer:
    def __init__(self):
        """Initialize the route optimizer with all required services."""
        if not OPENROUTE_API_KEY:
            raise ValueError(ERROR_MESSAGES['no_api_key'])

        self.routing_service = RoutingService()
        self.segmentation_service = SegmentationService(self.routing_service)
        self.poi_service = POIService(self.routing_service)
        self.pricing_service = PricingService()
        self.optimization_service = OptimizationService(self.pricing_service)

    def optimize_route(self, start_point: tuple, end_point: tuple) -> dict:
        """
        Optimize a route with fuel stops.

        Args:
            start_point: (lat, lon) tuple of start location
            end_point: (lat, lon) tuple of end location

        Returns:
            Dictionary containing:
                - route: Full route information
                - legs: List of route legs
                - optimized_stops: List of optimized fuel stops
                - total_cost: Total fuel cost
                - performance_metrics: Timing and statistics
        """
        start_time = time.time()
        performance_metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'legs_processed': 0,
            'stations_found': 0
        }

        try:
            # Get full route
            logger.info(f"Getting route from {start_point} to {end_point}")
            route = self.routing_service.get_route(start_point, end_point)
            performance_metrics['api_calls'] += 1

            # Split into legs
            logger.info("Splitting route into legs")
            legs = self.segmentation_service.split_route(route)
            performance_metrics['legs_processed'] = len(legs)
            logger.info(f"Route split into {len(legs)} legs")

            # Find stations and optimize stops
            optimized_stops = []
            total_cost = 0

            for i, leg in enumerate(legs, 1):
                logger.info(f"Processing leg {i}/{len(legs)}")

                # Find stations along leg
                stations = self.poi_service.find_stations_along_leg(leg)
                performance_metrics['stations_found'] += len(stations)
                logger.info(f"Found {len(stations)} stations along leg {i}")

                # Optimize stops for this leg
                leg_stops = self.optimization_service.optimize_stops(
                    leg['distance_mi'],
                    stations
                )
                optimized_stops.extend(leg_stops)
                total_cost += sum(stop['cost'] for stop in leg_stops)

            # Calculate total time
            total_time = time.time() - start_time
            performance_metrics['total_time_seconds'] = round(total_time, 2)

            # Prepare the output
            output = {
                'route': {
                    'start': start_point,
                    'end': end_point,
                    'total_distance_miles': round(route['distance_mi'], 1)
                },
                'legs': [{
                    'leg_number': i + 1,
                    'start': leg['start_point'],
                    'end': leg['end_point'],
                    'distance_miles': round(leg['distance_mi'], 1)
                } for i, leg in enumerate(legs)],
                'fuel_stops': [{
                    'stop_number': i + 1,
                    'station': {
                        'name': stop['station']['name'],
                        'location': stop['station']['location'],
                        'price_per_gallon': stop['station']['price']
                    },
                    'fuel_amount_gallons': stop['fuel_amount'],
                    'cost': stop['cost']
                } for i, stop in enumerate(optimized_stops)],
                'summary': {
                    'total_distance_miles': round(route['distance_mi'], 1),
                    'number_of_legs': len(legs),
                    'number_of_stops': len(optimized_stops),
                    'total_fuel_cost': round(total_cost, 2)
                },
                'performance_metrics': performance_metrics
            }

            return output

        except Exception as e:
            logger.error(f"Error optimizing route: {str(e)}")
            raise