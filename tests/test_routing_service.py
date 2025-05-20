import pytest
from route_optimizer.services.routing_service import RoutingService

@pytest.mark.unit
def test_get_route(routing_service, sample_route):
    """Test getting a route between two points."""
    start_point = sample_route['geometry'][0]
    end_point = sample_route['geometry'][-1]

    route = routing_service.get_route(start_point, end_point)

    assert route is not None
    assert 'geometry' in route
    assert 'distance_mi' in route
    assert 'duration_min' in route
    assert len(route['geometry']) > 0
    assert route['distance_mi'] > 0
    assert route['duration_min'] > 0

@pytest.mark.unit
def test_get_distance_between_points(routing_service):
    """Test calculating distance between two points."""
    point1 = (37.7749, -122.4194)  # San Francisco
    point2 = (34.0522, -118.2437)  # Los Angeles

    distance = routing_service.get_distance_between_points(point1, point2)

    assert distance > 0
    assert isinstance(distance, float)

@pytest.mark.integration
def test_route_caching(routing_service):
    """Test that routes are properly cached."""
    start_point = (37.7749, -122.4194)  # San Francisco
    end_point = (34.0522, -118.2437)    # Los Angeles

    # First request
    route1 = routing_service.get_route(start_point, end_point)

    # Second request should use cache
    route2 = routing_service.get_route(start_point, end_point)

    assert route1 == route2  # Routes should be identical