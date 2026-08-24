"""
ClarifAI Legal Clause Categorization Unit Tests (AI-PHASE-CLAUSE-CATEGORIZATION)
Verifies categorization into the fixed 8-value PRD set, adversarial out-of-set value rejection,
zero-category handling for ambiguous clauses, and structured API endpoint.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.models.clause_categorization import (
    ClauseCategoryEnum,
    APPROVED_CATEGORIES_SET,
    CategorizedClauseItem,
)
from app.services.clause_categorization_service import (
    categorize_clause_records,
    validate_category_value,
)

client = TestClient(app)


def test_all_8_approved_categories():
    sample_clauses = [
        {"position": 1, "text": "Party B shall remit $15,000.00 fee within 30 days of billing invoice."},
        {"position": 2, "text": "Either party may terminate this agreement upon 30 days written notice of default breach."},
        {"position": 3, "text": "This agreement shall automatically renew for successive one-year terms."},
        {"position": 4, "text": "Each party agrees to hold all confidential information in strict secrecy under NDA."},
        {"position": 5, "text": "Company shall indemnify and hold harmless client against all liability damages and loss."},
        {"position": 6, "text": "All copyrights, trademarks, and patent IP rights remain sole property of Licensor."},
        {"position": 7, "text": "Processing of personal data shall comply with GDPR privacy protection regulations."},
        {"position": 8, "text": "Any dispute shall be settled by binding arbitration under local court jurisdiction."},
    ]

    result = categorize_clause_records(sample_clauses)
    assert result["success"] is True
    assert result["total_clauses"] == 8

    categorized = result["clauses"]

    # Verify each clause received valid categories drawn ONLY from the 8-value set
    expected_categories = [
        ClauseCategoryEnum.PAYMENT,
        ClauseCategoryEnum.TERMINATION,
        ClauseCategoryEnum.RENEWAL,
        ClauseCategoryEnum.CONFIDENTIALITY,
        ClauseCategoryEnum.LIABILITY,
        ClauseCategoryEnum.INTELLECTUAL_PROPERTY,
        ClauseCategoryEnum.PRIVACY,
        ClauseCategoryEnum.DISPUTE_RESOLUTION,
    ]

    for idx, expected in enumerate(expected_categories):
        clause_cats = categorized[idx]["categories"]
        assert expected in clause_cats
        for cat in clause_cats:
            assert cat in APPROVED_CATEGORIES_SET or cat.value in APPROVED_CATEGORIES_SET


def test_ambiguous_preamble_clause_zero_categories():
    ambiguous_clause = [
        {"position": 1, "text": "This Agreement is made on August 24, 2026 by and between the undersigned parties."}
    ]
    result = categorize_clause_records(ambiguous_clause)

    # Verify zero categories assigned for general preamble
    assert result["clauses"][0]["categories"] == []


def test_adversarial_out_of_set_category_rejection():
    # 1. Test validate_category_value helper function rejects invalid category
    with pytest.raises(HTTPException) as exc_info:
        validate_category_value("UnapprovedCategory")
    assert exc_info.value.status_code == 422
    assert "INVALID_CATEGORY_REJECTED" in str(exc_info.value.detail)

    # 2. Test Pydantic model validator rejects out-of-set category string
    with pytest.raises(ValueError) as val_exc:
        CategorizedClauseItem(
            position=1,
            text="Valid clause text content here.",
            character_count=30,
            categories=["FinancialDomain"]  # Out-of-set invalid category
        )
    assert "Input should be" in str(val_exc.value)


def test_categorize_clauses_api_endpoint():
    payload = {
        "clauses": [
            {
                "position": 1,
                "clause_number": "Section 1",
                "title": "Payment Terms",
                "text": "Client agrees to pay invoices within 30 days.",
                "character_count": 42
            }
        ]
    }
    response = client.post("/api/v1/categorize-clauses", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_clauses"] == 1
    assert "Payment" in data["clauses"][0]["categories"]
