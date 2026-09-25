"""
Celery tasks for Comparison async processing pipeline (PRD Ch. 18, 28.5).
Orchestrates document comparison via AI adapter and persists ComparisonResult records.
"""
import logging
from celery import shared_task
from django.db import transaction

from apps.comparison.models import (
    Comparison,
    ComparisonCategory,
    ComparisonResult,
    ComparisonStatus,
)
from services import ai_client
from services.ai_client.exceptions import AIServiceError

logger = logging.getLogger(__name__)


@shared_task(name='tasks.comparison_tasks.process_comparison')
def process_comparison(comparison_id):
    """
    Background processing task driving document comparison through state lifecycle:
    pending -> processing -> complete / failed
    
    Security & Reliability Rules (PRD Ch. 28.5, Ch. 29.6):
    - Idempotency: If comparison is already complete, returns early. Reprocessing clears prior comparison results.
    - Mid-Flight Deletion Guard (Ch. 26.5.1): If base_document or target_document is deleted mid-flight, transitions to FAILED without crashing.
    - Result Persistence: Persists ComparisonResult rows with category (changed, matched, missing), difference_explanation, and similarity_score.
    """
    try:
        comparison = Comparison.objects.select_related('base_document', 'target_document').get(id=comparison_id)
    except Comparison.DoesNotExist:
        logger.error(f"Comparison {comparison_id} not found for processing.")
        return {"status": "not_found", "comparison_id": str(comparison_id)}

    # Idempotency Guard
    if comparison.status == ComparisonStatus.COMPLETE:
        logger.info(f"Comparison {comparison_id} is already complete. Idempotent skip.")
        return {"status": "already_complete", "comparison_id": str(comparison_id)}

    # Mid-Flight Document Deletion Guard (Ch. 26.5.1)
    if not comparison.base_document or not comparison.target_document:
        logger.warning(f"Comparison {comparison_id} referenced a document that was deleted mid-flight.")
        comparison.status = ComparisonStatus.FAILED
        comparison.save(update_fields=['status', 'updated_at'])
        return {"status": "failed", "reason": "Referenced document was deleted mid-flight."}

    try:
        comparison.status = ComparisonStatus.PROCESSING
        comparison.save(update_fields=['status', 'updated_at'])

        doc_a_id = str(comparison.base_document.id)
        doc_b_id = str(comparison.target_document.id)

        logger.info(f"Invoking AI service compare for documents {doc_a_id} and {doc_b_id} (user: {comparison.user.id})")
        ai_response = ai_client.compare(doc_a_id, doc_b_id, user_id=str(comparison.user.id))

        with transaction.atomic():
            # Clear existing results for idempotency
            ComparisonResult.objects.filter(comparison=comparison).delete()

            base_clauses_by_id = {str(c.id): c for c in comparison.base_document.clauses.all()}
            target_clauses_by_id = {str(c.id): c for c in comparison.target_document.clauses.all()}

            # Handle grouped category keys ('changed', 'matched', 'missing')
            has_grouped = any(key in ai_response for key in ('changed', 'matched', 'missing'))

            if has_grouped:
                for cat_name in (ComparisonCategory.CHANGED, ComparisonCategory.MATCHED, ComparisonCategory.MISSING):
                    items = ai_response.get(cat_name, [])
                    for item in items:
                        explanation = (
                            item.get('risk_change') or
                            item.get('difference_explanation') or
                            item.get('explanation') or
                            f"Comparison item in category '{cat_name}'."
                        )
                        c_id_a = str(item.get('clause_a_id') or item.get('base_clause_id') or item.get('clause_id_a') or '')
                        c_id_b = str(item.get('clause_b_id') or item.get('target_clause_id') or item.get('clause_id_b') or '')
                        ComparisonResult.objects.create(
                            comparison=comparison,
                            base_clause=base_clauses_by_id.get(c_id_a),
                            target_clause=target_clauses_by_id.get(c_id_b),
                            category=cat_name,
                            difference_explanation=explanation,
                            similarity_score=item.get('similarity_score', 0.8 if cat_name == ComparisonCategory.MATCHED else 0.4)
                        )
            else:
                items_list = ai_response.get('comparison_results', ai_response.get('differences', ai_response.get('results', [])))
                for item in items_list:
                    raw_category = str(item.get('classification') or item.get('category') or 'changed').lower()
                    if raw_category not in (ComparisonCategory.CHANGED, ComparisonCategory.MATCHED, ComparisonCategory.MISSING):
                        raw_category = ComparisonCategory.CHANGED

                    c_id_a = str(item.get('clause_id_a') or item.get('base_clause_id') or item.get('clause_a_id') or '')
                    c_id_b = str(item.get('clause_id_b') or item.get('target_clause_id') or item.get('clause_b_id') or '')

                    ComparisonResult.objects.create(
                        comparison=comparison,
                        base_clause=base_clauses_by_id.get(c_id_a),
                        target_clause=target_clauses_by_id.get(c_id_b),
                        category=raw_category,
                        difference_explanation=item.get('difference_explanation', item.get('explanation', '')),
                        similarity_score=item.get('similarity_score', item.get('similarity', 0.8))
                    )


        comparison.status = ComparisonStatus.COMPLETE
        comparison.save(update_fields=['status', 'updated_at'])
        logger.info(f"Comparison {comparison_id} processing successfully completed.")
        return {"status": "complete", "comparison_id": str(comparison_id)}

    except (AIServiceError, Exception) as exc:
        logger.error(f"Unhandled failure during comparison {comparison_id} processing: {exc}")
        comparison.status = ComparisonStatus.FAILED
        comparison.save(update_fields=['status', 'updated_at'])
        raise
