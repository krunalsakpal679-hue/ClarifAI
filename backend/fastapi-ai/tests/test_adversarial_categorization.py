"""
Adversarial Category Classification Unit Tests (Phase 2)
Verifies evidence-weighted dominant subject scoring over naive first-match keyword logic.
"""

import pytest
from app.models.clause_categorization import ClauseCategoryEnum
from app.services.clause_categorization_service import (
    score_clause_categories,
    categorize_clause_records
)

ADVERSARIAL_CATEGORY_CASES = [
    {
        "id": "CASE_1_RENT_ARREARS_TERMINATION",
        "description": "Clause mentions rent/payment arrears but dominant legal remedy is lease forfeiture and termination.",
        "text": "Failure to pay monthly ground rent within thirty (30) days of the due date shall constitute an incurable default resulting in immediate contract termination and forfeiture of leasehold rights.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.TERMINATION,
        "rule_findings": [{"rule_id": "R008", "risk_signal": "Unfavorable Termination"}]
    },
    {
        "id": "CASE_2_PAYMENT_DISPUTE_ARBITRATION",
        "description": "Clause mentions payment and billing disputes but dominant subject is mandatory binding arbitration.",
        "text": "In the event of any billing or payment dispute arising under this Agreement, the parties shall resolve the claim through binding arbitration administered by the American Arbitration Association rather than court litigation.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.DISPUTE_RESOLUTION,
        "rule_findings": [{"rule_id": "R012", "risk_signal": "Arbitration/Dispute Restriction"}]
    },
    {
        "id": "CASE_3_ROYALTY_FREE_IP_ASSIGNMENT",
        "description": "Clause mentions paying no royalties/fees, but dominant subject is full assignment of intellectual property.",
        "text": "Licensee shall pay no royalties, license fees, or other consideration for the perpetual assignment of all intellectual property, software source code, and patent rights created under this Statement of Work.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.INTELLECTUAL_PROPERTY,
        "rule_findings": [{"rule_id": "R011", "risk_signal": "Broad IP Transfer"}]
    },
    {
        "id": "CASE_4_CONFIDENTIALITY_PRICING_FEES",
        "description": "Clause mentions pricing and fee schedules, but dominant subject is strict confidentiality.",
        "text": "Consultant shall maintain strict confidentiality over Customer's pricing data, payment structures, and fee schedules, and shall not disclose such proprietary information to any third party.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.CONFIDENTIALITY,
        "rule_findings": [{"rule_id": "R010", "risk_signal": "Restrictive Confidentiality"}]
    },
    {
        "id": "CASE_5_LIABILITY_CAP_PAID_FEES",
        "description": "Clause mentions paid maintenance fees, but dominant effect is consequential damages disclaimer and liability limitation.",
        "text": "Under no circumstances shall Vendor be liable for indirect, consequential, or punitive damages, even if Customer has paid all maintenance charges and service fees in full.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.LIABILITY,
        "rule_findings": [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}]
    },
    {
        "id": "CASE_6_RENEWAL_CONDITIONED_FEES",
        "description": "Clause mentions fee settlement condition, but dominant subject is automatic renewal for successive periods.",
        "text": "Upon expiration of the initial term, Customer may extend the term for successive one-year renewal periods provided that all previous service fees have been settled.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.RENEWAL,
        "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}]
    },
    {
        "id": "CASE_7_TERMINATION_DESPITE_PAYMENT",
        "description": "Clause mentions timely payment, but dominant right is vendor convenience termination without notice.",
        "text": "Vendor reserves the unilateral right to terminate this agreement for convenience at any time without notice, regardless of whether Customer is current on all invoice payments.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.TERMINATION,
        "rule_findings": [{"rule_id": "R008", "risk_signal": "Unfavorable Termination"}]
    },
    {
        "id": "CASE_ADV_5_MAINTAIN_CONFIDENTIALITY_PRICING_BILLING",
        "description": "Dominant verb is maintain confidentiality of X where X refers to pricing and billing structures.",
        "text": "Client shall maintain the confidentiality of all pricing and billing structures disclosed hereunder.",
        "naive_match": "Payment",
        "expected_category": ClauseCategoryEnum.CONFIDENTIALITY,
        "rule_findings": []
    }
]


def test_adv_5_maintain_confidentiality_pricing_billing_regression():
    """
    Explicit regression test for ADV-5:
    'Client shall maintain the confidentiality of all pricing and billing structures disclosed hereunder.'
    Asserts that Confidentiality strictly wins over Payment without relying on rule engine findings.
    """
    clause_text = "Client shall maintain the confidentiality of all pricing and billing structures disclosed hereunder."
    
    # Test raw scoring without any rule findings
    ranked = score_clause_categories(text=clause_text, rule_findings=[])
    assert len(ranked) > 0, "ADV-5 produced no category rankings."
    
    winning_category, top_score = ranked[0]
    scores_dict = {cat.value: score for cat, score in ranked}
    
    # Explicit assertion on winning category
    assert winning_category == ClauseCategoryEnum.CONFIDENTIALITY, (
        f"ADV-5 Regression Failed: Expected winning category to be 'Confidentiality', but got '{winning_category.value}'. "
        f"Full score breakdown: {scores_dict}"
    )
    
    # Assert Confidentiality strictly outscores Payment
    conf_score = scores_dict.get(ClauseCategoryEnum.CONFIDENTIALITY.value, 0)
    payment_score = scores_dict.get(ClauseCategoryEnum.PAYMENT.value, 0)
    assert conf_score > payment_score, (
        f"Confidentiality ({conf_score}) must strictly outscore Payment ({payment_score})."
    )

    # Test batch categorization record endpoint
    res = categorize_clause_records([{"clause_id": "ADV-5", "text": clause_text}])
    assert res["success"] is True
    assert len(res["clauses"]) == 1
    assert res["clauses"][0]["categories"][0] == ClauseCategoryEnum.CONFIDENTIALITY


def test_adversarial_category_classification_all_cases():
    """Verifies that all 8 adversarial test cases resolve to expected dominant category, avoiding naive keyword pitfalls."""
    for case in ADVERSARIAL_CATEGORY_CASES:
        ranked = score_clause_categories(
            text=case["text"],
            rule_findings=case["rule_findings"]
        )
        assert len(ranked) > 0, f"Case {case['id']} produced no categories."
        top_cat, top_score = ranked[0]
        assert top_cat == case["expected_category"], (
            f"Failed on {case['id']}: Expected {case['expected_category'].value}, got {top_cat.value} (naive was {case['naive_match']}). Full ranking: {ranked}"
        )


def test_adversarial_category_batch_categorization():
    """Verifies batch categorization endpoint logic for adversarial cases."""
    clauses_payload = [
        {"clause_id": c["id"], "position": i + 1, "text": c["text"], "rule_findings": c["rule_findings"]}
        for i, c in enumerate(ADVERSARIAL_CATEGORY_CASES)
    ]
    res = categorize_clause_records(clauses_input=clauses_payload)
    assert res["success"] is True
    assert res["total_clauses"] == len(ADVERSARIAL_CATEGORY_CASES)

    for i, categorized_item in enumerate(res["clauses"]):
        expected = ADVERSARIAL_CATEGORY_CASES[i]["expected_category"]
        assigned = categorized_item["categories"]
        assert len(assigned) > 0
        assert assigned[0] == expected, f"Clause {categorized_item['clause_id']} primary category was {assigned[0]}, expected {expected}"

