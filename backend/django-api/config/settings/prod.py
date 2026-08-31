"""
Production settings for ClarifAI Django service.
"""
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Production PostgreSQL Database Configuration Placeholder
# Full PostgreSQL wiring per DATABASE_URL configured in Phase 1
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
