"""
ClarifAI Legal Risk Rule Engine Unit Tests (AI-PHASE-RULE-ENGINE-01)
Verifies exact 15 rules (R001–R015), rule_version v1.1 tagging, evidence span extraction,
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
    {
        "rule_id": "R015",
        "risk_signal": "Uncapped Liability Carve-Out",
        "positive": "Except for breaches of confidentiality, neither party's aggregate liability shall not exceed $100,000.",
        "negative": "In no event shall either party's aggregate monetary liability under this agreement exceed $50,000.",
        "edge": "Other than monetary liability under Section 5, liability is capped at total fees paid."
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
    assert dumped["rule_version"] == RULE_SET_VERSION
    assert dumped["match_status"] == "MATCH"


@pytest.mark.parametrize("tc", RULE_TEST_CASES)
def test_all_15_rules_positive_negative_edge_cases(tc):
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


ADVERSARIAL_TEST_CASES = [
    # R004 (Late-Payment Penalty)
    ("R004", "Delinquent invoices shall bear interest at a rate of 1.5% per month until settled in full.", True),
    ("R004", "Unpaid balances will accrue interest at the rate of two percent (2.0%) per month compounding monthly.", True),
    ("R004", "All overdue fees shall incur a late payment penalty of 5% plus interest at a rate of 1% per month.", True),
    # R006 (Broad Indemnification)
    ("R006", "The Service Provider agrees to defend, indemnify and hold harmless the Client against any third party losses.", True),
    ("R006", "Licensee shall defend and indemnify Licensor from any third-party intellectual property claims.", True),
    ("R006", "Consultant shall indemnify, hold harmless, and defend Client and its agents against all claims.", True),
    # R011 (Broad IP Transfer)
    ("R011", "All deliverables created under this Statement of Work shall be deemed works made for hire under the US Copyright Act.", True),
    ("R011", "Developer expressly agrees that all software created hereunder is a work made for hire.", True),
    ("R011", "Service Provider hereby assigns all right, title, and interest in and to all inventions to the Company.", True),
    # R012 (Arbitration/Dispute Restriction)
    ("R012", "The parties submit to the exclusive jurisdiction of the state courts located in Cook County, Illinois.", True),
    ("R012", "Any legal action arising under this contract shall be brought in the exclusive jurisdiction in Travis County, Texas.", True),
    ("R012", "Each party irrevocably agrees that disputes will be settled via binding arbitration under AAA rules.", True),
    # R015 (Uncapped Liability Carve-Out)
    ("R015", "Except for breaches of confidentiality obligations, each party's aggregate liability under this agreement shall not exceed $100,000.", True),
    ("R015", "Excluding liability for gross negligence or willful misconduct, total monetary liability shall not exceed the fees paid hereunder.", True),
    ("R015", "Other than liabilities resulting from Section 8 (Indemnity), neither party's aggregate liability is capped at $50,000.", True),
    ("R015", "In no event shall either party's aggregate monetary liability under this agreement exceed the total fees paid in the prior six months.", False),
]


@pytest.mark.parametrize("rule_id, text, should_match", ADVERSARIAL_TEST_CASES)
def test_adversarial_rule_variants(rule_id, text, should_match):
    res = evaluate_rules(text=text)
    matched = any(f["rule_id"] == rule_id for f in res["findings"])
    if should_match:
        assert matched, f"Adversarial variant for {rule_id} expected to match but did not: '{text}'"
    else:
        assert not matched, f"Adversarial variant for {rule_id} expected NOT to match but did: '{text}'"


def test_real_msa_regression_sentences_fire():
    """Asserts R004, R006, R011, R012 all fire on verbatim sentences from real MSA."""
    s_r004 = "Any late payments shall accrue interest at a rate of one percent (1.0%) per month or the highest legal permissible limit, whichever is lower."
    s_r006 = "Vendor agrees to defend, indemnify, and hold harmless Customer, its officers, affiliates, and employees from and against any third-party claims..."
    s_r011 = "All deliverables, documentation, custom scripts, and code developed exclusively for Customer pursuant to this Agreement shall constitute 'works made for hire'..."
    s_r012 = "Any dispute arising hereunder shall be subject to the exclusive jurisdiction of the state and federal courts located in New Castle County, Delaware."

    res_r004 = evaluate_rules(text=s_r004)
    assert any(f["rule_id"] == "R004" for f in res_r004["findings"]), "R004 failed to fire on verbatim MSA sentence"

    res_r006 = evaluate_rules(text=s_r006)
    assert any(f["rule_id"] == "R006" for f in res_r006["findings"]), "R006 failed to fire on verbatim MSA sentence"

    res_r011 = evaluate_rules(text=s_r011)
    assert any(f["rule_id"] == "R011" for f in res_r011["findings"]), "R011 failed to fire on verbatim MSA sentence"

    res_r012 = evaluate_rules(text=s_r012)
    assert any(f["rule_id"] == "R012" for f in res_r012["findings"]), "R012 failed to fire on verbatim MSA sentence"


def test_real_msa_r015_uncapped_liability_carveout():
    """Asserts R015 fires on Section 6 carve-out from real MSA."""
    s_r015 = (
        "Except for liabilities arising under Section 3 (Confidentiality) or Section 5 (Indemnification), "
        "neither party's aggregate monetary liability under this Agreement shall exceed the total amount actually "
        "paid by Customer to Vendor in the twelve (12) months preceding the event giving rise to liability."
    )
    res_r015 = evaluate_rules(text=s_r015)
    assert any(f["rule_id"] == "R015" for f in res_r015["findings"]), "R015 failed to fire on Section 6 carve-out sentence"


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
