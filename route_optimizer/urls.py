from django.urls import path
from .views import RouteOptimizationView

app_name = 'route_optimizer'

urlpatterns = [
    path('optimize/', RouteOptimizationView.as_view(), name='optimize_route'),
]