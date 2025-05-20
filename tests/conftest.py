import pytest
from django.conf import settings
from route_optimizer.services.routing_service import RoutingService
from route_optimizer.services.poi_service import POIService
from route_optimizer.services.pricing_service import PricingService
from route_optimizer.services.segmentation_service import SegmentationService
from route_optimizer.services.optimization_service import OptimizationService

@pytest.fixture
def routing_service():
    """Fixture for RoutingService."""
    return RoutingService()

@pytest.fixture
def poi_service(routing_service):
    """Fixture for POIService."""
    return POIService(routing_service)

@pytest.fixture
def pricing_service():
    """Fixture for PricingService."""
    return PricingService()

@pytest.fixture
def segmentation_service(routing_service):
    """Fixture for SegmentationService."""
    return SegmentationService(routing_service)

@pytest.fixture
def optimization_service(pricing_service):
    """Fixture for OptimizationService."""
    return OptimizationService(pricing_service)

@pytest.fixture
def sample_route():
    """Fixture for a sample route."""
    return {
        'geometry': [
            (37.7749, -122.4194),  # San Francisco
            (37.3382, -121.8863),  # San Jose
            (34.0522, -118.2437)   # Los Angeles
        ],
        'distance_mi': 382.0,
        'duration_min': 360
    }

@pytest.fixture
def sample_stations():
    """Fixture for sample gas stations."""
    return [
        {
            'name': 'Test Station 1',
            'location': (37.7749, -122.4194),
            'distance_from_route': 0.5,
            'price': 3.50
        },
        {
            'name': 'Test Station 2',
            'location': (37.3382, -121.8863),
            'distance_from_route': 1.0,
            'price': 3.45
        }
    ]