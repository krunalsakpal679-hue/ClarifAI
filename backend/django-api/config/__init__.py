"""
Config package initialization.
Loads Celery app on Django startup.
"""
from config.celery import app as celery_app

__all__ = ('celery_app',)
