"""
SecurityMiddleware loads configuration from environment variables and applies
security checks on all `/api/` requests, including:
  1. API key validation
  2. Per-IP rate limiting
  3. Maximum payload size enforcement
  4. Basic JSON structure validation (especially for the `/optimize/` endpoint)
"""
import json
import time
import logging
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework import status
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_key = os.getenv('API_KEY')
        self.max_payload_size = int(os.getenv('MAX_PAYLOAD_SIZE', '1048576'))  # 1MB default
        self.rate_limit = int(os.getenv('RATE_LIMIT', '60'))  # 60 requests per minute default
        self.rate_limit_window = 60  # 1 minute window

    def __call__(self, request):
        # Skip security checks for non-API endpoints
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        # 1. Check API Key
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != self.api_key:
            logger.warning(f"Invalid or missing API key from IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse(
                {'error': 'Invalid or missing API key'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Check Rate Limit
        client_ip = request.META.get('REMOTE_ADDR')
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse(
                {'error': 'Rate limit exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # 3. Check Payload Size
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_length = int(request.META.get('CONTENT_LENGTH', 0))
            if content_length > self.max_payload_size:
                logger.warning(f"Payload too large from IP: {client_ip}")
                return JsonResponse(
                    {'error': 'Payload too large'},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )

        # 4. Basic JSON Validation
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body)
                    # Validate required fields for route optimization endpoint
                    if request.path.endswith('/optimize/'):
                        if not self._validate_optimize_payload(body):
                            return JsonResponse(
                                {'error': 'Invalid request payload format'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON payload from IP: {client_ip}")
                return JsonResponse(
                    {'error': 'Invalid JSON payload'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return self.get_response(request)

    def _check_rate_limit(self, client_ip):
        """Check if the client has exceeded the rate limit."""
        cache_key = f'rate_limit_{client_ip}'
        current_time = int(time.time())
        window_start = current_time - self.rate_limit_window

        # Get existing requests in the current window
        requests = cache.get(cache_key, [])
        # Remove requests outside the current window
        requests = [req_time for req_time in requests if req_time > window_start]

        if len(requests) >= self.rate_limit:
            return False

        # Add current request
        requests.append(current_time)
        cache.set(cache_key, requests, self.rate_limit_window)
        return True

    def _validate_optimize_payload(self, payload):
        """Validate the payload for the route optimization endpoint."""
        try:
            # Check required fields
            if not isinstance(payload, dict):
                return False

            # Check start_point
            if 'start_point' not in payload or not isinstance(payload['start_point'], dict):
                return False
            if 'latitude' not in payload['start_point'] or 'longitude' not in payload['start_point']:
                return False
            if not isinstance(payload['start_point']['latitude'], (int, float)) or \
               not isinstance(payload['start_point']['longitude'], (int, float)):
                return False

            # Check end_point
            if 'end_point' not in payload or not isinstance(payload['end_point'], dict):
                return False
            if 'latitude' not in payload['end_point'] or 'longitude' not in payload['end_point']:
                return False
            if not isinstance(payload['end_point']['latitude'], (int, float)) or \
               not isinstance(payload['end_point']['longitude'], (int, float)):
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating optimize payload: {str(e)}")
            return False