from django.urls import path
from .views import CurrentWeatherView, ForecastWeatherView, HealthCheckView

urlpatterns = [
    path('current/', CurrentWeatherView.as_view(), name='current-weather'),
    path('forecast/', ForecastWeatherView.as_view(), name='forecast-weather'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]