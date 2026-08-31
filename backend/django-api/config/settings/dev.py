"""
Development settings for ClarifAI Django service.
"""
import os
import dj_database_url
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Parse DATABASE_URL if set; otherwise fallback to local SQLite for offline dev
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Allow unauthenticated access to health check during dev
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.AllowAny',
]
