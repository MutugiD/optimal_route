"""
OptimizationService uses environment-configured fuel economy to calculate the most cost-effective way to refuel
along a multi-leg route. It delegates price lookups to a PricingService, then for each leg:
  1. Computes gallons needed from distance ÷ MPG
  2. Finds the station with the lowest combined fuel cost plus a small distance penalty
  3. Aggregates total cost, selected stops, and per-leg cost breakdown

Helper methods:
  - _find_optimal_station: scores each candidate station by total cost (fuel + distance penalty)
  - optimize_stops: returns the single cheapest stop for a given leg distance, updating prices via PricingService
"""

import os
import logging
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from .pricing_service import PricingService

logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()

# Get environment variables
FUEL_ECONOMY_MPG = int(os.getenv('FUEL_ECONOMY_MPG', '10'))

class OptimizationService:
    def __init__(self, pricing_service: PricingService):
        """
        Initialize the optimization service.

        Args:
            pricing_service: Instance of PricingService for fuel price data
        """
        self.pricing_service = pricing_service
        self.mpg = FUEL_ECONOMY_MPG

    def optimize_route(self, legs: List[Dict], stations_by_leg: List[List[Dict]]) -> Dict:
        """
        Optimize fuel stops for the entire route.

        Args:
            legs: List of route legs
            stations_by_leg: List of station lists, one per leg

        Returns:
            Dict containing:
                - total_cost: float
                - stops: List of chosen stations
                - cost_breakdown: List of costs per leg
        """
        try:
            total_cost = 0
            chosen_stops = []
            cost_breakdown = []

            for leg_idx, (leg, stations) in enumerate(zip(legs, stations_by_leg)):
                # Calculate fuel needed for this leg
                fuel_needed = leg['distance_mi'] / self.mpg

                # Find optimal station for this leg
                optimal_station = self._find_optimal_station(stations, fuel_needed)

                if optimal_station:
                    leg_cost = fuel_needed * optimal_station['price']
                    total_cost += leg_cost

                    chosen_stops.append({
                        'leg_index': leg_idx,
                        'station': optimal_station,
                        'fuel_needed': fuel_needed,
                        'cost': leg_cost
                    })

                    cost_breakdown.append({
                        'leg_index': leg_idx,
                        'distance': leg['distance_mi'],
                        'fuel_needed': fuel_needed,
                        'station': optimal_station['name'],
                        'price_per_gallon': optimal_station['price'],
                        'cost': leg_cost
                    })
                else:
                    logger.warning(f"No suitable station found for leg {leg_idx}")
                    return None

            return {
                'total_cost': total_cost,
                'stops': chosen_stops,
                'cost_breakdown': cost_breakdown
            }

        except Exception as e:
            logger.error(f"Error optimizing route: {str(e)}")
            raise

    def _find_optimal_station(self, stations: List[Dict], fuel_needed: float) -> Dict:
        """
        Find the optimal station for a leg based on price and distance.

        Args:
            stations: List of available stations
            fuel_needed: Gallons of fuel needed

        Returns:
            Optimal station dictionary
        """
        try:
            if not stations:
                return None

            # Filter out stations without prices
            valid_stations = [s for s in stations if s.get('price') is not None]

            if not valid_stations:
                return None

            # Calculate total cost for each station
            for station in valid_stations:
                station['total_cost'] = (
                    fuel_needed * station['price'] +  # Fuel cost
                    station['distance_from_route'] * 0.1  # Small penalty for distance
                )

            # Return station with lowest total cost
            return min(valid_stations, key=lambda x: x['total_cost'])

        except Exception as e:
            logger.error(f"Error finding optimal station: {str(e)}")
            raise

    def optimize_stops(self, leg_distance: float, stations: List[Dict]) -> List[Dict]:
        """
        Optimize fuel stops for a route leg.

        Args:
            leg_distance: Distance of the leg in miles
            stations: List of available gas stations

        Returns:
            List of optimized fuel stops, each containing:
                - station: Station information
                - fuel_amount: Amount of fuel to purchase
                - cost: Total cost of fuel
        """
        try:
            if not stations:
                logger.warning("No stations available for optimization")
                return []

            # Calculate fuel needed for the leg
            fuel_needed = leg_distance / self.mpg

            # Update station prices
            stations_with_prices = self.pricing_service.update_station_prices(stations)

            # Filter out stations without valid prices
            valid_stations = [s for s in stations_with_prices if s.get('price') is not None]

            if not valid_stations:
                logger.warning("No stations with valid prices found")
                return []

            # Sort stations by price
            sorted_stations = sorted(valid_stations, key=lambda x: x['price'])

            # Select the cheapest station
            best_station = sorted_stations[0]
            price = best_station['price']

            return [{
                'station': best_station,
                'fuel_amount': round(fuel_needed, 2),
                'cost': round(fuel_needed * price, 2)
            }]

        except Exception as e:
            logger.error(f"Error optimizing stops: {str(e)}")
            raise