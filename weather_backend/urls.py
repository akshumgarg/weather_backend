from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Weather API is running',
        'endpoints': {
            'current': '/api/weather/current/?city=London',
            'forecast': '/api/weather/forecast/?city=London',
            'health': '/api/weather/health/'
        }
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/weather/', include('weather.urls')),
]