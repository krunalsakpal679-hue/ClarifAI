"""
URL Configuration for ClarifAI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Basic health check endpoint for Django API service."""
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



