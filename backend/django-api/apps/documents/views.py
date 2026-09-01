"""
Views for Document upload, list, detail polling, and deletion endpoints (PRD Ch. 30.2).
"""
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
from apps.documents.serializers import (
    ClauseSerializer,
    DocumentDetailSerializer,
    DocumentSummarySerializer,
    DocumentUploadSerializer,
)
from core.pagination import StandardPageNumberPagination
from core.permissions import IsOwner
from tasks.document_tasks import process_document


class DocumentNotReadyException(APIException):
    """
    HTTP 422 Unprocessable Entity returned when querying analysis/clauses of an incomplete document (PRD Ch. 30.8).
    """
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Document analysis is still in progress.'
    default_code = 'DOCUMENT_NOT_READY'


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
    DELETE /api/documents/{id}/ - Delete document & full cascade cleanup (Owner-only, 404 for non-owners)
    
    Deletion Cascade (PRD Ch. 26.5.1 & Ch. 26.5.2):
    - Triggers AI service Qdrant vector embedding cleanup via adapter.
    - Removes stored PDF file from storage.
    - Cascade deletes Document, Clause, DocumentSummary, ChatSession, ChatMessage, and Report records.
    - Sets comparison FKs to NULL (SET_NULL) to preserve comparison history shell without orphans.
    - Purges active application data; does not claim instantaneous erasure from backup systems.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer

    def perform_destroy(self, instance):
        doc_id = str(instance.id)

        # 1. Trigger AI service Qdrant vector embedding cleanup (PRD Ch. 26.5.1 & Part B.3)
        try:
            from services.ai_client import delete_document_embeddings
            delete_document_embeddings(doc_id)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"Vector cleanup trigger for document {doc_id} failed or unavailable: {exc}"
            )

        # 2. Clean up physical file from storage if present
        if instance.file_reference and default_storage.exists(instance.file_reference):
            try:
                default_storage.delete(instance.file_reference)
            except Exception:
                pass

        # 3. Cascade delete document record and related DB entities
        instance.delete()



class DocumentSummaryView(generics.RetrieveAPIView):
    """
    GET /api/documents/{id}/summary - Retrieve document summary (Owner-only).
    Returns 422 Unprocessable Entity if document is incomplete.
    Returns 404 Not Found if non-owned or nonexistent.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = DocumentSummarySerializer

    def get_object(self):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(self.request, document)

        if document.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException()

        try:
            return document.summary
        except DocumentSummary.DoesNotExist:
            raise DocumentNotReadyException("Summary not found for completed document.")


class ClauseListView(generics.ListAPIView):
    """
    GET /api/documents/{id}/clauses - List document clauses (Owner-only).
    Supports optional ?severity= filter (high, moderate, low, safe) and ?lang= parameter.
    Returns 422 Unprocessable Entity if document is incomplete.
    Returns 404 Not Found if non-owned or nonexistent.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ClauseSerializer
    pagination_class = StandardPageNumberPagination

    def get_queryset(self):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(self.request, document)

        if document.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException()

        queryset = Clause.objects.filter(document=document).order_by('position')

        severity_filter = self.request.query_params.get('severity', '').lower()
        if severity_filter in ('high', 'moderate', 'low', 'safe'):
            queryset = queryset.filter(severity=severity_filter)

        return queryset


class ClauseDetailView(generics.RetrieveAPIView):
    """
    GET /api/documents/{id}/clauses/{clause_id}/ - Single clause detail (Owner-only).
    Returns 422 Unprocessable Entity if document is incomplete.
    Returns 404 Not Found if document/clause is non-owned or nonexistent.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ClauseSerializer

    def get_object(self):
        document_id = self.kwargs.get('pk')
        clause_id = self.kwargs.get('clause_id')

        document = get_object_or_404(Document, pk=document_id)
        self.check_object_permissions(self.request, document)

        if document.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException()

        clause = get_object_or_404(Clause, pk=clause_id, document=document)
        return clause


class DashboardSummaryView(generics.GenericAPIView):
    """
    GET /api/dashboard/summary - Retrieve aggregate document statistics for requesting user (PRD Ch. 30.7 & Ch. 20).
    Scoped strictly to request.user documents only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_docs = Document.objects.filter(user=request.user)
        total_documents = user_docs.count()
        completed_count = user_docs.filter(status=DocumentStatus.COMPLETE).count()
        failed_count = user_docs.filter(status=DocumentStatus.FAILED).count()
        in_progress_count = total_documents - (completed_count + failed_count)

        # Flagged risk count: completed documents with at least one non-Safe clause
        flagged_risk_count = user_docs.filter(
            status=DocumentStatus.COMPLETE,
            clauses__severity__in=['high', 'moderate', 'low']
        ).distinct().count()

        return Response({
            "total_documents": total_documents,
            "in_progress_count": in_progress_count,
            "flagged_risk_count": flagged_risk_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }, status=status.HTTP_200_OK)


