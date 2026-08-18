from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from common.views import HealthView

api_v1_patterns = [
    path('auth/', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('repositories/', include('repositories.urls')),
    path('analyses/', include('analyses.urls')),
    path('reports/', include('reports.urls')),
    path('webhooks/', include('webhooks.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('health/', HealthView.as_view(), name='health'),
]

urlpatterns: list[URLPattern | URLResolver] = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
    urlpatterns.insert(0, path('__debug__/', include(debug_toolbar.urls)))
