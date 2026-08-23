"""
ClarifAI Multilingual Embedding Service Module
Handles dense vector embedding generation for clause storage in Qdrant,
RAG chatbot retrieval, and pairwise document comparison similarity.
Configured per PRD v2.3 Chapters 28.1, 28.4, 28.5, and Chapter 50.

NOTE: Uses base 'intfloat/multilingual-e5-base' as an interim placeholder.
The fine-tuned checkpoint source/URL is IMPLEMENTATION DECISION REQUIRED.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default interim model checkpoint per PRD instruction
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
    
    Args:
        text: Original clause text string.
        
    Returns:
        List of floats representing 768-dimensional embedding vector.
    """
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
    model = get_embedding_model()
    # E5 specification requirement: Prefix query with 'query: '
    formatted_query = f"query: {query.strip()}"
    embedding = model.encode(formatted_query, convert_to_numpy=True)
    return embedding.tolist()


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
            "chunking_strategy": "Direct clause-level embedding without chunking (<=512 tokens)"
        }
    except Exception as e:
        logger.error(f"Embedding status check failed: {e}")
        return {
            "loaded": False,
            "model_name": model_name,
            "error": str(e)
        }
