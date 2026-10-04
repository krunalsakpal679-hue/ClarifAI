"""
Unit tests for Workstream W5: Legal Drafting Fact Extraction & Grounding
Tests extraction of dual word(digits) durations, compounding interest rates,
flat fees vs percentage rates, currency parsing, span-local role assignment,
and token-boundary presence checking.
"""

import pytest
from app.services.claim_grounding_service import (
    extract_legal_facts,
    verify_and_ground_clause_narrative,
    parse_legal_number,
    check_banned_strings
)


def test_legal_drafting_durations_and_periods():
    """Tests dual word(digits) duration extraction across legal drafting styles."""
    # 1. Payment terms: 45 days, 15 days, 30 days
    t1 = "All undisputed invoices must be paid within forty-five (45) days of the invoice date."
    facts1 = extract_legal_facts(t1)
    assert len(facts1) >= 1
    assert facts1[0]["value"] == 45.0
    assert facts1[0]["unit"] == "days"
    assert facts1[0]["role"] == "Payment Term / Window"

    t2 = "Payments are due within fifteen (15) days of receipt."
    facts2 = extract_legal_facts(t2)
    assert len(facts2) >= 1
    assert facts2[0]["value"] == 15.0
    assert facts2[0]["unit"] == "days"

    # 2. Terms & Renewals: 12 month periods, 24 months, 2 years, 3 years
    t3 = "Agreement auto-renews for successive twelve (12) month periods unless terminated sixty (60) days prior."
    facts3 = extract_legal_facts(t3)
    values3 = [f["value"] for f in facts3]
    assert 12.0 in values3
    assert 60.0 in values3

    t4 = "Non-compete obligation continues during the term plus twenty-four (24) months thereafter."
    facts4 = extract_legal_facts(t4)
    assert any(f["value"] == 24.0 and f["unit"] == "months" for f in facts4)

    t5 = "The initial term of this lease shall be three (3) years commencing November 1, 2026."
    facts5 = extract_legal_facts(t5)
    assert any(f["value"] == 3.0 and f["unit"] == "years" for f in facts5)


def test_legal_drafting_rates_and_compounding():
    """Tests interest rates, compounding qualifiers, flat fees, and escalation caps."""
    # 1. Compounding interest
    t1 = "Late payments accrue interest at 1.5% per month, compounded monthly, plus all collection costs."
    facts1 = extract_legal_facts(t1)
    assert any(f["value"] == 1.5 and f["role"] == "Late Payment Interest Rate" for f in facts1)
    assert any(f.get("qualifier") == "compounded monthly" for f in facts1)

    # 2. Flat late fee vs interest rate
    t2 = "Tenant shall pay a flat late fee of 5% of the overdue balance if rent is received after the 5th."
    facts2 = extract_legal_facts(t2)
    assert any(f["value"] == 5.0 and f["role"] == "Flat Late Fee Percentage" for f in facts2)

    # 3. Price escalation
    t3 = "Vendor may raise prices up to fifteen percent (15%) at each annual renewal."
    facts3 = extract_legal_facts(t3)
    assert any(f["value"] == 15.0 and f["role"] == "Annual Price Escalation Cap" for f in facts3)


def test_currency_and_span_local_roles():
    """Tests currency amounts and span-local role assignment without cross-domain leakage."""
    # Rent and security deposit in lease
    lease_text = "Tenant agrees to pay $5,000.00 USD per month as base rent and a $10,000 security deposit upon execution."
    facts = extract_legal_facts(lease_text)
    roles = {f["role"]: f["value"] for f in facts}
    assert roles.get("Monthly Base Rent") == 5000.0
    assert roles.get("Security Deposit") == 10000.0
    # Ensure no employment / loan labels leak
    assert "Salary / Compensation" not in roles
    assert "Principal Amount" not in roles

    # Liability cap
    cap_text = "In no event shall aggregate liability under this Agreement exceed $50,000."
    cap_facts = extract_legal_facts(cap_text)
    assert any(f["role"] == "Liability Cap" and f["value"] == 50000.0 for f in cap_facts)


def test_token_boundary_presence_grounding():
    """Tests that token boundary checks prevent substring false matches (15 in 150)."""
    source = "Invoice must be paid within 15 days."
    # Narrative says 150 days (wrong number)
    narrative = "Invoices are payable within 150 days."
    res = verify_and_ground_clause_narrative(
        source_text=source,
        clause_title="Payment Terms",
        what_this_clause_means=narrative,
        obligations=narrative,
        details_list=[]
    )
    # 15 should NOT match 150, and must be preserved into details_list
    assert any("15 days" in d for d in res["details_list"])


def test_banned_strings_gate():
    """Spec CI Gate 5: Banned strings are caught and flagged."""
    banned_sample = "The Obligated Party shall pay RS 5000 per standard operative contractual provisions."
    detected = check_banned_strings(banned_sample)
    assert "Obligated Party" in detected
    assert "RS" in detected
    assert "standard operative contractual provisions" in detected
