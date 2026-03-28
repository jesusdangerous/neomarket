from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_view(request):
    return JsonResponse({
        'status': 'ok',
        'service': 'catalog',
    })


urlpatterns = [
    path('health/', health_view, name='health'),
    path('api/v1/', include('catalog_api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]

