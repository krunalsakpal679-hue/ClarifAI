"""
Development settings for ClarifAI Django service.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Default SQLite database fallback for local dev / setup smoke testing (No PostgreSQL required for project setup phase)
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
