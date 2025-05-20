from rest_framework import serializers
from typing import List, Dict, Tuple

class PointSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def to_representation(self, instance):
        if isinstance(instance, tuple):
            return {'latitude': instance[0], 'longitude': instance[1]}
        return instance

    def to_internal_value(self, data):
        if isinstance(data, tuple):
            return data
        return (data['latitude'], data['longitude'])

class StationSerializer(serializers.Serializer):
    name = serializers.CharField()
    location = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    price_per_gallon = serializers.FloatField()

class FuelStopSerializer(serializers.Serializer):
    stop_number = serializers.IntegerField()
    station = StationSerializer()
    fuel_amount_gallons = serializers.FloatField()
    cost = serializers.FloatField()

class RouteLegSerializer(serializers.Serializer):
    leg_number = serializers.IntegerField()
    start = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    end = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    distance_miles = serializers.FloatField()

class RouteSummarySerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    number_of_legs = serializers.IntegerField()
    number_of_stops = serializers.IntegerField()
    total_fuel_cost = serializers.FloatField()

class PerformanceMetricsSerializer(serializers.Serializer):
    api_calls = serializers.IntegerField()
    cache_hits = serializers.IntegerField()
    legs_processed = serializers.IntegerField()
    stations_found = serializers.IntegerField()
    total_time_seconds = serializers.FloatField()

class RouteSerializer(serializers.Serializer):
    start = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    end = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2
    )
    total_distance_miles = serializers.FloatField()

class RouteOptimizationRequestSerializer(serializers.Serializer):
    start_point = PointSerializer()
    end_point = PointSerializer()

class RouteOptimizationResponseSerializer(serializers.Serializer):
    route = RouteSerializer()
    legs = RouteLegSerializer(many=True)
    fuel_stops = FuelStopSerializer(many=True)
    summary = RouteSummarySerializer()
    performance_metrics = PerformanceMetricsSerializer()