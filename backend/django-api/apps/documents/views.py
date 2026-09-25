"""
Views for Document upload, list, detail polling, and deletion endpoints (PRD Ch. 30.2).
"""
import logging
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.services import (
    EVENT_DOCUMENT_DELETE,
    EVENT_DOCUMENT_UPLOAD,
    log_audit_event,
)
from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
from apps.documents.serializers import (
    ClauseSerializer,
    DocumentDetailSerializer,
    DocumentSummarySerializer,
    DocumentUploadSerializer,
)
from core.pagination import StandardPageNumberPagination
from core.permissions import IsOwner
from services import ai_client
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

        # Audit Log: document_upload (PRD Ch. 26.8)
        log_audit_event(
            EVENT_DOCUMENT_UPLOAD,
            user=document.user,
            request=request,
            metadata={"document_id": str(document.id), "filename": document.original_filename}
        )

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

        # 2b. Clean up associated report files from storage if present (PRD Ch. 26.5.1)
        for report in instance.reports.all():
            if report.file_reference and default_storage.exists(report.file_reference):
                try:
                    default_storage.delete(report.file_reference)
                except Exception:
                    pass

        # 3. Audit Log: document_delete (PRD Ch. 26.8)
        log_audit_event(
            EVENT_DOCUMENT_DELETE,
            user=instance.user,
            request=self.request,
            metadata={"document_id": doc_id}
        )

        # 4. Cascade delete document record and related DB entities
        instance.delete()



class DocumentSummaryView(generics.RetrieveAPIView):
    """
    GET /api/documents/{id}/summary - Retrieve document summary (Owner-only).
    Supports optional ?lang= parameter (e.g. ?lang=hi) with graceful fallback (PRD Ch. 19).
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
            summary = document.summary
        except DocumentSummary.DoesNotExist:
            raise DocumentNotReadyException("Summary not found for completed document.")

        lang = self.request.query_params.get('lang', 'en').lower()
        if lang == 'hi':
            cache_key = f"doc_summary_hi_{document.id}"
            cached_trans = cache.get(cache_key)
            if cached_trans is not None:
                if cached_trans.get('translation_available'):
                    summary.purpose_text_hi = cached_trans.get('purpose_text')
                    summary.obligations_text_hi = cached_trans.get('obligations_text')
                    summary.key_terms_text_hi = cached_trans.get('key_terms_text')
                    summary.key_risks_text_hi = cached_trans.get('key_risks_text')
                    summary.translation_available = True
                else:
                    summary.translation_available = False
            else:
                try:
                    summary_payload = {
                        "purpose": summary.purpose_text or "",
                        "obligations": summary.obligations_text or "",
                        "key_terms": summary.key_terms_text or "",
                        "key_risks": summary.key_risks_text or ""
                    }
                    ai_res = ai_client.translate(
                        document_id=str(document.id),
                        target_lang="hi",
                        summary=summary_payload,
                        clauses=[],
                        user_id=str(self.request.user.id)
                    )
                    status_flag = ai_res.get("translation_status", "TRANSLATION_UNAVAILABLE")
                    summary_hi = ai_res.get("summary_hi") or (ai_res.get("translated_content", {}).get("summary")) or {}
                    if status_flag == "SUCCESS" and summary_hi and summary_hi.get("purpose"):
                        summary.purpose_text_hi = summary_hi.get("purpose")
                        summary.obligations_text_hi = summary_hi.get("obligations")
                        summary.key_terms_text_hi = summary_hi.get("key_terms")
                        summary.key_risks_text_hi = summary_hi.get("key_risks")
                        summary.translation_available = True
                        cache.set(cache_key, {
                            "translation_available": True,
                            "purpose_text": summary.purpose_text_hi,
                            "obligations_text": summary.obligations_text_hi,
                            "key_terms_text": summary.key_terms_text_hi,
                            "key_risks_text": summary.key_risks_text_hi,
                        }, 86400)
                    else:
                        summary.translation_available = False
                        cache.set(cache_key, {"translation_available": False}, 300)
                except Exception as exc:
                    logging.getLogger(__name__).warning(f"Translation call failed for summary doc {document.id}: {exc}")
                    summary.translation_available = False
                    cache.set(cache_key, {"translation_available": False}, 300)

        return summary


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

        clauses = list(queryset)

        lang = self.request.query_params.get('lang', 'en').lower()
        if lang == 'hi' and clauses:
            cache_key = f"doc_clauses_hi_{document.id}"
            cached_trans = cache.get(cache_key)
            if cached_trans is not None:
                trans_map = cached_trans.get('clauses_map', {})
                is_available = cached_trans.get('translation_available', False)
                for c in clauses:
                    c.translation_available = is_available
                    if str(c.id) in trans_map:
                        c.simplified_text_hi = trans_map[str(c.id)].get('simplified_text_hi')
            else:
                try:
                    clauses_payload = [
                        {
                            "id": str(c.id),
                            "position": c.position,
                            "original_text": c.original_text,
                            "simplified_text": c.simplified_text or "",
                            "why_flagged": c.explanation or ""
                        }
                        for c in clauses
                    ]
                    ai_res = ai_client.translate(
                        document_id=str(document.id),
                        target_lang="hi",
                        summary={},
                        clauses=clauses_payload,
                        user_id=str(self.request.user.id)
                    )
                    status_flag = ai_res.get("translation_status", "TRANSLATION_UNAVAILABLE")
                    clauses_hi = ai_res.get("clauses_hi") or (ai_res.get("translated_content", {}).get("clauses")) or []
                    if status_flag == "SUCCESS" and clauses_hi:
                        trans_map = {}
                        for item in clauses_hi:
                            c_id = str(item.get("id") or item.get("clause_id", ""))
                            trans_map[c_id] = {
                                "simplified_text_hi": item.get("simplified_text_hi") or item.get("simplified_text")
                            }
                        for c in clauses:
                            c.translation_available = True
                            if str(c.id) in trans_map:
                                c.simplified_text_hi = trans_map[str(c.id)].get("simplified_text_hi")
                        cache.set(cache_key, {
                            "translation_available": True,
                            "clauses_map": trans_map
                        }, 86400)
                    else:
                        for c in clauses:
                            c.translation_available = False
                        cache.set(cache_key, {"translation_available": False, "clauses_map": {}}, 300)
                except Exception as exc:
                    logging.getLogger(__name__).warning(f"Translation call failed for clauses doc {document.id}: {exc}")
                    for c in clauses:
                        c.translation_available = False
                    cache.set(cache_key, {"translation_available": False, "clauses_map": {}}, 300)

        return clauses


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

        lang = self.request.query_params.get('lang', 'en').lower()
        if lang == 'hi':
            cache_key = f"doc_clauses_hi_{document.id}"
            cached_trans = cache.get(cache_key)
            if cached_trans and cached_trans.get('translation_available'):
                trans_map = cached_trans.get('clauses_map', {})
                if str(clause.id) in trans_map:
                    clause.simplified_text_hi = trans_map[str(clause.id)].get('simplified_text_hi')
                    clause.translation_available = True
                else:
                    clause.translation_available = False
            else:
                try:
                    ai_res = ai_client.translate(
                        document_id=str(document.id),
                        target_lang="hi",
                        summary={},
                        clauses=[{
                            "id": str(clause.id),
                            "position": clause.position,
                            "original_text": clause.original_text,
                            "simplified_text": clause.simplified_text or "",
                            "why_flagged": clause.explanation or ""
                        }],
                        user_id=str(self.request.user.id)
                    )
                    status_flag = ai_res.get("translation_status", "TRANSLATION_UNAVAILABLE")
                    clauses_hi = ai_res.get("clauses_hi") or (ai_res.get("translated_content", {}).get("clauses")) or []
                    if status_flag == "SUCCESS" and clauses_hi:
                        clause.simplified_text_hi = clauses_hi[0].get("simplified_text_hi") or clauses_hi[0].get("simplified_text")
                        clause.translation_available = True
                    else:
                        clause.translation_available = False
                except Exception:
                    clause.translation_available = False

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


