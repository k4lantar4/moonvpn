"""
MoonVPN Base Settings

This module contains the base settings for the MoonVPN project.
All environment-specific settings should inherit from these base settings.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'corsheaders',
    # Local apps
    'backend.core',
    'backend.models',
    'backend.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'moonvpn'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
        }
    }
}

# Celery settings
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# CORS settings
CORS_ORIGIN_WHITELIST = os.getenv('CORS_ORIGIN_WHITELIST', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# VPN Panel settings
VPN_PANEL = {
    'DOMAIN': os.getenv('V2RAY_PANEL_DOMAIN', '46.105.239.6'),
    'PORT': os.getenv('V2RAY_PANEL_PORT', '2096'),
    'PATH': os.getenv('V2RAY_PANEL_PATH', '/jdkfg34lj5468vdfgn943n0235nj7g54'),
    'API_PATH': os.getenv('V2RAY_PANEL_API_PATH', '/panel/api'),
    'USERNAME': os.getenv('V2RAY_PANEL_USERNAME', 'k4lantar4'),
    'PASSWORD': os.getenv('V2RAY_PANEL_PASSWORD', '}|9QV;y5T5+4'),
    'SSL': os.getenv('V2RAY_PANEL_SSL', 'false').lower() == 'true',
}

# Payment Gateway settings
PAYMENT = {
    'ZARINPAL': {
        'MERCHANT_ID': os.getenv('ZARINPAL_MERCHANT_ID', ''),
        'SANDBOX': os.getenv('ZARINPAL_SANDBOX', 'True') == 'True',
    },
}

# Telegram Bot settings
TELEGRAM = {
    'BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'ADMIN_IDS': list(map(int, os.getenv('TELEGRAM_ADMIN_IDS', '').split(','))),
    'MANAGEMENT_GROUPS': {
        'MANAGE': os.getenv('TELEGRAM_MANAGE_GROUP', ''),
        'REPORTS': os.getenv('TELEGRAM_REPORTS_GROUP', ''),
        'LOGS': os.getenv('TELEGRAM_LOGS_GROUP', ''),
        'TRANSACTIONS': os.getenv('TELEGRAM_TRANSACTIONS_GROUP', ''),
        'OUTAGES': os.getenv('TELEGRAM_OUTAGES_GROUP', ''),
        'SELLERS': os.getenv('TELEGRAM_SELLERS_GROUP', ''),
        'BACKUPS': os.getenv('TELEGRAM_BACKUPS_GROUP', ''),
    },
}

# System settings
SYSTEM = {
    'BACKUP_PATH': os.path.join(BASE_DIR, 'backup'),
    'BACKUP_RETENTION_DAYS': 30,
    'TRAFFIC_CHECK_INTERVAL': 300,  # 5 minutes
    'WARNING_THRESHOLDS': {
        'traffic': [50, 75, 90, 95],  # Percentage of limit
        'bandwidth': [50, 75, 90, 95]  # Percentage of capacity
    },
} 