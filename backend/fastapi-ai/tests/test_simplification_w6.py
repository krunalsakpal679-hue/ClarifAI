"""
Unit Tests for Workstream 6 (W6): Plain-Language Simplification & Summaries
Validates that clause summaries are extraction-first, grounded in verbatim clause text,
use real party names, correctly handle Contract D (MSA) and all contract categories,
and strictly omit banned placeholders and templates.
"""

import pytest
from app.services.simplification_service import (
    synthesize_detailed_plain_english_analysis,
    simplify_single_clause,
    simplify_document_clauses,
    check_for_legal_advice,
    check_for_prompt_injection_leak
)
from app.services.claim_grounding_service import check_banned_strings


def test_w6_contract_d_msa_synthesis():
    """Verify all 9 sections of Contract D (MSA) synthesize clean, grounded explanations."""
    msa_clauses = [
        {
            "position": 1,
            "clause_number": "1",
            "title": "CUSTOMER INDEMNIFICATION AND THIRD-PARTY DEFENSE",
            "category": "Indemnification",
            "text": "Customer shall defend, indemnify, and hold harmless Vendor, its affiliates, officers, directors, employees, and agents from and against any and all claims, demands, liabilities, damages, losses, costs, and expenses (including reasonable attorneys' fees) arising out of or related to Customer Data or Customer's use of the Services without limitation.",
            "severity": "High"
        },
        {
            "position": 2,
            "clause_number": "2",
            "title": "TERMINATION FOR CONVENIENCE AND SUSPENSION",
            "category": "Termination",
            "text": "Vendor reserves the right to suspend or terminate this Agreement immediately upon written notice for any reason or no reason, without refund of any prepaid fees and with no obligation to assist in data migration or service transition.",
            "severity": "High"
        },
        {
            "position": 3,
            "clause_number": "3",
            "title": "TERM, AUTOMATIC RENEWAL AND ANNUAL PRICE ESCALATION",
            "category": "Renewal",
            "text": "This Agreement shall automatically renew for successive twelve (12) month periods unless either party provides written notice of non-renewal at least sixty (60) days prior to the expiration of the then-current term. Vendor may increase fees by up to fifteen percent (15%) upon each renewal.",
            "severity": "Moderate"
        },
        {
            "position": 4,
            "clause_number": "4",
            "title": "INVOICING, PAYMENT TERMS AND LATE PAYMENT ACCRUALS",
            "category": "Payment",
            "text": "All invoices rendered by Vendor are due within fifteen (15) days of receipt. Past due amounts shall accrue interest at the maximum rate permitted by law or 1.5% per month, compounded monthly, plus all collection costs and reasonable legal fees.",
            "severity": "Moderate"
        },
        {
            "position": 5,
            "clause_number": "5",
            "title": "CONFIDENTIALITY AND TRADE SECRET PRESERVATION",
            "category": "Confidentiality",
            "text": "Each party shall maintain the confidentiality of all proprietary information for three (3) years following disclosure; provided, however, that trade secrets shall remain protected indefinitely. Disclosures required by court order are permitted with prior written notice.",
            "severity": "Low"
        },
        {
            "position": 6,
            "clause_number": "6",
            "title": "INTELLECTUAL PROPERTY AND TELEMETRY LICENSING",
            "category": "Intellectual Property",
            "text": "Vendor retains all right, title, and interest in and to the Platform, underlying algorithms, and documentation. Customer grants Vendor a perpetual, irrevocable, royalty-free, worldwide license to use, aggregate, and analyze anonymized operational usage telemetry to enhance model performance.",
            "severity": "High"
        },
        {
            "position": 7,
            "clause_number": "7",
            "title": "DATA PRIVACY AND COMPLIANCE SAFEGUARDS",
            "category": "Privacy",
            "text": "Both parties agree to comply with all applicable data privacy regulations, including the General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA), maintaining appropriate technical and organizational safeguards against unauthorized processing or accidental loss.",
            "severity": "Moderate"
        },
        {
            "position": 8,
            "clause_number": "8",
            "title": "GOVERNING JURISDICTION AND BINDING ARBITRATION",
            "category": "Dispute Resolution",
            "text": "This Agreement shall be governed by the laws of the State of Delaware, United States, without regard to its conflict of laws principles. Any dispute arising out of or related to this Agreement shall be resolved exclusively through final and binding arbitration administered by the American Arbitration Association.",
            "severity": "Moderate"
        },
        {
            "position": 9,
            "clause_number": "9",
            "title": "CROSS-BORDER TARIFFS AND STATUTORY ALLOCATION",
            "category": "General / Boilerplate",
            "text": "In the event of unforeseen cross-border tariffs or trade restrictions as referenced in Annex IV, the financial burden shall be dynamically negotiated between the parties under the principles of UNCITRAL Article 79 rules, subject to the force majeure provisions of Section 7.2.",
            "severity": "Moderate"
        }
    ]

    res = simplify_document_clauses(msa_clauses)
    assert res["success"] is True
    assert res["total_clauses"] == 9

    # Check Clause 1: One-way Customer Indemnity
    c1 = res["clauses"][0]
    assert "Customer only" in c1["who_is_bound"]
    assert "defend, indemnify, and hold harmless" in c1["simplified_text"].lower()
    assert not check_banned_strings(c1["simplified_text"])

    # Check Clause 2: Vendor termination at will
    c2 = res["clauses"][1]
    assert "Vendor only" in c2["who_is_bound"]
    assert "no refund" in c2["simplified_text"].lower()
    assert not check_banned_strings(c2["simplified_text"])

    # Check Clause 4: 15-day payment with 1.5% compounding interest
    c4 = res["clauses"][3]
    assert "15 days" in c4["simplified_text"]
    assert "1.5%" in c4["simplified_text"]
    assert "compounded monthly" in c4["simplified_text"].lower() or "compounding" in c4["simplified_text"].lower()
    assert not check_banned_strings(c4["simplified_text"])

    # Check Clause 6: Perpetual telemetry license
    c6 = res["clauses"][5]
    assert "perpetual, irrevocable, royalty-free" in c6["simplified_text"].lower()
    assert not check_banned_strings(c6["simplified_text"])

    # Check Clause 9: Dangling references
    c9 = res["clauses"][8]
    assert "Annex IV" in c9["simplified_text"] or "Section 7.2" in c9["simplified_text"]
    assert not check_banned_strings(c9["simplified_text"])


def test_w6_banned_string_elimination():
    """Verify that zero banned strings or templates are produced."""
    sample_text = "Vendor may terminate for convenience upon written notice."
    res = synthesize_detailed_plain_english_analysis(
        text=sample_text,
        severity="High",
        category="Termination",
        clause_number="2",
        title="Termination"
    )
    assert res["status"] == "ok"
    banned = check_banned_strings(res["simplified_text"])
    assert not banned, f"Found banned strings: {banned}"


def test_w6_failure_isolation_honest_fallback():
    """Verify that when AI call fails, honest fallback is provided and severity is 'Needs review'."""
    class FailingMockClient:
        class chat:
            class completions:
                @staticmethod
                def create(*args, **kwargs):
                    raise RuntimeError("API timeout simulation")

    clause = {
        "position": 1,
        "clause_number": "1",
        "title": "Payment Terms",
        "category": "Payment",
        "text": "Payment is due in 30 days."
    }

    res = simplify_single_clause(clause, override_client=FailingMockClient())
    assert res["status"] == "FAILED_SIMPLIFICATION"
    assert res["severity"] in ("Needs review", "RISK_CLASSIFICATION_UNAVAILABLE")
    assert "AI explanation generation failed" in res["simplified_text"]
    assert "Payment is due in 30 days." in res["original_text"]
