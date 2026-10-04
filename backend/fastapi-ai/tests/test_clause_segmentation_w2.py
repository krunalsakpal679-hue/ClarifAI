"""
Unit Tests for Workstream 2 (W2): Strict Structural Clause Segmentation
"""

import pytest
from app.services.clause_segmentation_service import segment_document_clauses


def test_w2_no_mid_sentence_heading_split():
    raw_text = (
        "This Agreement governs consulting services.\n\n"
        "Section 1. ENGAGEMENT\n"
        "Consultant will render advisory services. Customer desires to retain Vendor for ongoing cloud services.\n"
        "(a) Consultant shall deliver reports.\n"
        "(b) Consultant shall maintain records.\n\n"
        "Section 2. PAYMENT\n"
        "Invoices are payable within 30 days."
    )
    res = segment_document_clauses(raw_text)
    assert res["success"] is True
    assert res["total_clauses"] == 2
    assert res["clauses"][0]["clause_number"] == "1"
    assert res["clauses"][0]["title"] == "ENGAGEMENT"
    assert "(a) Consultant shall deliver reports." in res["clauses"][0]["text"]
    assert "(b) Consultant shall maintain records." in res["clauses"][0]["text"]
    assert res["clauses"][1]["clause_number"] == "2"
    assert res["clauses"][1]["title"] == "PAYMENT"


def test_w2_header_metadata_isolated_from_clauses():
    raw_text = (
        "MASTER SERVICES AGREEMENT\n"
        "Document ID: DOC-MSA-2026-ENT-001\n"
        "Governing Law: State of Delaware, United States\n"
        "Effective Date: September 12, 2026\n"
        "Overall Risk Classification: HIGH RISK (Automated Audit Score: 84/100)\n\n"
        "WHEREAS, Customer desires to procure cloud services from Vendor;\n"
        "NOW, THEREFORE, the Parties agree as follows:\n\n"
        "Section 1. CUSTOMER INDEMNIFICATION AND THIRD-PARTY DEFENSE\n"
        "Customer shall indemnify and defend Vendor.\n\n"
        "Section 2. TERMINATION FOR CONVENIENCE AND SUSPENSION\n"
        "Vendor may terminate immediately without refund."
    )
    res = segment_document_clauses(raw_text)
    assert res["success"] is True
    assert res["total_clauses"] == 2
    assert res["clauses"][0]["clause_number"] == "1"
    assert res["clauses"][0]["title"] == "CUSTOMER INDEMNIFICATION AND THIRD-PARTY DEFENSE"
    assert res["clauses"][1]["clause_number"] == "2"
    assert res["clauses"][1]["title"] == "TERMINATION FOR CONVENIENCE AND SUSPENSION"
    assert "Document ID" not in res["clauses"][0]["text"]
    assert res["document_header"] is not None
    assert res["recitals"] is not None


def test_w2_exact_clause_counts_contracts_a_b_c():
    from app.services.pdf_service import extract_pdf_text_service
    from app.services.text_cleaning_service import clean_legal_text
    from pathlib import Path

    # Contract A
    pdf_a = Path("sample_documents/Sample_Cloud_Consulting_Agreement.pdf").read_bytes()
    clean_a = clean_legal_text(extract_pdf_text_service(pdf_a, "A.pdf")["full_text"])["cleaned_text"]
    res_a = segment_document_clauses(clean_a)
    assert res_a["total_clauses"] == 12

    # Contract B
    pdf_b = Path("sample_documents/Document_B_Consulting_Services_Agreement.pdf").read_bytes()
    clean_b = clean_legal_text(extract_pdf_text_service(pdf_b, "B.pdf")["full_text"])["cleaned_text"]
    res_b = segment_document_clauses(clean_b)
    assert res_b["total_clauses"] == 7

    # Contract C
    pdf_c = Path("sample_documents/Sample_Commercial_Lease_Agreement.pdf").read_bytes()
    clean_c = clean_legal_text(extract_pdf_text_service(pdf_c, "C.pdf")["full_text"])["cleaned_text"]
    res_c = segment_document_clauses(clean_c)
    assert res_c["total_clauses"] == 7
