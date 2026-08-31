"""
Celery configuration for ClarifAI project (PRD Ch. 18.3 & 28.3).
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('clarifai')

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in installed apps and tasks/ package
app.autodiscover_tasks()
