"""
Production settings for ClarifAI Django service.
"""
import os
import dj_database_url
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Production PostgreSQL Database Configuration parsed from DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}
