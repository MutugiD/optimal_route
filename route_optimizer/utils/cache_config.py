import os
import logging
from django.core.cache import cache
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))

class CacheManager:
    _caches = {}

    @classmethod
    def get_cache(cls, cache_name):
        """Get or create a cache instance."""
        if cache_name not in cls._caches:
            cls._caches[cache_name] = cache
        return cls._caches[cache_name]

    @classmethod
    def clear_all_caches(cls):
        """Clear all caches."""
        for cache_instance in cls._caches.values():
            cache_instance.clear()
        logger.info("All caches cleared")

    @classmethod
    def set_with_timestamp(cls, cache_name, key, value, timeout=None):
        """Set a cache value with timestamp."""
        cache_data = {
            'data': value,
            'timestamp': datetime.now().timestamp()
        }
        cls.get_cache(cache_name).set(key, cache_data, timeout=timeout)
        logger.debug(f"Cache set: {cache_name}:{key}")

    @classmethod
    def get_with_timestamp(cls, cache_name, key):
        """Get a cache value with timestamp."""
        cache_data = cls.get_cache(cache_name).get(key)
        if cache_data:
            logger.debug(f"Cache hit: {cache_name}:{key}")
            return cache_data['data']
        logger.debug(f"Cache miss: {cache_name}:{key}")
        return None

    @classmethod
    def get_cache_info(cls, cache_name, key):
        """Get cache information including timestamp."""
        cache_data = cls.get_cache(cache_name).get(key)
        if cache_data:
            return {
                'timestamp': datetime.fromtimestamp(cache_data['timestamp']),
                'age_seconds': datetime.now().timestamp() - cache_data['timestamp']
            }
        return None