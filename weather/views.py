from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.cache import cache
import requests
import logging

logger = logging.getLogger(__name__)


class CurrentWeatherView(APIView):
    """
    Get current weather for a city
    GET /api/weather/current/?city=London
    """
    
    def get(self, request):
        city = request.query_params.get('city', '').strip()
        
        if not city:
            return Response({
                'success': False,
                'message': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check cache first
        cache_key = f'weather_current_{city.lower()}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached weather data for {city}")
            return Response(cached_data, status=status.HTTP_200_OK)
        
        try:
            # Call OpenWeatherMap API
            url = f"{settings.WEATHER_API_BASE_URL}/weather"
            params = {
                'q': city,
                'appid': settings.WEATHER_API_KEY,
                'units': 'metric'
            }
            
            logger.info(f"Fetching weather data for {city}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format response
                weather_data = {
                    'success': True,
                    'city': data['name'],
                    'country': data['sys']['country'],
                    'coordinates': {
                        'lat': data['coord']['lat'],
                        'lon': data['coord']['lon'],
                    },
                    'temperature': round(data['main']['temp']),
                    'feels_like': round(data['main']['feels_like']),
                    'temp_min': round(data['main']['temp_min']),
                    'temp_max': round(data['main']['temp_max']),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'description': data['weather'][0]['description'].title(),
                    'main': data['weather'][0]['main'],
                    'icon': data['weather'][0]['icon'],
                    'wind_speed': round(data['wind']['speed'], 1),
                    'wind_deg': data['wind'].get('deg', 0),
                    'clouds': data['clouds']['all'],
                    'visibility': data.get('visibility', 0),
                    'sunrise': data['sys']['sunrise'],
                    'sunset': data['sys']['sunset'],
                    'timezone': data['timezone'],
                    'timestamp': data['dt'],
                }
                
                # Cache the data for 30 minutes
                cache.set(cache_key, weather_data, timeout=1800)
                
                logger.info(f"Successfully fetched weather for {city}")
                return Response(weather_data, status=status.HTTP_200_OK)
            
            elif response.status_code == 404:
                return Response({
                    'success': False,
                    'message': f'City "{city}" not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            else:
                logger.error(f"Weather API error: {response.status_code}")
                return Response({
                    'success': False,
                    'message': 'Failed to fetch weather data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching weather for {city}")
            return Response({
                'success': False,
                'message': 'Request timeout. Please try again.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return Response({
                'success': False,
                'message': 'Network error. Please check your connection.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForecastWeatherView(APIView):
    """
    Get 5-day weather forecast
    GET /api/weather/forecast/?city=London
    """
    
    def get(self, request):
        city = request.query_params.get('city', '').strip()
        
        if not city:
            return Response({
                'success': False,
                'message': 'City parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check cache first
        cache_key = f'weather_forecast_{city.lower()}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached forecast data for {city}")
            return Response(cached_data, status=status.HTTP_200_OK)
        
        try:
            url = f"{settings.WEATHER_API_BASE_URL}/forecast"
            params = {
                'q': city,
                'appid': settings.WEATHER_API_KEY,
                'units': 'metric',
                'cnt': 40  # 5 days * 8 (3-hour intervals)
            }
            
            logger.info(f"Fetching forecast data for {city}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format forecast data
                forecasts = []
                for item in data['list']:
                    forecasts.append({
                        'datetime': item['dt'],
                        'date_text': item['dt_txt'],
                        'temperature': round(item['main']['temp']),
                        'feels_like': round(item['main']['feels_like']),
                        'temp_min': round(item['main']['temp_min']),
                        'temp_max': round(item['main']['temp_max']),
                        'humidity': item['main']['humidity'],
                        'pressure': item['main']['pressure'],
                        'description': item['weather'][0]['description'].title(),
                        'main': item['weather'][0]['main'],
                        'icon': item['weather'][0]['icon'],
                        'wind_speed': round(item['wind']['speed'], 1),
                        'clouds': item['clouds']['all'],
                        'pop': item.get('pop', 0) * 100,  # Probability of precipitation
                    })
                
                forecast_data = {
                    'success': True,
                    'city': data['city']['name'],
                    'country': data['city']['country'],
                    'coordinates': {
                        'lat': data['city']['coord']['lat'],
                        'lon': data['city']['coord']['lon'],
                    },
                    'forecasts': forecasts
                }
                
                # Cache the data for 30 minutes
                cache.set(cache_key, forecast_data, timeout=1800)
                
                logger.info(f"Successfully fetched forecast for {city}")
                return Response(forecast_data, status=status.HTTP_200_OK)
            
            elif response.status_code == 404:
                return Response({
                    'success': False,
                    'message': f'City "{city}" not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to fetch forecast data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'message': 'Request timeout. Please try again.'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except Exception as e:
            logger.error(f"Forecast error: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthCheckView(APIView):
    """
    Health check endpoint
    GET /api/weather/health/
    """
    
    def get(self, request):
        return Response({
            'success': True,
            'message': 'Weather API is running',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)