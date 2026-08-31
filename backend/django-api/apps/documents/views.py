"""
Views for Document upload, list, detail polling, and deletion endpoints (PRD Ch. 30.2).
"""
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.documents.models import Document
from apps.documents.serializers import (
    DocumentDetailSerializer,
    DocumentUploadSerializer,
)
from core.pagination import StandardPageNumberPagination
from core.permissions import IsOwner


from tasks.document_tasks import process_document


class DocumentListCreateView(generics.ListCreateAPIView):
    """
    POST /api/documents/ - Upload document (Authenticated, status=queued, enqueues process_document)
    GET  /api/documents/ - List owner's documents (Authenticated, owner-scoped)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentUploadSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        # Enqueue background processing task asynchronously (PRD Ch. 18.3 & 28.3)
        process_document.delay(str(document.id))

        response_serializer = DocumentDetailSerializer(document)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



class DocumentDetailDeleteView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/documents/{id}/ - Detail & status polling endpoint (Owner-only, 404 for non-owners)
    DELETE /api/documents/{id}/ - Delete document & cascade file cleanup (Owner-only, 404 for non-owners)
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer

    def perform_destroy(self, instance):
        # Clean up file from storage if present
        if instance.file_reference and default_storage.exists(instance.file_reference):
            try:
                default_storage.delete(instance.file_reference)
            except Exception:
                pass
        # Cascade delete document record and related DB entities
        instance.delete()
