"""
ClarifAI Legal Risk Rule Engine Unit Tests (AI-PHASE-RULE-ENGINE-01)
Verifies exact 14 rules (R001–R014), rule_version v1.0 tagging, evidence span extraction,
prohibition of severity field per Chapter 16.10, and multi-signal fixture documents.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.rule_engine import RuleFinding, RULE_SET_VERSION
from app.services.rule_engine_service import evaluate_rules

client = TestClient(app)

# 14 Rules Fixtures Data (Positive, Negative, Edge case)
RULE_TEST_CASES = [
    {
        "rule_id": "R001",
        "risk_signal": "Auto-Renewal",
        "positive": "This contract shall renew automatically for consecutive one-year terms.",
        "negative": "This contract expires on December 31, 2026 without renewal.",
        "edge": "The subscription WILL AUTOMATICALLY RENEW unless cancelled in writing."
    },
    {
        "rule_id": "R002",
        "risk_signal": "Early-Termination Penalty",
        "positive": "Early termination shall incur an early termination fee of $5,000.00.",
        "negative": "Either party may terminate without any cancellation charge.",
        "edge": "Liquidated damages for early termination equal 50% of remaining fees."
    },
    {
        "rule_id": "R003",
        "risk_signal": "Hidden/Add-on Charges",
        "positive": "Client is responsible for an additional administrative fee and processing surcharge.",
        "negative": "All pricing is fixed and inclusive of all applicable fees.",
        "edge": "Unspecified fee surcharges may apply to monthly statements."
    },
    {
        "rule_id": "R004",
        "risk_signal": "Late-Payment Penalty",
        "positive": "Overdue invoices accrue a late payment interest rate of 1.5% per month.",
        "negative": "Invoices are payable net 30 days without interest.",
        "edge": "A late charge shall apply to all delinquent balances."
    },
    {
        "rule_id": "R005",
        "risk_signal": "Excessive Liability Transfer",
        "positive": "The company disclaims all liability and user assumes all risk.",
        "negative": "Company accepts standard statutory liability for gross negligence.",
        "edge": "Under no circumstances shall company have liability whatsoever."
    },
    {
        "rule_id": "R006",
        "risk_signal": "Broad Indemnification",
        "positive": "Customer agrees to defend and indemnify company against all claims.",
        "negative": "Each party is responsible solely for its own negligent acts.",
        "edge": "User shall indemnify and hold harmless vendor from third party losses."
    },
    {
        "rule_id": "R007",
        "risk_signal": "Unilateral Modification",
        "positive": "Vendor reserves the right to modify these terms at any time without prior notice.",
        "negative": "Amendments require mutual written consent signed by both parties.",
        "edge": "Company may change these terms at any time in its sole discretion."
    },
    {
        "rule_id": "R008",
        "risk_signal": "Unfavorable Termination",
        "positive": "Company may terminate for convenience immediately without cause.",
        "negative": "Termination requires a material breach and 30-day cure period.",
        "edge": "Immediate termination without notice may occur at company discretion."
    },
    {
        "rule_id": "R009",
        "risk_signal": "Unusual Notice Requirement",
        "positive": "Non-renewal requires written notice of at least 90 days prior to term end.",
        "negative": "Notice of non-renewal requires standard 30 days notice.",
        "edge": "Cancellation requires written notice of at least 120 days."
    },
    {
        "rule_id": "R010",
        "risk_signal": "Restrictive Confidentiality",
        "positive": "The confidentiality obligation shall survive indefinitely.",
        "negative": "Confidentiality obligations expire three (3) years after termination.",
        "edge": "Receiving party is bound to perpetual confidentiality forever."
    },
    {
        "rule_id": "R011",
        "risk_signal": "Broad IP Transfer",
        "positive": "Contractor assigns all right, title, and interest in all work made for hire.",
        "negative": "Contractor retains ownership of pre-existing background IP.",
        "edge": "All deliverables are irrevocable assignment to client."
    },
    {
        "rule_id": "R012",
        "risk_signal": "Arbitration/Dispute Restriction",
        "positive": "All claims shall be resolved through binding arbitration and class action waiver.",
        "negative": "Disputes shall be settled in local state courts of competent jurisdiction.",
        "edge": "Parties waive the right to a jury trial in all matters."
    },
    {
        "rule_id": "R013",
        "risk_signal": "Data/Privacy Obligation",
        "positive": "Company reserves the right to sell personal information to third-party advertisers.",
        "negative": "Personal data is strictly processed in compliance with GDPR.",
        "edge": "Vendor may share data with third-party advertisers without restriction."
    },
    {
        "rule_id": "R014",
        "risk_signal": "Restrictive Employment/Business Obligation",
        "positive": "Employee agrees to a strict non-compete restricting competitive business for 2 years.",
        "negative": "Employee is free to engage in independent consulting post-employment.",
        "edge": "Participant shall not engage in competing business activities."
    },
]


def test_rule_finding_schema_has_no_severity_field():
    """Chapter 16.10: Rule findings must NEVER include or imply a final severity field."""
    finding = RuleFinding(
        rule_id="R001",
        risk_signal="Auto-Renewal",
        matched_text="renews automatically",
        clause_id="1",
        evidence="Contract renews automatically every year."
    )
    dumped = finding.model_dump()
    assert "severity" not in dumped
    assert "risk_level" not in dumped
    assert dumped["rule_version"] == "v1.0"
    assert dumped["match_status"] == "MATCH"


@pytest.mark.parametrize("tc", RULE_TEST_CASES)
def test_all_14_rules_positive_negative_edge_cases(tc):
    rule_id = tc["rule_id"]

    # Positive match test
    pos_res = evaluate_rules(text=tc["positive"])
    pos_matches = [f for f in pos_res["findings"] if f["rule_id"] == rule_id]
    assert len(pos_matches) >= 1, f"Rule {rule_id} failed positive match on: {tc['positive']}"
    assert pos_matches[0]["rule_version"] == RULE_SET_VERSION

    # Negative match test
    neg_res = evaluate_rules(text=tc["negative"])
    neg_matches = [f for f in neg_res["findings"] if f["rule_id"] == rule_id]
    assert len(neg_matches) == 0, f"Rule {rule_id} falsely matched negative text: {tc['negative']}"

    # Edge case match test
    edge_res = evaluate_rules(text=tc["edge"])
    edge_matches = [f for f in edge_res["findings"] if f["rule_id"] == rule_id]
    assert len(edge_matches) >= 1, f"Rule {rule_id} failed edge case match on: {tc['edge']}"


def test_multi_signal_fixture_document():
    multi_signal_text = (
        "Section 1. Payment Terms.\nInvoices overdue accrue a late payment fee.\n\n"
        "Section 2. Renewal.\nThis contract shall renew automatically for successive terms.\n\n"
        "Section 3. Liability.\nCustomer agrees to defend and indemnify vendor from all claims."
    )

    res = evaluate_rules(text=multi_signal_text)
    assert res["success"] is True
    found_rule_ids = {f["rule_id"] for f in res["findings"]}

    # Verify planted rules detected
    assert "R001" in found_rule_ids  # Auto-Renewal
    assert "R004" in found_rule_ids  # Late-Payment
    assert "R006" in found_rule_ids  # Broad Indemnification


def test_evaluate_rules_api_endpoint():
    payload = {
        "text": "Company reserves the right to modify these terms at any time without prior notice."
    }
    response = client.post("/api/v1/evaluate-rules", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_findings"] >= 1
    assert data["findings"][0]["rule_id"] == "R007"
    assert "severity" not in data["findings"][0]
