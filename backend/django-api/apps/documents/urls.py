"""
URL routing for Documents endpoints (PRD Ch. 30.2).
"""
from django.urls import include, path
from apps.documents.views import (
    ClauseDetailView,
    ClauseListView,
    DocumentDetailDeleteView,
    DocumentListCreateView,
    DocumentSummaryView,
)

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document_list_create'),
    path('<uuid:pk>/', DocumentDetailDeleteView.as_view(), name='document_detail_delete'),
    path('<uuid:pk>/summary/', DocumentSummaryView.as_view(), name='document_summary'),
    path('<uuid:pk>/clauses/', ClauseListView.as_view(), name='document_clause_list'),
    path('<uuid:pk>/clauses/<uuid:clause_id>/', ClauseDetailView.as_view(), name='document_clause_detail'),
    path('<uuid:pk>/chat/', include('apps.chat.urls')),
]


