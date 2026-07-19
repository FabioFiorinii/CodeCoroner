from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

api_v1_patterns = [
    path('auth/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('repositories/', include('repositories.urls')),
    path('analyses/', include('analyses.urls')),
    path('reports/', include('reports.urls')),
    path('webhooks/', include('webhooks.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
