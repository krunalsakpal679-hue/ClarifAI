"""
Celery tasks for Document async processing pipeline (PRD Ch. 15, 18.3, 28.3).
"""
import logging
from celery import shared_task
from apps.documents.models import Document, DocumentStatus

logger = logging.getLogger(__name__)


@shared_task(name='tasks.document_tasks.process_document')
def process_document(document_id):
    """
    Background processing task driving a Document through the exact PRD Ch. 15 state lifecycle:
    queued -> extracting -> ocr -> segmenting -> classifying -> simplifying -> summarizing -> indexing -> complete
    
    Security & Reliability Rules:
    - Idempotency: Reprocessing an already-complete document is a no-op guard.
    - Failure Handling: Unhandled exceptions transition Document to status=failed with failure_reason (never stuck).
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
        # Sequential PRD Ch. 15 forward processing lifecycle
        pipeline_sequence = [
            DocumentStatus.EXTRACTING,
            DocumentStatus.OCR,
            DocumentStatus.SEGMENTING,
            DocumentStatus.CLASSIFYING,
            DocumentStatus.SIMPLIFYING,
            DocumentStatus.SUMMARIZING,
            DocumentStatus.INDEXING,
            DocumentStatus.COMPLETE,
        ]

        for next_status in pipeline_sequence:
            # Transition document status safely
            document.transition_to(next_status)
            logger.debug(f"Document {document_id} transitioned to {next_status}")

        logger.info(f"Document {document_id} processing complete.")
        return {"status": "complete", "document_id": str(document_id)}

    except Exception as exc:
        logger.error(f"Unhandled failure during document {document_id} processing: {exc}")
        # Ensure document is never left stuck in a non-terminal state
        try:
            document.transition_to(DocumentStatus.FAILED, failure_reason=str(exc))
        except Exception as transition_exc:
            logger.critical(f"Failed to transition document {document_id} to failed: {transition_exc}")
        raise
