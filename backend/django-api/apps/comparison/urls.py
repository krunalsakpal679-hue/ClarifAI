"""
URL routing for Comparison endpoints (PRD Ch. 30.5).
"""
from django.urls import path
from apps.comparison.views import ComparisonDetailView, ComparisonListCreateView

urlpatterns = [
    path('', ComparisonListCreateView.as_view(), name='comparison_list_create'),
    path('<uuid:pk>/', ComparisonDetailView.as_view(), name='comparison_detail'),
]
