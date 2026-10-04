"""
Unit Tests for Workstream 8 (W8): Executive Overview and Report Renderer
Validates that executive overview sections, key figures, risk profile counts,
and clause card formatting adhere strictly to the ground-truth specification.
"""

import pytest
from app.services.summarization_service import generate_document_executive_summary


def test_w8_executive_overview_consistency():
    """Verify overview risk counts match clause array exactly."""
    clauses = [
        {"position": 1, "clause_number": "1", "title": "Indemnity", "severity": "High", "text": "Customer shall defend..."},
        {"position": 2, "clause_number": "2", "title": "Termination", "severity": "High", "text": "Vendor may terminate at will..."},
        {"position": 3, "clause_number": "3", "title": "Payment", "severity": "Moderate", "text": "Due in 15 days..."},
        {"position": 4, "clause_number": "4", "title": "Confidentiality", "severity": "Low", "text": "3 years..."},
        {"position": 5, "clause_number": "5", "title": "Governing Law", "severity": "Low", "text": "Delaware law..."}
    ]

    res = generate_document_executive_summary(
        full_document_text="Master Services Agreement between Vendor and Customer.",
        clauses=clauses
    )

    assert res["success"] is True
    counts = res["risk_counts"]
    total_counted = counts["HIGH"] + counts["MEDIUM"] + counts["LOW"] + counts["REVIEW"]
    assert total_counted == len(clauses)
    assert counts["HIGH"] == 2
    assert counts["MEDIUM"] == 1
    assert counts["LOW"] == 2
    assert counts["REVIEW"] == 0
