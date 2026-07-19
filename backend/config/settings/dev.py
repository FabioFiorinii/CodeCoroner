from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES['default']['OPTIONS'] = {}

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)
