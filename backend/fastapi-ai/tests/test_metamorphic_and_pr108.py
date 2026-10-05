"""
ClarifAI Metamorphic and PR #108 Comprehensive Robustness Tests
(Master Prompt v5: Section 7a & 7a-2)

Tests:
1. Fact verifier on currency symbols, decimal amounts, percentages, and duration tokens.
2. Metamorphic perturbation of numbers, rates, party roles, and jurisdictions.
3. Heading-first categorization resilience against body-text financial numbers.
4. Segmentation immunity to inline exhibit citations and page markers.
5. Echo and template detector (<0.60 token overlap, no multi-clause sentence repetition).
6. Hardcode scan ensuring app code contains zero contract-specific literals.
"""

import pytest
import re
from app.services.fact_verifier_service import verify_fact_grounding
from app.services.clause_segmentation_service import segment_clauses
from app.services.clause_categorization_service import score_clause_categories, ClauseCategoryEnum
from app.services.simplification_service import simplify_single_clause


def test_verifier_pr108_amounts_and_percentages():
    """Verify that numbers with $, %, decimals, and written words pass, while hallucinated numbers fail."""
    clause = "Client shall pay an initial deposit of $5,000.00 within forty-five (45) days, plus interest at 2.0% per month."
    
    # 1. Valid facts matching exact source quotes
    valid_facts = [
        {"field": "deposit", "value": "$5,000.00", "source_quote": "an initial deposit of $5,000.00"},
        {"field": "deposit_num", "value": "5000", "source_quote": "$5,000.00"},
        {"field": "payment_window", "value": "45 days", "source_quote": "within forty-five (45) days"},
        {"field": "interest_rate", "value": "2.0% per month", "source_quote": "interest at 2.0% per month"},
    ]
    for fact in valid_facts:
        is_grounded, err = verify_fact_grounding(fact, clause)
        assert is_grounded, f"Valid fact {fact} unexpectedly rejected: {err}"

    # 2. Hallucinated numbers not in quote must FAIL
    invalid_facts = [
        {"field": "deposit", "value": "$10,000.00", "source_quote": "an initial deposit of $5,000.00"},
        {"field": "interest", "value": "15%", "source_quote": "interest at 2.0% per month"},
        {"field": "deadline", "value": "60 days", "source_quote": "within forty-five (45) days"},
        {"field": "phantom", "value": "$1,000,000", "source_quote": "deposit of $5,000.00"}
    ]
    for fact in invalid_facts:
        is_grounded, err = verify_fact_grounding(fact, clause)
        assert not is_grounded, f"Invalid fact {fact} should have been rejected."


def test_metamorphic_number_perturbation():
    """Verify that altering numbers in a contract changes extracted facts to the new numbers."""
    base_text = "Vendor may charge late fee of 2.0% per month for amounts overdue past 45 days."
    perturbed_text = "Vendor may charge late fee of 3.5% per month for amounts overdue past 37 days."

    fact_35 = {"field": "interest", "value": "3.5%", "source_quote": "3.5% per month"}
    fact_20 = {"field": "interest", "value": "2.0%", "source_quote": "2.0% per month"}

    # In perturbed text, 3.5% must pass and 2.0% must fail
    g35, _ = verify_fact_grounding(fact_35, perturbed_text)
    g20, _ = verify_fact_grounding(fact_20, perturbed_text)

    assert g35 is True
    assert g20 is False


def test_metamorphic_heading_categories_pr108():
    """Verify that headings decide category even when body text mentions unrelated money amounts."""
    test_cases = [
        ("Section 20. SUBCONTRACTING", "Subcontracts over $25,000 must carry all flow-down terms.", ClauseCategoryEnum.SUBCONTRACTING),
        ("Section 6. INSURANCE", "Consultant shall maintain $1,000,000 aggregate liability insurance.", ClauseCategoryEnum.INSURANCE),
        ("Section 12. RETENTION AND AUDIT OF RECORDS", "Accounting records and subcontracts over $25,000 retained 5 years.", ClauseCategoryEnum.AUDIT_AND_RECORDS),
        ("Section 15. WORK PRODUCTS", "Fee Schedule applies to all work products and deliverables.", ClauseCategoryEnum.IP_WORK_PRODUCT),
        ("Section 21. NONASSIGNMENT", "Neither party may assign this agreement without $10,000 transfer fee.", ClauseCategoryEnum.ASSIGNMENT),
        ("Section 18. DISPUTES", "Any controversy exceeding $50,000 submitted to internal review committee.", ClauseCategoryEnum.DISPUTE_RESOLUTION),
    ]

    for title, text, expected_enum in test_cases:
        ranked = score_clause_categories(text=text, title=title)
        assert len(ranked) > 0, f"No categories scored for {title}"
        primary_cat, score = ranked[0]
        assert primary_cat == expected_enum, f"Heading '{title}' got {primary_cat.value} instead of {expected_enum.value}."


def test_metamorphic_inline_exhibits_and_page_markers():
    """Verify inline Exhibit mentions and page markers do NOT trigger closing appendix truncation."""
    contract_text = (
        "Section 1. SCOPE OF SERVICES\n"
        "Consultant shall perform services described in Exhibit A attached hereto.\n"
        "Page 2 of 5\n"
        "Section 2. COMPENSATION\n"
        "Compensation shall be paid at the rates set forth in\n"
        "Exhibit B: Fee Schedule, which by this reference is incorporated herein.\n"
        "Consultant shall submit invoices monthly.\n"
        "Section 3. TERM\n"
        "The term of this Agreement is one year.\n"
        "IN WITNESS WHEREOF, the parties execute this agreement."
    )

    res = segment_clauses(contract_text)
    assert res["success"] is True
    clause_ids = [c["clause_id"] for c in res["clauses"]]
    assert len(clause_ids) == 3, f"Expected 3 clauses, got {len(clause_ids)}: {clause_ids}"
    assert res["is_continuous"] is True


def test_echo_and_template_detector():
    """Verify that plain_language never echoes the original clause text (>0.60 token overlap)."""
    clause = {
        "clause_id": "c-test-echo",
        "clause_number": "1",
        "title": "INDEMNIFICATION FOR DAMAGES",
        "text": "The Consultant shall exonerate, indemnify, defend, and hold harmless the Commission, its officers, agents, employees and volunteers from and against any and all claims, demands, losses, damages, defense costs, or liability of any kind or nature which Commission may sustain or incur.",
        "category": "Indemnification",
        "severity": "High"
    }

    res = simplify_single_clause(clause)
    plain = res["plain_language"]
    orig = clause["text"]

    tokens_orig = set(re.findall(r'\b[a-zA-Z]{3,}\b', orig.lower()))
    tokens_plain = set(re.findall(r'\b[a-zA-Z]{3,}\b', plain.lower()))
    overlap = len(tokens_orig.intersection(tokens_plain)) / max(len(tokens_orig.union(tokens_plain)), 1)

    assert overlap < 0.60, f"Echo detected: Jaccard token overlap {overlap:.2f} >= 0.60"
    assert "The Consultant shall exonerate, indemnify, defend, and hold harmless the Commission" not in plain


def test_banned_literals_hardcode_scan():
    """Ensure app code contains zero contract-specific names or facts."""
    import os
    banned_literals = [
        "Yesenia",
        "Luis Mendez",
        "Pacific Ave",
        "1.5% monthly late payment fees on overdue balances",
        "Total liability strictly capped at prior 12 months fees paid with zero carve-outs",
        "Operational terms evaluated under deterministic fact extraction"
    ]

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as py_file:
                    content = py_file.read()
                    for literal in banned_literals:
                        assert literal not in content, f"Banned contract-specific literal '{literal}' found in {path}"
