"""
Views for Report generation and PDF download endpoints (PRD Ch. 30.6).
Enforces owner-only security posture, failure isolation, and FileResponse downloads.
"""
import os
import logging
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.comparison.models import Comparison, ComparisonStatus
from apps.documents.models import Document, DocumentStatus
from apps.documents.views import DocumentNotReadyException
from apps.reports.generator import generate_comparison_pdf, generate_document_pdf
from apps.reports.models import Report, ReportStatus
from apps.reports.serializers import ReportCreateInputSerializer, ReportSerializer
from core.permissions import IsOwner

logger = logging.getLogger(__name__)


class DocumentReportCreateView(generics.CreateAPIView):
    """
    POST /api/documents/{id}/report - Generate PDF report for analyzed document (Owner-only).
    
    Security & Reliability Rules (PRD Ch. 28.1, Ch. 30.6):
    - Ownership: Strictly scoped to document owner (returns 404 for non-owners).
    - Status Check: Document must be DocumentStatus.COMPLETE (returns 422 DOCUMENT_NOT_READY if incomplete).
    - Resource Constraint: Sets document_id and leaves comparison_id NULL.
    - Failure Isolation: Generation failures mark report.status = FAILED without corrupting Document/Clause DB records.
    - Ch. 59 Resolution: Regenerate-on-request (compiles a fresh PDF per request).
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(request, document)

        if document.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException("Document analysis must be completed before generating a report.")

        input_serializer = ReportCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        language = input_serializer.validated_data.get('language') or request.data.get('lang') or 'en'

        report = Report.objects.create(
            user=request.user,
            document=document,
            comparison=None,
            language=language,
            status=ReportStatus.PENDING
        )

        try:
            file_path = generate_document_pdf(report, document, language=language)
            report.file_reference = file_path
            report.status = ReportStatus.COMPLETE
            report.save(update_fields=['file_reference', 'status'])
        except Exception as exc:
            logger.error(f"Failed to generate document PDF report {report.id}: {exc}")
            report.status = ReportStatus.FAILED
            report.failure_reason = str(exc)
            report.save(update_fields=['status', 'failure_reason'])
            raise APIException(
                detail={"error": {"code": "REPORT_GENERATION_FAILED", "message": "Failed to compile document report PDF."}},
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ComparisonReportCreateView(generics.CreateAPIView):
    """
    POST /api/comparisons/{id}/report - Generate PDF report for comparison (Owner-only).
    
    Security & Reliability Rules (PRD Ch. 28.1, Ch. 30.6):
    - Ownership: Strictly scoped to comparison owner (returns 404 for non-owners).
    - Status Check: Comparison must be ComparisonStatus.COMPLETE (returns 422 DOCUMENT_NOT_READY if incomplete).
    - Resource Constraint: Sets comparison_id and leaves document_id NULL.
    - Failure Isolation: Generation failures mark report.status = FAILED without corrupting Comparison DB records.
    - Ch. 59 Resolution: Regenerate-on-request (compiles a fresh PDF per request).
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        comparison_id = self.kwargs.get('pk')
        comparison = get_object_or_404(Comparison, pk=comparison_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(request, comparison)

        if comparison.status != ComparisonStatus.COMPLETE:
            raise DocumentNotReadyException("Comparison must be completed before generating a report.")

        input_serializer = ReportCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        language = input_serializer.validated_data.get('language') or request.data.get('lang') or 'en'

        report = Report.objects.create(
            user=request.user,
            document=None,
            comparison=comparison,
            language=language,
            status=ReportStatus.PENDING
        )

        try:
            file_path = generate_comparison_pdf(report, comparison, language=language)
            report.file_reference = file_path
            report.status = ReportStatus.COMPLETE
            report.save(update_fields=['file_reference', 'status'])
        except Exception as exc:
            logger.error(f"Failed to generate comparison PDF report {report.id}: {exc}")
            report.status = ReportStatus.FAILED
            report.failure_reason = str(exc)
            report.save(update_fields=['status', 'failure_reason'])
            raise APIException(
                detail={"error": {"code": "REPORT_GENERATION_FAILED", "message": "Failed to compile comparison report PDF."}},
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ReportDownloadView(generics.RetrieveAPIView):
    """
    GET /api/reports/{id}/download - Stream compiled PDF file for download (Owner-only).
    
    Security Posture (PRD Ch. 26.3 & Task 8):
    - Report files are NEVER publicly served. Every request enforces authentication and IsOwner check.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Report.objects.all()

    def retrieve(self, request, *args, **kwargs):
        report_id = self.kwargs.get('pk')
        report = get_object_or_404(Report, pk=report_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(request, report)

        if report.status != ReportStatus.COMPLETE or not report.file_reference or not os.path.exists(report.file_reference):
            raise NotFound("Generated report file was not found or report is not complete.")

        filename = f"clarifai_report_{report.id}.pdf"
        file_handle = open(report.file_reference, 'rb')
        response = FileResponse(file_handle, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
