from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from common.views import ModelSettingsView

from .views import (
    ChangePasswordView,
    GroupViewSet,
    LoginView,
    RegisterView,
    UserAdminViewSet,
    UserDetailView,
)

admin_router = DefaultRouter()
admin_router.register(r'users', UserAdminViewSet, basename='admin-user')
admin_router.register(r'groups', GroupViewSet, basename='admin-group')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', UserDetailView.as_view(), name='auth-me'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('admin/', include(admin_router.urls)),
    path('admin/model-settings/', ModelSettingsView.as_view(), name='model-settings'),
]
