"""
Celery tasks for Document async processing pipeline (PRD Ch. 15, 18.3, 28.3, Part B.6).
Orchestrates document extraction, risk classification, rule findings, simplification, and summarization via AI adapter.
"""
import logging
from celery import shared_task
from django.db import transaction

from apps.documents.models import (
    Clause,
    ClauseCategory,
    ClauseSeverity,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)
from services import ai_client
from services.ai_client.exceptions import AIServiceError

logger = logging.getLogger(__name__)

ALLOWED_SEVERITIES = {'high', 'moderate', 'low', 'safe'}
ALLOWED_CATEGORIES = {
    'Payment',
    'Termination',
    'Renewal',
    'Confidentiality',
    'Liability',
    'Intellectual Property',
    'Privacy',
    'Dispute Resolution',
}


@shared_task(name='tasks.document_tasks.process_document')
def process_document(document_id):
    """
    Background processing task driving a Document through the exact PRD Ch. 15 state lifecycle:
    queued -> extracting -> ocr -> segmenting -> classifying -> simplifying -> summarizing -> indexing -> complete
    
    Security, Reliability & Persistence Rules (PRD Part B.6, Ch. 16.5, Ch. 29.10, Ch. 56.9-56.10):
    - Idempotency: Reprocessing clears prior clause/summary records for that document before re-persisting.
    - AI Integration: Invokes services.ai_client.process_document(document_id, file_reference).
    - Summary & Clauses: Persists DocumentSummary and Clause records with rule_findings JSON array.
    - Conflict Policy (Part B.6): Classifier output is final severity; rule findings are preserved as evidence.
    - Per-Clause Isolation (Ch. 16.5): Failure in one clause marks only that clause as failed; valid clauses are saved.
    - Invalid Classifier Output (Ch. 56.10): Invalid classifier outputs mark clause as failed, NEVER silently "Safe".
    - Data Protection: Never logs raw document body text (PRD Ch. 26.8).
    """
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found for processing.")
        return {"status": "not_found", "document_id": str(document_id)}

    # Idempotency Guard (PRD Ch. 33.12)
    if document.status == DocumentStatus.COMPLETE:
        logger.info(f"Document {document_id} is already complete. Idempotent skip.")
        return {"status": "already_complete", "document_id": str(document_id)}

    try:
        # 1. Idempotency Cleanup: Clear prior clauses and summary records for this document
        with transaction.atomic():
            Clause.objects.filter(document=document).delete()
            DocumentSummary.objects.filter(document=document).delete()

        # 2. Extracting & AI Microservice Call
        document.transition_to(DocumentStatus.EXTRACTING)
        logger.info(f"Invoking AI service process_document for document {document_id}")
        ai_response = ai_client.process_document(str(document.id), str(document.file_reference))

        # 3. State Progression: OCR -> Segmenting -> Classifying -> Simplifying -> Summarizing
        document.transition_to(DocumentStatus.OCR)
        document.transition_to(DocumentStatus.SEGMENTING)
        document.transition_to(DocumentStatus.CLASSIFYING)
        document.transition_to(DocumentStatus.SIMPLIFYING)
        document.transition_to(DocumentStatus.SUMMARIZING)

        # 4. Persist Document Summary
        summary_payload = ai_response.get('summary', {})
        if isinstance(summary_payload, dict):
            overview = summary_payload.get('overview', '')
            key_points = summary_payload.get('key_points', [])
            key_risks_text = "\n".join(key_points) if isinstance(key_points, list) else str(key_points)
        else:
            overview = str(summary_payload)
            key_risks_text = ""

        DocumentSummary.objects.create(
            document=document,
            purpose_text=overview,
            key_risks_text=key_risks_text,
            key_terms_text="",
            obligations_text=""
        )

        # 5. Indexing & Clause Persistence with Per-Clause Failure Isolation & Conflict Policy
        document.transition_to(DocumentStatus.INDEXING)
        clauses_payload = ai_response.get('clauses', [])

        for idx, clause_item in enumerate(clauses_payload, start=1):
            clause_status = clause_item.get('status')
            raw_severity = clause_item.get('severity')
            raw_category = clause_item.get('category')
            original_text = clause_item.get('original_text', f'Clause {idx}')
            simplified_text = clause_item.get('simplified_text', '')
            explanation = clause_item.get('explanation', '')
            rule_findings = clause_item.get('rule_findings', [])

            # Check for Per-Clause Failure Isolation (Ch. 16.5) or Invalid Classifier Output (Ch. 56.10)
            is_clause_failed = (
                clause_status in ('failed', 'clause_extraction_failed') or
                raw_severity not in ALLOWED_SEVERITIES or
                raw_category not in ALLOWED_CATEGORIES or
                not original_text
            )

            if is_clause_failed:
                # Per-Clause Failure Isolation: Mark ONLY this clause as FAILED.
                # Do NOT invent "safe" or silent fallback severity (Ch. 56.10).
                Clause.objects.create(
                    document=document,
                    position=idx,
                    original_text=original_text or f"Clause {idx}",
                    simplified_text=simplified_text or "Clause processing failed.",
                    explanation=explanation or "Clause classification/extraction failed during AI pipeline execution.",
                    severity=None,
                    category=None,
                    status=ClauseStatus.FAILED,
                    rule_findings=rule_findings if isinstance(rule_findings, list) else []
                )
                logger.warning(f"Clause {idx} for document {document_id} marked as FAILED (isolated failure).")
            else:
                # Part B.6 Conflict Policy:
                # Classifier severity is final. Rule findings are preserved in rule_findings JSON array as evidence.
                Clause.objects.create(
                    document=document,
                    position=idx,
                    original_text=original_text,
                    simplified_text=simplified_text,
                    explanation=explanation,
                    severity=raw_severity,
                    category=raw_category,
                    status=ClauseStatus.COMPLETE,
                    rule_findings=rule_findings if isinstance(rule_findings, list) else []
                )

        # 6. Final Transition to Complete
        document.transition_to(DocumentStatus.COMPLETE)
        logger.info(f"Document {document_id} processing successfully completed and persisted.")
        return {"status": "complete", "document_id": str(document_id)}

    except (AIServiceError, Exception) as exc:
        logger.error(f"Unhandled failure during document {document_id} processing: {exc}")
        try:
            document.transition_to(DocumentStatus.FAILED, failure_reason=str(exc))
            # Audit Log: analysis_failure (PRD Ch. 26.8)
            from apps.audit.services import EVENT_ANALYSIS_FAILURE, log_audit_event
            log_audit_event(
                EVENT_ANALYSIS_FAILURE,
                user=document.user,
                metadata={"document_id": str(document.id), "failure_reason": str(exc)}
            )
        except Exception as transition_exc:
            logger.critical(f"Failed to transition document {document_id} to failed: {transition_exc}")
        raise

