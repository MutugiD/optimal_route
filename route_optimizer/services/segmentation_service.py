"""
SegmentationService divides a full route into manageable legs based on a maximum driving range.
It uses RoutingService-calculated distances to:
  - Return the entire route as one leg if it’s within range
  - Otherwise, approximate equal-length segments by splitting the route geometry
  - Estimate inter-point distances proportionally to avoid extra API calls
  - Validate that each leg does not exceed the configured maximum range
Configuration (max range) is loaded from environment variables.
"""

from typing import List, Dict
import logging
import os
from dotenv import load_dotenv
from .routing_service import RoutingService

# Load environment variables
load_dotenv()

# Get environment variables
MAX_RANGE_MILES = int(os.getenv('MAX_RANGE_MILES', '500'))

logger = logging.getLogger(__name__)

class SegmentationService:
    def __init__(self, routing_service: RoutingService):
        """
        Initialize the segmentation service.

        Args:
            routing_service: Instance of RoutingService for distance calculations
        """
        self.routing_service = routing_service
        self.max_range = MAX_RANGE_MILES

    def split_route(self, route: Dict) -> List[Dict]:
        """
        Split a route into legs of maximum range.

        Args:
            route: Route dictionary containing geometry and distance

        Returns:
            List of route legs, each containing:
                - geometry: List of coordinates
                - distance_mi: Distance in miles
                - start_point: (lat, lon) tuple
                - end_point: (lat, lon) tuple
        """
        try:
            geometry = route['geometry']
            total_distance = route['distance_mi']

            # If total distance is within range, return single leg
            if total_distance <= self.max_range:
                return [{
                    'geometry': geometry,
                    'distance_mi': total_distance,
                    'start_point': geometry[0],
                    'end_point': geometry[-1]
                }]

            # Calculate number of legs needed
            num_legs = int(total_distance / self.max_range) + 1
            leg_distance = total_distance / num_legs

            legs = []
            current_leg = []
            current_distance = 0
            last_point = None

            for point in geometry:
                if last_point is None:
                    current_leg.append(point)
                    last_point = point
                    continue

                # Calculate distance between points
                point_distance = self._calculate_point_distance(last_point, point, total_distance, len(geometry))
                current_distance += point_distance

                if current_distance <= leg_distance:
                    current_leg.append(point)
                else:
                    # Create new leg
                    legs.append({
                        'geometry': current_leg,
                        'distance_mi': current_distance,
                        'start_point': current_leg[0],
                        'end_point': current_leg[-1]
                    })
                    current_leg = [point]
                    current_distance = 0

                last_point = point

            # Add the last leg if it has points
            if current_leg:
                legs.append({
                    'geometry': current_leg,
                    'distance_mi': current_distance,
                    'start_point': current_leg[0],
                    'end_point': current_leg[-1]
                })

            return legs

        except Exception as e:
            logger.error(f"Error splitting route: {str(e)}")
            raise

    def _calculate_point_distance(self, point1: tuple, point2: tuple, total_distance: float, num_points: int) -> float:
        """
        Calculate the distance between two points using proportional distance.

        Args:
            point1: First point (lat, lon)
            point2: Second point (lat, lon)
            total_distance: Total route distance in miles
            num_points: Total number of points in the route

        Returns:
            Distance in miles
        """
        try:
            # Calculate average distance per point
            avg_distance = total_distance / (num_points - 1)

            # Use the average distance as an approximation
            # This avoids making API calls while maintaining reasonable accuracy
            return avg_distance

        except Exception as e:
            logger.error(f"Error calculating point distance: {str(e)}")
            raise

    def validate_legs(self, legs: List[Dict]) -> bool:
        """
        Validate that all legs are within maximum range.

        Args:
            legs: List of route legs

        Returns:
            True if all legs are valid, False otherwise
        """
        try:
            for i, leg in enumerate(legs):
                if leg['distance_mi'] > self.max_range:
                    logger.warning(f"Leg {i} exceeds maximum range: {leg['distance_mi']:.2f} miles")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating legs: {str(e)}")
            raise