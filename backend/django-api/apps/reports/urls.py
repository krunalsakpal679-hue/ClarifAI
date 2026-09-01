"""
URL routing for Report download endpoints (PRD Ch. 30.6).
"""
from django.urls import path
from apps.reports.views import ReportDownloadView

urlpatterns = [
    path('<uuid:pk>/download/', ReportDownloadView.as_view(), name='report_download'),
]
