"""
URL routing for Documents endpoints (PRD Ch. 30.2).
"""
from django.urls import path
from apps.documents.views import DocumentDetailDeleteView, DocumentListCreateView

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document_list_create'),
    path('<uuid:pk>/', DocumentDetailDeleteView.as_view(), name='document_detail_delete'),
]
