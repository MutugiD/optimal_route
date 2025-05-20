from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RouteOptimizationRequestSerializer,
    RouteOptimizationResponseSerializer
)
from .optimizer import RouteOptimizer
import logging
import json

logger = logging.getLogger(__name__)

# Create your views here.

class RouteOptimizationView(APIView):
    """
    API endpoint for route optimization.
    """
    def post(self, request, format=None):
        try:
            # Log incoming request
            logger.info(f"Received request data: {json.dumps(request.data, indent=2)}")

            # Validate request data
            serializer = RouteOptimizationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Request validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Extract validated data
            start_point = serializer.validated_data['start_point']
            end_point = serializer.validated_data['end_point']
            logger.info(f"Validated start_point: {start_point}, end_point: {end_point}")

            # Initialize optimizer and get results
            optimizer = RouteOptimizer()
            result = optimizer.optimize_route(start_point, end_point)
            logger.info(f"Optimization result: {json.dumps(result, indent=2)}")

            # Validate and return response
            response_serializer = RouteOptimizationResponseSerializer(data=result)
            if not response_serializer.is_valid():
                logger.error(f"Response validation failed: {response_serializer.errors}")
                return Response(
                    {"error": "Invalid response format", "details": response_serializer.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info("Response serialization successful")
            return Response(response_serializer.validated_data)

        except Exception as e:
            logger.error(f"Error in route optimization: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
