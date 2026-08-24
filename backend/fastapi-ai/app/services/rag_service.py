"""
ClarifAI RAG Pipeline & Two-Stage Gating Service Module (AI-PHASE-RAG)
Implements question embedding, ownership-scoped Qdrant retrieval, Stage 1 relevance evaluation,
Stage 2 sufficiency evaluation, and controlled no-answer decision path.
Per ClarifAI PRD v2.3 Chapter 28.5, Chapter 34, and Chapter 50.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient

from app.core.config import settings
from app.services.embedding_service import generate_query_embedding
from app.services.qdrant_service import get_qdrant_client, ensure_collection_exists, query_clauses_scoped
from app.models.common import SCHEMA_VERSION

logger = logging.getLogger(__name__)


def evaluate_relevance_stage(
    candidates: List[Dict[str, Any]],
    threshold: Optional[float] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Stage 1 — Relevance Gate: Filters retrieved candidate clauses against configured relevance threshold.

    Args:
        candidates: Retrieved Qdrant clause candidate dicts with score.
        threshold: Optional override for relevance threshold (defaults to settings.RAG_RELEVANCE_THRESHOLD).

    Returns:
        Tuple of (relevance_passed: bool, relevant_candidates: List[Dict[str, Any]]).
    """
    rel_threshold = threshold if threshold is not None else settings.RAG_RELEVANCE_THRESHOLD
    relevant_clauses = [
        cand for cand in candidates
        if cand.get("score", 0.0) >= rel_threshold
    ]

    passed = len(relevant_clauses) > 0
    logger.info(f"RAG Stage 1 Relevance Gate: {len(relevant_clauses)}/{len(candidates)} candidates passed (threshold={rel_threshold}). Passed={passed}.")
    return passed, relevant_clauses


def evaluate_sufficiency_stage(
    relevant_candidates: List[Dict[str, Any]],
    threshold: Optional[float] = None
) -> bool:
    """
    Stage 2 — Sufficiency Gate: Evaluates whether the relevant evidence set is sufficient to answer the question.

    Args:
        relevant_candidates: Candidates that passed Stage 1 relevance.
        threshold: Optional override for sufficiency threshold (defaults to settings.RAG_SUFFICIENCY_THRESHOLD).

    Returns:
        bool indicating if evidence set is sufficient for generation.
    """
    suf_threshold = threshold if threshold is not None else settings.RAG_SUFFICIENCY_THRESHOLD
    if not relevant_candidates:
        return False

    top_score = max(c.get("score", 0.0) for c in relevant_candidates)
    passed = top_score >= suf_threshold

    logger.info(f"RAG Stage 2 Sufficiency Gate: top_score={top_score:.4f}, threshold={suf_threshold}. Passed={passed}.")
    return passed


def retrieve_and_evaluate_evidence(
    user_id: str,
    document_id: str,
    question: str,
    top_k: int = 5,
    relevance_threshold: Optional[float] = None,
    sufficiency_threshold: Optional[float] = None,
    client: Optional[QdrantClient] = None
) -> Dict[str, Any]:
    """
    Executes end-to-end RAG evidence retrieval & two-stage gating pipeline:
    1. Embeds question using Multilingual-E5 (query: prefix).
    2. Queries Qdrant with mandatory user_id & document_id scoping.
    3. Evaluates Stage 1 Relevance Gate.
    4. Evaluates Stage 2 Sufficiency Gate.
    5. Returns validated evidence set or controlled no-answer decision.

    Args:
        user_id: Mandatory owner user ID string.
        document_id: Mandatory target document ID string.
        question: User query question string.
        top_k: Candidate retrieval limit.
        relevance_threshold: Optional threshold override for Stage 1.
        sufficiency_threshold: Optional threshold override for Stage 2.
        client: Optional QdrantClient instance.

    Returns:
        Dict containing gating results, evidence set, or no-answer decision reason.
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id is MANDATORY for ownership-scoped RAG retrieval.")
    if not document_id or not document_id.strip():
        raise ValueError("document_id is MANDATORY for ownership-scoped RAG retrieval.")
    if not question or not question.strip():
        raise ValueError("Question string cannot be empty.")

    if client is None:
        client = get_qdrant_client()

    # Ensure Qdrant collection exists before querying
    ensure_collection_exists(client)

    # 1. Embed question using Multilingual-E5 query prefixing
    query_vector = generate_query_embedding(question)

    # 2. Ownership-scoped Qdrant retrieval (hard-filtered by user_id and document_id)
    candidates = query_clauses_scoped(
        user_id=user_id,
        document_id=document_id,
        query_vector=query_vector,
        top_k=top_k,
        client=client
    )

    if not candidates:
        logger.info(f"Qdrant returned 0 candidate points for doc '{document_id}', user '{user_id}'. Controlled no-answer.")
        return {
            "has_sufficient_evidence": False,
            "relevance_gate_passed": False,
            "sufficiency_gate_passed": False,
            "no_answer_reason": "No document clauses were retrieved for this document.",
            "validated_evidence": [],
            "user_id": user_id,
            "document_id": document_id,
            "question": question,
            "schema_version": SCHEMA_VERSION
        }

    # 3. Stage 1 — Relevance Evaluation
    rel_passed, relevant_candidates = evaluate_relevance_stage(candidates, threshold=relevance_threshold)
    if not rel_passed:
        logger.info(f"RAG Stage 1 Relevance Gate FAILED for doc '{document_id}'. Controlled no-answer.")
        return {
            "has_sufficient_evidence": False,
            "relevance_gate_passed": False,
            "sufficiency_gate_passed": False,
            "no_answer_reason": "No relevant document clauses matched the question above the relevance threshold.",
            "validated_evidence": [],
            "user_id": user_id,
            "document_id": document_id,
            "question": question,
            "schema_version": SCHEMA_VERSION
        }

    # 4. Stage 2 — Sufficiency Evaluation
    suf_passed = evaluate_sufficiency_stage(relevant_candidates, threshold=sufficiency_threshold)
    if not suf_passed:
        logger.info(f"RAG Stage 2 Sufficiency Gate FAILED for doc '{document_id}'. Controlled no-answer.")
        return {
            "has_sufficient_evidence": False,
            "relevance_gate_passed": True,
            "sufficiency_gate_passed": False,
            "no_answer_reason": "Retrieved evidence is insufficient to answer the question reliably.",
            "validated_evidence": [],
            "user_id": user_id,
            "document_id": document_id,
            "question": question,
            "schema_version": SCHEMA_VERSION
        }

    # 5. Both Gates Passed: Format validated evidence set
    validated_evidence = [
        {
            "clause_id": cand.get("clause_id"),
            "position": cand.get("position"),
            "text": cand.get("text", cand.get("original_text", "")),
            "original_text": cand.get("original_text", ""),
            "severity": cand.get("severity", "Safe"),
            "categories": cand.get("categories", []),
            "score": cand.get("score", 0.0)
        }
        for cand in relevant_candidates
    ]

    logger.info(f"RAG Pipeline SUCCESS: {len(validated_evidence)} validated evidence clauses ready for LLM generation.")
    return {
        "has_sufficient_evidence": True,
        "relevance_gate_passed": True,
        "sufficiency_gate_passed": True,
        "no_answer_reason": None,
        "validated_evidence": validated_evidence,
        "user_id": user_id,
        "document_id": document_id,
        "question": question,
        "schema_version": SCHEMA_VERSION
    }
