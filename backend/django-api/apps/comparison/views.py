"""
Views for Comparison creation and detail retrieval endpoints (PRD Ch. 30.5).
Enforces explicit double-ownership check and document processing completion rules.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.comparison.models import Comparison, ComparisonStatus
from apps.comparison.serializers import (
    ComparisonCreateInputSerializer,
    ComparisonDetailSerializer,
)
from apps.documents.models import Document, DocumentStatus
from apps.documents.views import DocumentNotReadyException
from core.permissions import IsOwner
from tasks.comparison_tasks import process_comparison


class ComparisonListCreateView(generics.ListCreateAPIView):
    """
    POST /api/comparisons/ - Create document comparison (Authenticated).
    GET  /api/comparisons/ - List user's comparisons (Authenticated, owner-scoped).
    
    Security & Validation Rules (PRD Ch. 18, Ch. 30.5):
    - Double-Ownership Check: BOTH base_document and target_document must belong to request.user (404 if either is unowned/missing).
    - Different Document Check: Cannot compare a document against itself (400 if document_a == document_b).
    - Completion Check: BOTH documents must be DocumentStatus.COMPLETE (422 DOCUMENT_NOT_READY if either is incomplete).
    - Async Execution: Enqueues process_comparison.delay(comparison_id).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ComparisonDetailSerializer

    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        input_serializer = ComparisonCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        doc_a_id = input_serializer.validated_data['document_a_id']
        doc_b_id = input_serializer.validated_data['document_b_id']

        # 1. Explicit Double-Ownership Check (404 for unowned or missing documents)
        doc_a = Document.objects.filter(id=doc_a_id, user=request.user).first()
        doc_b = Document.objects.filter(id=doc_b_id, user=request.user).first()

        if not doc_a or not doc_b:
            raise NotFound("One or both referenced documents were not found or not owned.")

        # 2. Completion Check (422 DOCUMENT_NOT_READY if either document is not complete)
        if doc_a.status != DocumentStatus.COMPLETE or doc_b.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException("Both documents must be fully processed before comparison.")

        # Check for existing completed comparison between these documents
        existing_comp = Comparison.objects.filter(
            user=request.user,
            base_document=doc_a,
            target_document=doc_b,
            status=ComparisonStatus.COMPLETE
        ).order_by('-created_at').first()
        if existing_comp and existing_comp.results.exists():
            response_serializer = ComparisonDetailSerializer(existing_comp, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        # 3. Create Comparison record
        comparison = Comparison.objects.create(
            user=request.user,
            base_document=doc_a,
            target_document=doc_b,
            status=ComparisonStatus.PENDING
        )

        # 4. Enqueue Celery comparison task
        try:
            process_comparison.delay(str(comparison.id))
        except Exception as exc:
            comparison.status = ComparisonStatus.FAILED
            comparison.save()
            return Response(
                {"error": {"code": "SERVICE_UNAVAILABLE", "message": "Background task broker is currently unavailable."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        response_serializer = ComparisonDetailSerializer(comparison, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ComparisonDetailView(generics.RetrieveAPIView):
    """
    GET /api/comparisons/{id}/ - Retrieve comparison status and results (Owner-only).
    Supports UUID PK as well as composite 'comp-{docA}-{docB}' identifier.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ComparisonDetailSerializer
    queryset = Comparison.objects.all()

    def get_object(self):
        pk = str(self.kwargs.get('pk', ''))
        # Handle composite 'comp-{docA}-{docB}' pattern
        if pk.startswith('comp-'):
            sub = pk[5:]
            if len(sub) == 73 and sub[36] == '-':
                doc_a_id = sub[:36]
                doc_b_id = sub[37:]
                comp = Comparison.objects.filter(
                    user=self.request.user,
                    base_document_id=doc_a_id,
                    target_document_id=doc_b_id
                ).order_by('-created_at').first()
                if comp:
                    self.check_object_permissions(self.request, comp)
                    return comp

                doc_a = Document.objects.filter(id=doc_a_id, user=self.request.user).first()
                doc_b = Document.objects.filter(id=doc_b_id, user=self.request.user).first()
                if doc_a and doc_b:
                    comp = Comparison.objects.create(
                        user=self.request.user,
                        base_document=doc_a,
                        target_document=doc_b,
                        status=ComparisonStatus.PENDING
                    )
                    try:
                        process_comparison.delay(str(comp.id))
                    except Exception:
                        process_comparison(str(comp.id))
                    comp.refresh_from_db()
                    self.check_object_permissions(self.request, comp)
                    return comp

        return super().get_object()
