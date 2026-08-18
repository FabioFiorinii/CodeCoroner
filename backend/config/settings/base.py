import json
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

IS_PRODUCTION = os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.prod')


def _require_secret(name: str, default: str) -> str:
    value = os.environ.get(name, '')
    if value and value != default:
        return value
    if IS_PRODUCTION:
        raise ImproperlyConfigured(f'{name} must be set to a non-default value in production')
    return default


SECRET_KEY = _require_secret('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'axes',
    'accounts',
    'projects',
    'repositories',
    'analyses',
    'reports',
    'webhooks',
    'common',
    'dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'codecoroner'),
        'USER': os.environ.get('DB_USER', 'codecoroner'),
        'PASSWORD': _require_secret('DB_PASSWORD', 'dev_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {'pool': True},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_USERNAME_FORM_FIELD = 'email'
AXES_LOCKOUT_PARAMETERS = ['username']
AXES_LOCKOUT_TEMPLATE = None
AXES_RESET_ON_SUCCESS = True
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '200/hour',
        'anon': '20/hour',
    },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

AI_ENGINE_URL = os.environ.get('AI_ENGINE_URL', 'http://ai-engine:8002')

WEBHOOK_SECRET_KEY = os.environ.get('WEBHOOK_SECRET_KEY', '')

AUTO_PULL_HOUR = int(os.environ.get('AUTO_PULL_HOUR', '3'))
AUTO_PULL_MINUTE = int(os.environ.get('AUTO_PULL_MINUTE', '0'))

LDAP_GROUP_MAP = json.loads(os.environ.get('LDAP_GROUP_MAP', '{}'))

if os.environ.get('LDAP_SERVER_URI'):
    import ldap
    from django_auth_ldap.config import GroupOfNamesType, LDAPSearch

    AUTHENTICATION_BACKENDS = [
        'axes.backends.AxesStandaloneBackend',
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
    AUTH_LDAP_SERVER_URI = os.environ['LDAP_SERVER_URI']
    AUTH_LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN')
    AUTH_LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD')
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        os.environ.get('LDAP_BASE_DN', 'dc=codecoroner,dc=dev'),
        ldap.SCOPE_SUBTREE,
        '(mail=%(user)s)',
    )
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        os.environ.get('LDAP_BASE_DN', 'dc=codecoroner,dc=dev'),
        ldap.SCOPE_SUBTREE,
        '(objectClass=groupOfNames)',
    )
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
    AUTH_LDAP_USER_ATTR_MAP = {
        'username': 'uid',
        'first_name': 'givenName',
        'last_name': 'sn',
        'email': 'mail',
    }
    AUTH_LDAP_ALWAYS_UPDATE_USER = True
    user_flags = {}
    if os.environ.get('LDAP_STAFF_GROUP'):
        user_flags['is_staff'] = os.environ['LDAP_STAFF_GROUP']
    if os.environ.get('LDAP_SUPERUSER_GROUP'):
        user_flags['is_superuser'] = os.environ['LDAP_SUPERUSER_GROUP']
    AUTH_LDAP_USER_FLAGS_BY_GROUP = user_flags

MODEL_TIERS = {
    'fast': {
        'label': 'Fast',
        'llm_model': 'qwen2.5-coder:3b',
        'rca_model': 'qwen2.5-coder:3b',
        'params': '3.1B',
    },
    'balanced': {
        'label': 'Balanced',
        'llm_model': 'qwen2.5-coder:7b',
        'rca_model': 'qwen2.5-coder:7b',
        'params': '7.6B',
    },
    'precise': {
        'label': 'Precise',
        'llm_model': 'qwen2.5-coder:14b',
        'rca_model': 'qwen2.5-coder:14b',
        'params': '14.8B',
    },
}

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:8080,http://localhost:5173',
).split(',')

CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
}
