"""
PricingService loads and caches fuel prices from a CSV file, then applies those prices to a
list of station dicts—using the exact match by station name or falling back to the average price
when missing.
"""
import logging
import os
from dotenv import load_dotenv
from ..utils.cache_config import CacheManager
import csv
from pathlib import Path

# Load environment variables
load_dotenv()

# Get environment variables
FUEL_PRICES_CSV = os.getenv('FUEL_PRICES_CSV', 'data/fuel-prices.csv')

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        """Initialize the pricing service."""
        self.cache = CacheManager.get_cache('price')
        self.price_file = Path(FUEL_PRICES_CSV)

    def update_station_prices(self, stations: list) -> list:
        """
        Update station prices from the pricing data.

        Args:
            stations: List of station dictionaries

        Returns:
            Updated list of stations with prices
        """
        try:
            # Load prices from CSV
            prices = self._load_prices()

            # Update station prices
            for station in stations:
                station_name = station['name']
                if station_name in prices:
                    station['price'] = prices[station_name]
                else:
                    # Use average price if station not found
                    station['price'] = sum(prices.values()) / len(prices)

            return stations

        except Exception as e:
            logger.error(f"Error updating station prices: {str(e)}")
            raise

    def _load_prices(self) -> dict:
        """
        Load fuel prices from CSV file.

        Returns:
            Dictionary mapping station names to prices
        """
        try:
            # Check cache first
            cache_key = 'fuel_prices'
            cached_prices = self.cache.get(cache_key)
            if cached_prices:
                logger.info("Using cached prices")
                return cached_prices

            if not self.price_file.exists():
                raise FileNotFoundError(f"Price file not found: {self.price_file}")

            prices = {}
            with open(self.price_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    prices[row['Truckstop Name']] = float(row['Retail Price'])

            # Cache the prices
            self.cache.set(cache_key, prices)
            return prices

        except Exception as e:
            logger.error(f"Error loading prices: {str(e)}")
            raise