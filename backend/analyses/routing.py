from django.urls import re_path
from .consumers import AnalysisStatusConsumer

websocket_urlpatterns = [
    re_path(r'ws/analyses/(?P<analysis_id>[^/]+)/$', AnalysisStatusConsumer.as_asgi()),
]
