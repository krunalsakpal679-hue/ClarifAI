"""
URL Configuration for ClarifAI project.
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def health_check(request):
    """Basic health check endpoint for Django API service."""
    return JsonResponse({
        "status": "healthy",
        "service": "ClarifAI Django API",
        "version": "1.0.0"
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
]
