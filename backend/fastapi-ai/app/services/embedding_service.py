"""
ClarifAI Multilingual Embedding Service Module (AI-PHASE-EMBEDDINGS)
Handles dense vector embedding generation for clause storage in Qdrant,
RAG chatbot retrieval, and pairwise document comparison similarity.
Configured per PRD v2.3 Chapters 28.1, 28.4, 28.5, and Chapter 50.

Uses approved Multilingual-E5 model ('intfloat/multilingual-e5-base') per Decision R-05.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from app.models.common import SCHEMA_VERSION

logger = logging.getLogger(__name__)

# Default interim model checkpoint per PRD instruction (Decision R-05)
DEFAULT_EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-base"

# Documented chunking strategy constant:
# Clauses are embedded directly without chunking because average clause length (50-300 tokens)
# fits well within Multilingual-E5's maximum sequence length of 512 tokens.
MAX_SEQUENCE_LENGTH: int = 512

_model_instance: Optional[SentenceTransformer] = None


def get_embedding_model_name() -> str:
    """
    Returns configured embedding model identifier from EMBEDDING_MODEL_NAME environment variable.
    """
    return os.getenv("EMBEDDING_MODEL_NAME", DEFAULT_EMBEDDING_MODEL_NAME)


def get_embedding_model() -> SentenceTransformer:
    """
    Lazy loads and returns singleton instance of SentenceTransformer embedding model.
    """
    global _model_instance
    if _model_instance is None:
        model_name = get_embedding_model_name()
        logger.info(f"Loading embedding model '{model_name}'...")
        _model_instance = SentenceTransformer(model_name)
    return _model_instance


def get_embedding_dimension() -> int:
    """
    Returns actual vector dimension produced by loaded embedding model.
    For intfloat/multilingual-e5-base, dimension is 768.
    """
    model = get_embedding_model()
    if hasattr(model, "get_embedding_dimension"):
        return model.get_embedding_dimension()
    return model.get_sentence_embedding_dimension()


def generate_clause_embedding(text: str) -> List[float]:
    """
    Generates dense vector embedding for a contract clause or document passage.
    Applies Multilingual-E5 required 'passage: ' prefix.
    Embedded text field choice: original_text / text for fidelity to source.

    Args:
        text: Original clause text string.

    Returns:
        List of floats representing 768-dimensional embedding vector.
    """
    if not text or not text.strip():
        raise ValueError("Input clause text for embedding generation must not be empty.")

    model = get_embedding_model()
    # E5 specification requirement: Prefix text with 'passage: '
    formatted_text = f"passage: {text.strip()}"
    embedding = model.encode(formatted_text, convert_to_numpy=True)
    return embedding.tolist()


def generate_query_embedding(query: str) -> List[float]:
    """
    Generates dense vector embedding for a chatbot user query.
    Applies Multilingual-E5 required 'query: ' prefix.

    Args:
        query: User question string.

    Returns:
        List of floats representing 768-dimensional query vector.
    """
    if not query or not query.strip():
        raise ValueError("Input query text for embedding generation must not be empty.")

    model = get_embedding_model()
    # E5 specification requirement: Prefix query with 'query: '
    formatted_query = f"query: {query.strip()}"
    embedding = model.encode(formatted_query, convert_to_numpy=True)
    return embedding.tolist()


def generate_document_clause_embeddings(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates dense vector embeddings for a list of document clauses with per-clause failure isolation
    and shared failure handling (Chapter 16.5).

    Args:
        clauses: List of clause dict items.

    Returns:
        List of clause dict items augmented with 'embedding' vector and 'embedding_status'.
    """
    dim = get_embedding_dimension()
    embedded_clauses = []

    for clause in clauses:
        clause_id = clause.get("clause_id", clause.get("position", "unknown"))
        # Documented text choice: original_text preferred for fidelity to source, fallback to text
        raw_text = clause.get("original_text") or clause.get("text", "")

        clause_item = dict(clause)
        if not raw_text or not raw_text.strip():
            logger.warning(f"Clause {clause_id} has empty text; marking embedding as FAILED.")
            clause_item["embedding"] = None
            clause_item["embedding_status"] = "FAILED"
            clause_item["embedding_error"] = "Empty clause text."
            embedded_clauses.append(clause_item)
            continue

        try:
            vector = generate_clause_embedding(raw_text)
            clause_item["embedding"] = vector
            clause_item["embedding_dimension"] = len(vector)
            clause_item["embedding_status"] = "SUCCESS"
            clause_item["embedding_error"] = None
        except Exception as exc:
            logger.error(f"Embedding generation failed for clause {clause_id}: {exc}")
            clause_item["embedding"] = None
            clause_item["embedding_status"] = "FAILED"
            clause_item["embedding_error"] = f"Embedding generation failed: {exc}"

        embedded_clauses.append(clause_item)

    return embedded_clauses


def get_embedding_status() -> Dict[str, Any]:
    """
    Returns diagnostic status of embedding model.
    """
    model_name = get_embedding_model_name()
    try:
        dim = get_embedding_dimension()
        return {
            "loaded": True,
            "model_name": model_name,
            "is_interim_placeholder": True,
            "fine_tuned_status": "IMPLEMENTATION DECISION REQUIRED",
            "vector_dimension": dim,
            "max_sequence_length": MAX_SEQUENCE_LENGTH,
            "chunking_strategy": "Direct clause-level embedding without chunking (<=512 tokens), prefixed with 'passage: '"
        }
    except Exception as e:
        logger.error(f"Embedding status check failed: {e}")
        return {
            "loaded": False,
            "model_name": model_name,
            "error": str(e)
        }
