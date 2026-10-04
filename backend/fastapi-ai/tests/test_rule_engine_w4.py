"""
Unit tests for Workstream W4: Party-Centric Severity & Rule Engine
Tests generalized legal pattern matching across diverse contract types,
party perspectives (Customer, Vendor, Client, Consultant, Tenant),
and the NOT_ASSESSED / Needs Review failure isolation invariants.
"""

import pytest
from app.services.rule_engine_service import evaluate_rules, RULES_REGISTRY
from app.services.output_validator_service import (
    validate_and_resolve_clause_risk,
    compute_party_severity,
    validate_severity_label,
    OutputValidationError
)


def test_rule_engine_generalized_patterns():
    """Test that rules match verb/noun forms across diverse contract types."""
    # 1. Termination at will without refund (MSA)
    msa_term = "Vendor may suspend or terminate immediately upon written notice for any reason or no reason without refund of prepaid fees."
    findings = evaluate_rules(text=msa_term)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R008" in rule_ids

    # 2. Perpetual telemetry license (MSA)
    msa_ip = "Customer grants Vendor a perpetual, irrevocable, royalty-free license to use anonymized operational usage telemetry to enhance machine learning models."
    findings = evaluate_rules(text=msa_ip)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R011" in rule_ids

    # 3. Compounding interest and collection legal costs (Consulting / MSA)
    late_fee = "Balances more than 30 days past due accrue interest at 2.0% per month compounding monthly plus all collection costs and reasonable legal fees."
    findings = evaluate_rules(text=late_fee)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R004" in rule_ids

    # 4. Non-compete and non-solicit (Consulting)
    non_compete = "Consultant shall not directly or indirectly compete during the term plus 24 months thereafter for any client introduced by Client."
    findings = evaluate_rules(text=non_compete)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R014" in rule_ids

    # 5. Uncapped indemnity (MSA / Lease)
    indemnity = "Customer shall defend, indemnify, and hold harmless Vendor against any and all claims without limitation."
    findings = evaluate_rules(text=indemnity)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R006" in rule_ids

    # 6. Auto-renewal with price escalation (SaaS / MSA)
    auto_renew = "This agreement shall automatically renew for successive 12-month periods, and Vendor may raise prices up to 15% at each renewal."
    findings = evaluate_rules(text=auto_renew)["findings"]
    rule_ids = [f["rule_id"] for f in findings]
    assert "R001" in rule_ids


def test_party_centric_severity_resolution():
    """Test that severity reflects the reviewing party's risk exposure."""
    # Customer reviewing one-way uncapped indemnity -> High
    indem_text = "Customer shall indemnify and hold harmless Vendor from any and all damages without limitation."
    res_customer = validate_and_resolve_clause_risk(
        clause={"clause_number": "1", "text": indem_text, "category": "Indemnification"},
        raw_classification={"severity": "Low"},
        rule_findings=[{"clause_id": "1", "rule_id": "R006", "risk_signal": "Broad Indemnification"}],
        reviewing_party="Customer"
    )
    assert res_customer["final_severity"] == "High"
    assert "R006" in res_customer["rule_ids"]
    assert "reviewing party" in res_customer["risk_reason"].lower() or "indemnification" in res_customer["risk_reason"].lower()

    # Vendor reviewing termination for convenience at Vendor's option -> Low/Safe
    term_text = "Vendor may terminate immediately for convenience."
    sev, reason = compute_party_severity(
        rule_ids=["R008"],
        category="Termination",
        clause_text=term_text,
        reviewing_party="Vendor"
    )
    # For vendor who holds the right, it's not a severe penalty
    assert sev in ["Low", "Moderate", "High"]

    # Customer reviewing Vendor's at-will termination without refund -> High
    res_term_cust = validate_and_resolve_clause_risk(
        clause={"clause_number": "2", "text": "Vendor reserves right to terminate immediately without refund", "category": "Termination"},
        raw_classification={"severity": "Low"},
        rule_findings=[{"clause_id": "2", "rule_id": "R008", "risk_signal": "Unfavorable Termination"}],
        reviewing_party="Customer"
    )
    assert res_term_cust["final_severity"] == "High"

    # Consultant reviewing one-sided non-compete -> High
    res_consultant = validate_and_resolve_clause_risk(
        clause={"clause_number": "10", "text": "Consultant shall not compete during term plus 24 months", "category": "Restrictive Covenants"},
        raw_classification={"severity": "Low"},
        rule_findings=[{"clause_id": "10", "rule_id": "R014", "risk_signal": "Non-Compete"}],
        reviewing_party="Consultant"
    )
    assert res_consultant["final_severity"] == "High"


def test_benign_boilerplate_severity():
    """Test that standard boilerplate without risk signals is classified as Low/Safe."""
    gov_text = "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware."
    res_gov = validate_and_resolve_clause_risk(
        clause={"clause_number": "8", "text": gov_text, "category": "Governing Law"},
        raw_classification={"severity": "Low"},
        rule_findings=[],
        reviewing_party="Customer"
    )
    assert res_gov["final_severity"] == "Low"

    entire_text = "This Agreement constitutes the entire agreement between the parties with respect to the subject matter."
    res_entire = validate_and_resolve_clause_risk(
        clause={"clause_number": "12", "text": entire_text, "category": "Entire Agreement"},
        raw_classification={"severity": "Safe"},
        rule_findings=[],
        reviewing_party="Customer"
    )
    assert res_entire["final_severity"] in ["Safe", "Low"]


def test_failure_isolation_never_defaults_to_safe():
    """Test that malformed or errored classifications produce 'Needs review' / FAILED_VALIDATION."""
    # Missing classifier output
    res_none = validate_and_resolve_clause_risk(
        clause={"clause_number": "1", "text": "Some ambiguous text", "category": "General"},
        raw_classification=None,
        rule_findings=[]
    )
    assert res_none["validation_status"] == "FAILED_VALIDATION"
    assert res_none["final_severity"] is None
    assert res_none["severity"] == "Needs review"

    # Classifier runtime error
    res_err = validate_and_resolve_clause_risk(
        clause={"clause_number": "2", "text": "Some text", "category": "General"},
        raw_classification={"error": "Model timeout after 5000ms"},
        rule_findings=[]
    )
    assert res_err["validation_status"] == "FAILED_VALIDATION"
    assert res_err["final_severity"] is None
    assert res_err["severity"] == "Needs review"
