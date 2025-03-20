"""
MoonVPN Test Settings

This module contains test-specific settings that override base settings.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-test-key'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Celery
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Password hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}

# Payment Gateway
PAYMENT['ZARINPAL']['SANDBOX'] = True
PAYMENT['ZARINPAL']['MERCHANT_ID'] = 'test-merchant-id'

# VPN Panel settings for testing
VPN_PANEL.update({
    'DOMAIN': 'localhost',
    'PORT': '8080',
    'PATH': '/test',
    'API_PATH': '/api',
    'USERNAME': 'test',
    'PASSWORD': 'test',
    'SSL': False,
})

# Telegram Bot settings for testing
TELEGRAM.update({
    'BOT_TOKEN': 'test-bot-token',
    'ADMIN_IDS': [123456789],
    'MANAGEMENT_GROUPS': {
        'MANAGE': '-100123456789',
        'REPORTS': '-100123456790',
        'LOGS': '-100123456791',
        'TRANSACTIONS': '-100123456792',
        'OUTAGES': '-100123456793',
        'SELLERS': '-100123456794',
        'BACKUPS': '-100123456795',
    },
})

# System settings for testing
SYSTEM.update({
    'BACKUP_PATH': os.path.join(BASE_DIR, 'test_backup'),
    'BACKUP_RETENTION_DAYS': 1,
    'TRAFFIC_CHECK_INTERVAL': 1,  # 1 second for faster testing
    'WARNING_THRESHOLDS': {
        'traffic': [50, 75],  # Reduced thresholds for testing
        'bandwidth': [50, 75],
    },
}) 