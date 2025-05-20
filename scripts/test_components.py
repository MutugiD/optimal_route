import os
import sys
import django
import logging
from pathlib import Path
import json
from datetime import datetime

# Set up Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'optimal_api.settings')
django.setup()

# Import required services and utilities
from route_optimizer.services.routing_service import RoutingService
from route_optimizer.utils.cache_config import CacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_cache_info(cache_info):
    """Format cache info for logging."""
    if cache_info:
        return {
            'timestamp': cache_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'age_seconds': round(cache_info['age_seconds'], 2)
        }
    return None

def test_routing_service():
    """Test the routing service with caching."""
    try:
        # Clear all caches before testing
        CacheManager.clear_all_caches()
        logger.info("Cleared all caches")

        # Initialize routing service
        routing_service = RoutingService()
        logger.info("Initialized routing service")

        # Test coordinates
        start_point = (37.7749, -122.4194)  # San Francisco
        end_point = (34.0522, -118.2437)    # Los Angeles

        # First request - should hit the API
        logger.info("Making first request...")
        route1 = routing_service.get_route(start_point, end_point)
        logger.info(f"First request successful. Distance: {route1['distance_mi']:.2f} miles")

        # Get cache info after first request
        cache_key = routing_service._get_cache_key('route', start_point, end_point)
        cache_info = CacheManager.get_cache_info('route', cache_key)
        logger.info(f"Cache info after first request: {json.dumps(format_cache_info(cache_info), indent=2)}")

        # Second request - should use cache
        logger.info("Making second request...")
        route2 = routing_service.get_route(start_point, end_point)
        logger.info(f"Second request successful. Distance: {route2['distance_mi']:.2f} miles")

        # Verify cache was used
        cache_info = CacheManager.get_cache_info('route', cache_key)
        logger.info(f"Cache info after second request: {json.dumps(format_cache_info(cache_info), indent=2)}")

        if cache_info and cache_info['age_seconds'] > 0:
            logger.info("Cache verification successful - second request used cached data")
        else:
            logger.error("Cache verification failed - second request did not use cached data")

        # Verify routes are identical
        assert route1 == route2, "Routes from first and second requests should be identical"
        logger.info("Route comparison successful - routes are identical")

        return True

    except Exception as e:
        logger.error(f"Error testing routing service: {str(e)}")
        return False

def test_poi_service(route, routing_service):
    """Test the POI service."""
    from route_optimizer.services.poi_service import POIService

    logger.info("\nTesting POI Service...")
    try:
        poi_service = POIService(routing_service)

        # Create a test leg
        test_leg = {
            'geometry': route['geometry'],
            'distance_mi': route['distance_mi'],
            'start_point': route['geometry'][0],
            'end_point': route['geometry'][-1]
        }

        # Find stations
        stations = poi_service.find_stations_along_leg(test_leg)
        logger.info(f"✓ Found {len(stations)} stations")

        # Print first 3 stations
        for i, station in enumerate(stations[:3], 1):
            logger.info(f"\nStation {i}:")
            logger.info(f"  Name: {station['name']}")
            logger.info(f"  Location: {station['location']}")
            logger.info(f"  Distance from route: {station.get('distance_from_route', 'N/A')} miles")

        return stations

    except Exception as e:
        logger.error(f"✗ POI Service test failed: {str(e)}")
        raise

def test_pricing_service(stations):
    """Test the pricing service."""
    from route_optimizer.services.pricing_service import PricingService

    logger.info("\nTesting Pricing Service...")
    try:
        pricing_service = PricingService()

        # Update station prices
        stations_with_prices = pricing_service.update_station_prices(stations)
        logger.info(f"✓ Updated prices for {len(stations_with_prices)} stations")

        # Print first 3 stations with prices
        for i, station in enumerate(stations_with_prices[:3], 1):
            logger.info(f"\nStation {i}:")
            logger.info(f"  Name: {station['name']}")
            logger.info(f"  Price: ${station.get('price', 'N/A')}/gallon")

        return stations_with_prices

    except Exception as e:
        logger.error(f"✗ Pricing Service test failed: {str(e)}")
        raise

def test_segmentation_service(routing_service, route):
    """Test the segmentation service."""
    from route_optimizer.services.segmentation_service import SegmentationService

    logger.info("\nTesting Segmentation Service...")
    try:
        segmentation_service = SegmentationService(routing_service)
        legs = segmentation_service.split_route(route)
        logger.info(f"✓ Route split into {len(legs)} legs")
        for i, leg in enumerate(legs):
            logger.info(f"  Leg {i+1}: {leg['distance_mi']:.2f} miles")
        return legs
    except Exception as e:
        logger.error(f"✗ Segmentation Service test failed: {str(e)}")
        raise

def test_optimization_service(pricing_service, legs, poi_service):
    """Test the optimization service."""
    from route_optimizer.services.optimization_service import OptimizationService

    logger.info("\nTesting Optimization Service...")
    try:
        optimization_service = OptimizationService(pricing_service)
        total_cost = 0

        for i, leg in enumerate(legs):
            leg_stations = poi_service.find_stations_along_leg(leg)
            optimized_stops = optimization_service.optimize_stops(leg['distance_mi'], leg_stations)

            logger.info(f"  Leg {i+1} optimized stops:")
            for stop in optimized_stops:
                logger.info(f"    Station: {stop['station']['name']}")
                logger.info(f"      Fuel: {stop['fuel_amount']:.2f} gallons")
                logger.info(f"      Cost: ${stop['cost']:.2f}")
                total_cost += stop['cost']

        logger.info(f"✓ Total optimization cost: ${total_cost:.2f}")
    except Exception as e:
        logger.error(f"✗ Optimization Service test failed: {str(e)}")
        raise

def main():
    """Run all component tests."""
    try:
        # Test routing service
        routing_service = RoutingService()
        start_point = (37.7749, -122.4194)  # San Francisco
        end_point = (34.0522, -118.2437)    # Los Angeles

        # Get route for testing other services
        route = routing_service.get_route(start_point, end_point)

        # Run routing service tests
        if not test_routing_service():
            logger.error("\n✗ Test suite failed: Routing service test failed")
            sys.exit(1)

        # Test POI service
        logger.info("\nTesting POI Service...")
        poi_service = __import__('route_optimizer.services.poi_service', fromlist=['POIService']).POIService(routing_service)
        stations = test_poi_service(route, routing_service)

        # Test pricing service
        pricing_service = __import__('route_optimizer.services.pricing_service', fromlist=['PricingService']).PricingService()
        stations_with_prices = test_pricing_service(stations)

        # Test segmentation service
        legs = test_segmentation_service(routing_service, route)

        # Test optimization service
        test_optimization_service(pricing_service, legs, poi_service)

        logger.info("\n✓ All tests completed successfully!")

    except Exception as e:
        logger.error(f"\n✗ Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()