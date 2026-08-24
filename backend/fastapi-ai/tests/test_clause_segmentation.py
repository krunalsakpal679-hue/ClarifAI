"""
ClarifAI Legal Clause Segmentation Unit Tests (AI-PHASE-CLAUSE-SEGMENTATION)
Verifies rule-based boundary detection, position ordering, source clause numbering,
verbatim text preservation, zero-clause failure path, and deterministic stability.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.clause_segmentation_service import segment_document_clauses

client = TestClient(app)


def test_numbered_contract_clause_segmentation():
    contract_text = (
        "Section 1. Term and Termination.\n"
        "This Agreement shall commence on the Effective Date and continue for a period of one (1) year.\n\n"
        "Section 2. Confidentiality Obligations.\n"
        "Each party agrees to hold all Confidential Information in strict confidence.\n\n"
        "Section 3. Limitation of Liability.\n"
        "In no event shall either party be liable for any indirect or consequential damages."
    )
    result = segment_document_clauses(contract_text)

    assert result["success"] is True
    assert result["total_clauses"] == 3
    clauses = result["clauses"]

    # Verify positions (1-indexed sequential)
    assert [c["position"] for c in clauses] == [1, 2, 3]

    # Verify source clause numbers preserved
    assert clauses[0]["clause_number"] == "1"
    assert clauses[1]["clause_number"] == "2"
    assert clauses[2]["clause_number"] == "3"

    # Verify verbatim text preservation
    assert "Agreement shall commence on the Effective Date" in clauses[0]["text"]
    assert "strict confidence" in clauses[1]["text"]
    assert "consequential damages" in clauses[2]["text"]


def test_heading_pattern_clause_segmentation():
    tos_text = (
        "INDEMNIFICATION\n"
        "User agrees to indemnify and hold harmless the Company from any third-party claims.\n\n"
        "GOVERNING LAW\n"
        "This agreement shall be governed by and construed in accordance with the laws of California.\n\n"
        "TERMINATION\n"
        "Either party may terminate this agreement at any time upon 30 days written notice."
    )
    result = segment_document_clauses(tos_text)

    assert result["success"] is True
    assert result["total_clauses"] == 3
    clauses = result["clauses"]

    assert clauses[0]["title"] == "INDEMNIFICATION"
    assert clauses[1]["title"] == "GOVERNING LAW"
    assert clauses[2]["title"] == "TERMINATION"


def test_zero_clauses_detected_failure_path():
    with pytest.raises(Exception) as exc_info:
        segment_document_clauses("   \n\n   ")

    # Verify structured HTTP 422 failure
    assert "ZERO_CLAUSES_DETECTED" in str(exc_info.value)


def test_segmentation_stability_repeatability():
    text = (
        "Clause 1. Definitions.\nDefinitions used herein shall have the standard legal meaning.\n\n"
        "Clause 2. Notices.\nAll notices under this contract shall be in writing."
    )

    run1 = segment_document_clauses(text)
    run2 = segment_document_clauses(text)

    assert run1 == run2
    assert run1["total_clauses"] == run2["total_clauses"]


def test_verbatim_text_preservation():
    verbatim_text = (
        "Section 4. Payment Terms.\n"
        "Party B shall remit $15,000.00 within thirty (30) days of invoice date."
    )
    result = segment_document_clauses(verbatim_text)
    clause = result["clauses"][0]

    # Assert text is verbatim and not rewritten
    assert "$15,000.00" in clause["text"]
    assert "thirty (30) days" in clause["text"]
    assert clause["character_count"] == len("".join(clause["text"].split()))


def test_segment_clauses_api_endpoint():
    payload = {
        "text": (
            "Section 1. Scope of Services.\nVendor agrees to perform services.\n\n"
            "Section 2. Fees and Expenses.\nClient agrees to pay invoices."
        )
    }
    response = client.post("/api/v1/segment-clauses", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_clauses"] == 2
    assert data["clauses"][0]["position"] == 1
    assert data["clauses"][1]["position"] == 2
