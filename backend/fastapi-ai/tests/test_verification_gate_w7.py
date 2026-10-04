"""
Unit Tests for Workstream 7 (W7): Claim-Level Verification Gate & Document-Level Gap Analysis
Validates claim-level provenance verification, directionality checking,
and detection of document drafting issues (double negatives, dangling cross-references,
questionable legal citations, missing standard clauses, blank signatures, pre-printed ratings).
"""

import pytest
from app.services.claim_grounding_service import verify_clause_claims, detect_document_level_gaps
from app.services.summarization_service import generate_document_executive_summary


def test_w7_claim_verification_grounded():
    """Verify that a factually grounded clause passes verification."""
    clause = {
        "clause_number": "2",
        "title": "FEES AND PAYMENT TERMS",
        "category": "Payment",
        "original_text": "Client shall pay all undisputed invoices within forty-five (45) days of the invoice date. Past due balances shall accrue interest at 2.0% per month.",
        "plain_language": "Client shall pay all undisputed invoices within 45 days of invoice date; past due balances incur interest at 2.0% per month.",
        "who_is_bound": "Client only"
    }

    res = verify_clause_claims(clause)
    assert res["verified"] is True
    assert len(res["unsupported_claims"]) == 0
    assert res["status"] == "ok"


def test_w7_claim_verification_ungrounded_number():
    """Verify that a clause containing fabricated numbers fails verification."""
    clause = {
        "clause_number": "2",
        "title": "FEES AND PAYMENT TERMS",
        "category": "Payment",
        "original_text": "Client shall pay all undisputed invoices within forty-five (45) days of the invoice date.",
        "plain_language": "Client shall pay within 30 days of receipt with a $500 penalty.",
        "who_is_bound": "Client only"
    }

    res = verify_clause_claims(clause)
    assert res["verified"] is False
    assert len(res["unsupported_claims"]) > 0
    assert any("30 days" in c or "$500" in c for c in res["unsupported_claims"])
    assert res["status"] == "analysis_incomplete"


def test_w7_document_gaps_contract_d_msa():
    """Verify document-level analysis detects all drafting gaps and issues in Contract D (MSA)."""
    msa_text = """
    MASTER SERVICES AGREEMENT - ENTERPRISE CLOUD SERVICES
    Reference: DOC-MSA-2026-ENT-001
    Overall Risk Classification: HIGH RISK (Automated Audit Score: 84/100)
    
    1. CUSTOMER INDEMNIFICATION: Customer shall defend, indemnify, and hold harmless Vendor...
    2. TERMINATION FOR CONVENIENCE: Vendor reserves the right to suspend or terminate immediately for any reason or no reason without refund of prepaid fees...
    3. TERM AND RENEWAL: auto-renews for successive 12-month periods unless 60 days notice... Vendor may increase fees by up to 15%...
    4. INVOICING: due within 15 days... 1.5% per month compounded monthly...
    5. CONFIDENTIALITY: 3 years following disclosure...
    6. IP AND TELEMETRY: perpetual, irrevocable, royalty-free worldwide license to operational usage telemetry...
    7. PRIVACY: GDPR and CCPA...
    8. ARBITRATION: Delaware law, American Arbitration Association...
    9. CROSS-BORDER TARIFFS: referenced in Annex IV, dynamically negotiated under UNCITRAL Article 79, subject to force majeure of Section 7.2.
    
    IN WITNESS WHEREOF:
    CloudScale Technologies, Inc.      Enterprise Solutions Global Ltd.
    By: ___________________________    By: ___________________________
    Marcus Vance, Chief Legal Officer   Sarah Jenkins, VP Global Procurement
    """

    clauses = [
        {"clause_number": "1", "category": "Indemnification", "text": "Customer shall defend, indemnify..."},
        {"clause_number": "2", "category": "Termination", "text": "Vendor reserves the right to suspend or terminate..."},
        {"clause_number": "3", "category": "Renewal", "text": "auto-renews for successive 12-month periods..."},
        {"clause_number": "4", "category": "Payment", "text": "due within 15 days..."},
        {"clause_number": "5", "category": "Confidentiality", "text": "3 years following disclosure..."},
        {"clause_number": "6", "category": "Intellectual Property", "text": "perpetual, irrevocable license to telemetry..."},
        {"clause_number": "7", "category": "Privacy", "text": "GDPR and CCPA..."},
        {"clause_number": "8", "category": "Dispute Resolution", "text": "American Arbitration Association..."},
        {"clause_number": "9", "category": "General / Boilerplate", "text": "Annex IV, UNCITRAL Article 79, Section 7.2 force majeure..."}
    ]

    gaps = detect_document_level_gaps(msa_text, clauses)

    # 1. Check dangling cross-references
    assert any("Annex IV" in g for g in gaps)
    assert any("Section 7.2" in g for g in gaps)

    # 2. Check mis-cited CISG provision
    assert any("UNCITRAL Article 79" in g for g in gaps)

    # 3. Check pre-printed rating ignored
    assert any("Overall Risk Classification" in g or "claimed in document" in g for g in gaps)

    # 4. Check missing liability cap & reciprocal rights
    assert any("limitation of liability cap" in g.lower() for g in gaps)
    assert any("Vendor indemnity" in g for g in gaps)
    assert any("reciprocal termination right" in g for g in gaps)

    # 5. Check arbitration missing seat/rules
    assert any("Arbitration clause lacks" in g for g in gaps)

    # 6. Check blank signatures
    assert any("Signature blocks are blank" in g for g in gaps)


def test_w7_document_gaps_contract_b_double_negative():
    """Verify document-level analysis detects double negative in Contract B."""
    b_text = "Neither party shall not exceed aggregate liability of $50,000."
    gaps = detect_document_level_gaps(b_text, [])
    assert any("double negative" in g.lower() for g in gaps)
