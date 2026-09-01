"""
URL routing for Comparison endpoints (PRD Ch. 30.5).
"""
from django.urls import path
from apps.comparison.views import ComparisonDetailView, ComparisonListCreateView
from apps.reports.views import ComparisonReportCreateView

urlpatterns = [
    path('', ComparisonListCreateView.as_view(), name='comparison_list_create'),
    path('<uuid:pk>/', ComparisonDetailView.as_view(), name='comparison_detail'),
    path('<uuid:pk>/report/', ComparisonReportCreateView.as_view(), name='comparison_report_create'),
]

