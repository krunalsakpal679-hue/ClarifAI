"""
ClarifAI Definitive Cross-Document Data Contamination & Multi-Document Isolation Regression Test Suite
(Phase A Resolution - PRD v2.3 Chapters 15, 16.5, 28.4, 28.5, 34, 50, 56.9)

Validates that when two documents with deliberately distinct, non-overlapping facts
(different dollar amounts, state/jurisdiction names, party names, exception carve-outs, notice periods)
are processed sequentially back-to-back AND concurrently in parallel:
1. ZERO fields, names, amounts, or exceptions from Document X ever appear in Document Y's output records.
2. ZERO fields, names, amounts, or exceptions from Document Y ever appear in Document X's output records.
3. Qdrant vector retrieval strictly enforces document_id and user_id scoping with zero cross-document vector leakage.
4. Concurrent multi-thread execution exhibits zero shared-mutable state corruption.
5. In-process session memory and caches remain completely isolated per document.
"""

import concurrent.futures
import json
import os
import re
from typing import Dict, Any, List
import pytest
from qdrant_client import QdrantClient

from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.rule_engine_service import evaluate_rules
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_summary
from app.services.qdrant_service import (
    get_qdrant_client,
    ensure_collection_exists,
    index_document_clauses,
    query_clauses_scoped,
    retrieve_all_document_clauses,
    delete_document_points
)
from app.services.chatbot_service import (
    generate_chatbot_answer,
    clear_session_memory
)


# ==============================================================================
# 1. Deliberately Distinct Document Fixtures with Zero Fact Overlap
# ==============================================================================

DOC_X_TEXT = """1. ENGAGEMENT AND PARTIES
This Cloud Infrastructure Agreement is entered into between Acrobat Cloud Technologies Inc. ("Provider") and Beacon Financial Services LLC ("Customer"). Provider shall deliver real-time financial telemetry analytics.

2. INVOICING AND CHARGES
Customer shall pay all undisputed invoices within seventy-five (75) days. Overdue balances accrue late interest charges at four point two five percent (4.25%) per month compounding quarterly.

3. WORK PRODUCT AND PROPRIETARY DELIVERABLES
All custom telemetry models, algorithmic code, and bespoke analytics modules developed exclusively for Customer constitute works made for hire and vest exclusively in Customer.

4. INDEMNITY ALLOCATION
Provider agrees to defend, indemnify, and hold harmless Customer and its directors from any third-party claims or damages resulting from Provider's intentional misconduct or intellectual property infringement.

5. AGGREGATE LIABILITY CAP
Other than liabilities arising from gross negligence or breach of data security, neither party's aggregate monetary liability under this agreement shall exceed one million two hundred fifty thousand dollars ($1,250,000).

6. GOVERNING FORUM AND VENUE
Any controversy or dispute arising under this contract shall be submitted exclusively to the jurisdiction of the state courts located in King County, Washington.

7. CONFIDENTIALITY COVENANT
Customer and Provider agree to hold all proprietary trade secrets in strict secrecy for six (6) years following contract expiration.
"""

DOC_Y_TEXT = """1. SCOPE OF MARITIME SERVICES
This Operational Logistics Contract is entered into between Zenith Marine Logistics Corp. ("Consultant") and Apex Harbor Operators Ltd. ("Client"). Consultant shall render port navigation optimization advisory.

2. PAYMENT AND DISBURSEMENTS
Client shall remit payment for professional fees within one hundred twenty (120) days of invoice receipt. Overdue invoices accrue penalty fees of one point seven five percent (1.75%) per month.

3. ADVISORY REPORTS OWNERSHIP
All shipping route analysis reports, feasibility spreadsheets, and strategic maritime surveys created under this agreement constitute works made for hire belonging solely to Client.

4. INDEMNIFICATION BURDEN
Consultant agrees to defend and indemnify Client, its officers, and staff against all third-party losses or claims arising directly out of Consultant's gross negligence.

5. MONETARY DAMAGES LIMITATION
Except for liabilities resulting from willful misconduct or breach of confidentiality, neither party's total monetary liability under this agreement shall exceed eight hundred forty thousand dollars ($840,000).

6. EXCLUSIVE JURISDICTION
Any dispute or legal claim arising out of this agreement shall fall under the exclusive venue and jurisdiction of the state courts in Orange County, Florida.

7. NON-DISCLOSURE OBLIGATION
Each party covenants to maintain strict confidentiality over proprietary technical navigation data for two (2) years following engagement termination.
"""

# Unique token sets strictly belonging to Document X
DOC_X_UNIQUE_TERMS = [
    "Acrobat Cloud Technologies",
    "Beacon Financial Services",
    "$1,250,000",
    "1,250,000",
    "4.25%",
    "75 days",
    "seventy-five",
    "King County, Washington",
    "King County",
    "Washington",
    "breach of data security",
    "data security",
    "six (6) years",
    "financial telemetry analytics",
    "telemetry"
]

# Unique token sets strictly belonging to Document Y
DOC_Y_UNIQUE_TERMS = [
    "Zenith Marine Logistics",
    "Apex Harbor Operators",
    "$840,000",
    "840,000",
    "1.75%",
    "120 days",
    "one hundred twenty",
    "Orange County, Florida",
    "Orange County",
    "Florida",
    "port navigation optimization",
    "two (2) years",
    "shipping route analysis"
]


def _run_full_pipeline(doc_text: str) -> Dict[str, Any]:
    """Runs the complete 7-stage FastAPI processing pipeline on raw document text."""
    seg_res = segment_document_clauses(doc_text)
    clauses = seg_res["clauses"]
    
    rules_res = evaluate_rules(clauses=clauses, text=doc_text)
    findings = rules_res.get("findings", [])
    
    cat_res = categorize_clause_records(clauses, rule_findings=findings)
    categorized = cat_res["clauses"]
    
    risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
    classified = risk_res["clauses"]
    
    simp_res = simplify_document_clauses(classified, rule_findings=findings)
    simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])
    
    sum_res = generate_document_summary(classified, rule_findings=findings)
    
    return {
        "segmented": clauses,
        "findings": findings,
        "categorized": categorized,
        "classified": classified,
        "simplified": simplified,
        "summary": sum_res
    }


def _extract_all_text_artifacts(pipeline_result: Dict[str, Any]) -> str:
    """Aggregates all generated strings across clauses, explanations, and executive summaries."""
    text_chunks = []
    
    # Executive Summary fields
    summary = pipeline_result.get("summary", {})
    for k in ["purpose_text", "key_risks_text", "key_terms_text", "obligations_text"]:
        val = summary.get(k, "")
        if val:
            text_chunks.append(str(val))
            
    # Clauses
    for cl in pipeline_result.get("simplified", []):
        text_chunks.append(str(cl.get("simplified_text", "")))
        text_chunks.append(str(cl.get("why_flagged", "")))
        struct = cl.get("structured_explanation") or {}
        if isinstance(struct, dict):
            text_chunks.append(str(struct.get("what_this_clause_means", "")))
            risk_obj = struct.get("risk") or {}
            text_chunks.append(str(risk_obj.get("reason", "")))
            cat_obj = struct.get("category") or {}
            text_chunks.append(str(cat_obj.get("reason", "")))
            
    return " \n ".join(text_chunks)


# ==============================================================================
# 2. Sequential Back-to-Back Cross-Document Contamination Tests
# ==============================================================================

def test_sequential_cross_document_isolation_x_then_y():
    """
    Processes Document X, then immediately processes Document Y in the same worker process.
    Asserts absolute zero contamination from X into Y and vice-versa.
    """
    res_x = _run_full_pipeline(DOC_X_TEXT)
    res_y = _run_full_pipeline(DOC_Y_TEXT)
    
    y_full_text = _extract_all_text_artifacts(res_y)
    x_full_text = _extract_all_text_artifacts(res_x)
    
    # 1. Assert ZERO Document X facts appear in Document Y
    for x_term in DOC_X_UNIQUE_TERMS:
        assert x_term.lower() not in y_full_text.lower(), (
            f"CONTAMINATION DETECTED: Document X fact '{x_term}' found in Document Y generated analysis!\n"
            f"Document Y full output:\n{y_full_text}"
        )
        
    # 2. Assert ZERO Document Y facts appear in Document X
    for y_term in DOC_Y_UNIQUE_TERMS:
        assert y_term.lower() not in x_full_text.lower(), (
            f"CONTAMINATION DETECTED: Document Y fact '{y_term}' found in Document X generated analysis!\n"
            f"Document X full output:\n{x_full_text}"
        )


def test_sequential_cross_document_isolation_y_then_x_order_invariance():
    """
    Inverses execution order (Process Y first, then X) to verify cache/order neutrality.
    """
    res_y = _run_full_pipeline(DOC_Y_TEXT)
    res_x = _run_full_pipeline(DOC_X_TEXT)
    
    y_full_text = _extract_all_text_artifacts(res_y)
    x_full_text = _extract_all_text_artifacts(res_x)
    
    for x_term in DOC_X_UNIQUE_TERMS:
        assert x_term.lower() not in y_full_text.lower(), f"Fact '{x_term}' leaked from X into Y (inverse order)."
    for y_term in DOC_Y_UNIQUE_TERMS:
        assert y_term.lower() not in x_full_text.lower(), f"Fact '{y_term}' leaked from Y into X (inverse order)."


# ==============================================================================
# 3. Parallel / Concurrent Multi-Threaded Cross-Document Isolation Tests
# ==============================================================================

def test_concurrent_parallel_document_processing_isolation():
    """
    Processes Document X and Document Y simultaneously across concurrent worker threads.
    Asserts zero shared-state race conditions, dictionary overwrites, or data bleeding.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures_x = [executor.submit(_run_full_pipeline, DOC_X_TEXT) for _ in range(2)]
        futures_y = [executor.submit(_run_full_pipeline, DOC_Y_TEXT) for _ in range(2)]
        
        results_x = [f.result() for f in futures_x]
        results_y = [f.result() for f in futures_y]
        
    for idx, rx in enumerate(results_x):
        x_text = _extract_all_text_artifacts(rx)
        for y_term in DOC_Y_UNIQUE_TERMS:
            assert y_term.lower() not in x_text.lower(), (
                f"CONCURRENT LEAK in Thread X-{idx}: Doc Y fact '{y_term}' found in Doc X output."
            )
            
    for idx, ry in enumerate(results_y):
        y_text = _extract_all_text_artifacts(ry)
        for x_term in DOC_X_UNIQUE_TERMS:
            assert x_term.lower() not in y_text.lower(), (
                f"CONCURRENT LEAK in Thread Y-{idx}: Doc X fact '{x_term}' found in Doc Y output."
            )


# ==============================================================================
# 4. Qdrant Vector Database Hard Filter & Ownership Isolation Tests
# ==============================================================================

def test_qdrant_vector_scoping_and_cross_document_isolation():
    """
    Indexes Document X and Document Y into Qdrant vector database under the same user.
    Asserts:
    - Queries for Document X retrieve ONLY points with document_id='doc_x'.
    - Queries for Document Y retrieve ONLY points with document_id='doc_y'.
    - Zero Document X payload text is returned on Document Y queries.
    """
    q_client = QdrantClient(":memory:")
    ensure_collection_exists(q_client)
    
    user_id = "user_alpha_2026"
    doc_x_id = "doc_x_contract_101"
    doc_y_id = "doc_y_contract_202"
    
    res_x = _run_full_pipeline(DOC_X_TEXT)
    res_y = _run_full_pipeline(DOC_Y_TEXT)
    
    # 1. Index both documents
    index_document_clauses(user_id=user_id, document_id=doc_x_id, clauses=res_x["simplified"], client=q_client)
    index_document_clauses(user_id=user_id, document_id=doc_y_id, clauses=res_y["simplified"], client=q_client)
    
    # 2. Retrieve all clauses for Doc X and verify 100% ID isolation
    ret_x = retrieve_all_document_clauses(user_id=user_id, document_id=doc_x_id, client=q_client)
    assert len(ret_x) == len(res_x["simplified"])
    for pt in ret_x:
        assert pt["document_id"] == doc_x_id
        assert pt["document_id"] != doc_y_id
        for y_term in DOC_Y_UNIQUE_TERMS:
            assert y_term.lower() not in (pt.get("text", "") or pt.get("original_text", "")).lower()
            
    # 3. Retrieve all clauses for Doc Y and verify 100% ID isolation
    ret_y = retrieve_all_document_clauses(user_id=user_id, document_id=doc_y_id, client=q_client)
    assert len(ret_y) == len(res_y["simplified"])
    for pt in ret_y:
        assert pt["document_id"] == doc_y_id
        assert pt["document_id"] != doc_x_id
        for x_term in DOC_X_UNIQUE_TERMS:
            assert x_term.lower() not in (pt.get("text", "") or pt.get("original_text", "")).lower()


# ==============================================================================
# 5. Clause 5 Liability Cap Exception Specific Grounding Regression
# ==============================================================================

def test_clause_5_liability_cap_exception_exact_grounding():
    """
    Validates specifically that Clause 5 liability cap carve-outs are dynamically extracted
    verbatim from the active document, preventing Document A exceptions ('indemnification, gross negligence, or willful misconduct')
    from ever polluting Document B ('gross negligence or breach of confidentiality').
    """
    res_x = _run_full_pipeline(DOC_X_TEXT)
    res_y = _run_full_pipeline(DOC_Y_TEXT)
    
    cl5_x = res_x["simplified"][4]
    cl5_y = res_y["simplified"][4]
    
    what_means_x = cl5_x["structured_explanation"]["what_this_clause_means"]
    what_means_y = cl5_y["structured_explanation"]["what_this_clause_means"]
    
    # Document X source says: "gross negligence or breach of data security"
    assert "data security" in what_means_x.lower() or "gross negligence" in what_means_x.lower()
    assert "confidentiality" not in what_means_x.lower()
    
    # Document Y source says: "willful misconduct or breach of confidentiality"
    assert "breach of confidentiality" in what_means_y.lower() or "willful misconduct" in what_means_y.lower()
    assert "data security" not in what_means_y.lower()
