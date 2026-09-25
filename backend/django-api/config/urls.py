"""
URL Configuration for ClarifAI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


from django.db import connection


def health_check(request):
    """Health check endpoint for Django API service verifying database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception:
        return JsonResponse({
            "status": "unhealthy",
            "service": "ClarifAI Django API",
            "database": "disconnected"
        }, status=503)

    return JsonResponse({
        "status": "healthy",
        "service": "ClarifAI Django API",
        "version": "1.0.0"
    })


from apps.documents.views import DashboardSummaryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/auth/', include('apps.users.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/comparisons/', include('apps.comparison.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/dashboard/summary', DashboardSummaryView.as_view(), name='dashboard_summary'),
]



