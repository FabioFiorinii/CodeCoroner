from .base import *

DEBUG = False

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


CORS_ALLOWED_ORIGINS = _csv_env('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = _csv_env('CSRF_TRUSTED_ORIGINS')

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'user': os.environ.get('RATE_LIMIT_USER', '100/hour'),
    'anon': os.environ.get('RATE_LIMIT_ANON', '10/hour'),
}

LOGGING['root']['level'] = 'WARNING'
LOGGING['root']['handlers'] = ['console_json', 'app_file']
