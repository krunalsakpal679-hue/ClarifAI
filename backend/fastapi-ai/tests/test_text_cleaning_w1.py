"""
Unit Tests for Workstream 1 (W1): Text Cleaning, Page Furniture Stripping & Header Extraction
"""

import pytest
from app.services.text_cleaning_service import (
    clean_legal_text,
    extract_structured_document_header,
    rejoin_hard_wrapped_paragraphs
)


def test_w1_strip_running_headers_and_footers():
    raw_text = (
        "MASTER SERVICES AGREEMENT\n\n"
        "ClarifAI Demo Legal Document Repository - Confidential & Proprietary\n"
        "Page 1 of 5\n\n"
        "This Agreement is entered into between Vendor Corp (\"Vendor\") and Customer LLC (\"Customer\").\n"
        "Page 2 of 5\n"
        "All Rights Reserved\n"
    )
    res = clean_legal_text(raw_text)
    assert res["success"] is True
    assert "ClarifAI Demo Legal Document Repository" not in res["cleaned_text"]
    assert "Page 1 of 5" not in res["cleaned_text"]
    assert "Page 2 of 5" not in res["cleaned_text"]
    assert len(res["page_furniture"]) >= 3


def test_w1_rejoin_hard_wrapped_paragraphs():
    raw_text = (
        "Customer shall remit payment for all undisputed\n"
        "invoices within forty-five (45) days of the invoice\n"
        "date without offset or deduction."
    )
    res = clean_legal_text(raw_text)
    expected = "Customer shall remit payment for all undisputed invoices within forty-five (45) days of the invoice date without offset or deduction."
    assert res["cleaned_text"] == expected


def test_w1_header_extraction_with_claimed_risk_rating():
    raw_text = (
        "MASTER SERVICES AGREEMENT\n"
        "Document ID: DOC-MSA-2026-ENT-001\n"
        "Governing Law: State of Delaware, United States\n"
        "Effective Date: September 12, 2026\n"
        "Overall Risk Classification: HIGH RISK (Automated Audit Score: 84/100)\n\n"
        "This Agreement is by and between CloudScale Technologies, Inc. (\"Vendor\") and Enterprise Solutions Global Ltd. (\"Customer\").\n\n"
        "Section 1. SERVICES\n"
        "Vendor will provide enterprise services."
    )
    res = clean_legal_text(raw_text)
    header = res["document_header"]

    assert header["reference_number"] == "DOC-MSA-2026-ENT-001"
    assert "Delaware" in header["governing_law_line"]
    assert header["effective_date"] == "September 12, 2026"
    assert header["claimed_in_document"]["risk_rating"] == "HIGH RISK"
    assert header["claimed_in_document"]["audit_score"] == "84/100"
    
    party_roles = {p["role"].lower(): p["name"] for p in header["parties"]}
    assert "vendor" in party_roles
    assert "customer" in party_roles
    assert "CloudScale Technologies" in party_roles["vendor"]
    assert "Enterprise Solutions Global" in party_roles["customer"]


def test_w1_ocr_normalization():
    raw_text = (
        "Section 6. TOTAL CASUALTY LOSS AND FEPLACEMENTVALUE\n"
        "Lessee shall maintain INOENITY coverage AWO casualty insurance."
    )
    res = clean_legal_text(raw_text)
    assert "REPLACEMENT VALUE" in res["cleaned_text"]
    assert "INDEMNITY" in res["cleaned_text"]
    assert "AND" in res["cleaned_text"]
