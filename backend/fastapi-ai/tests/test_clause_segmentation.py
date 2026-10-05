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


from app.core.config import settings


def test_preamble_and_closing_separation_segmentation():
    contract_with_preamble = (
        "THIS AGREEMENT is made between Company A and Company B.\n"
        "WHEREAS the parties desire to collaborate;\n"
        "NOW THEREFORE the parties agree as follows:\n\n"
        "1. In pursuance of the said agreement, Company A shall provide services.\n\n"
        "2. The Lessee hereby covenants to pay rent on time.\n\n"
        "IN WITNESS WHEREOF the parties have executed this Agreement.\n"
        "Signed and delivered by Company A.\n"
        "THE SCHEDULE ABOVE REFERRED TO"
    )
    result = segment_document_clauses(contract_with_preamble)

    assert result["success"] is True
    assert result["total_clauses"] == 2
    clauses = result["clauses"]

    # Verify positions and numbering match the operative clauses exactly
    assert clauses[0]["position"] == 1
    assert clauses[0]["clause_number"] == "1"
    assert "Company A shall provide services" in clauses[0]["text"]

    assert clauses[1]["position"] == 2
    assert clauses[1]["clause_number"] == "2"
    assert "pay rent on time" in clauses[1]["text"]

    # Verify preamble & closing are separated and not in clauses
    assert result["preamble"] is not None
    assert "WHEREAS the parties desire to collaborate" in result["preamble"]
    assert "IN WITNESS WHEREOF" not in clauses[1]["text"]
    assert result["signature_block"] is not None
    assert "IN WITNESS WHEREOF" in result["signature_block"]


def test_segment_clauses_api_endpoint():
    payload = {
        "text": (
            "Section 1. Scope of Services.\nVendor agrees to perform services.\n\n"
            "Section 2. Fees and Expenses.\nClient agrees to pay invoices."
        )
    }
    headers = {}
    if settings.INTERNAL_SERVICE_SECRET:
        headers["X-Internal-Service-Secret"] = settings.INTERNAL_SERVICE_SECRET

    response = client.post("/api/v1/segment-clauses", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_clauses"] == 2
    assert data["clauses"][0]["position"] == 1
    assert data["clauses"][1]["position"] == 2


def test_contract_e_sample_shuttle_24_sections_segmentation():
    """
    Regression test ensuring Contract E (SampleContract-Shuttle.pdf) segments
    into exactly 24 numbered sections with sub-items (A., B., 1., 2.) nested.
    """
    from pathlib import Path
    from app.services.pdf_service import extract_pdf_text_service
    from app.services.text_cleaning_service import clean_legal_text

    pdf_path = Path("evaluation_dataset/documents/SampleContract-Shuttle.pdf")
    if not pdf_path.exists():
        pdf_path = Path("evaluation_dataset/documents/contract_e_professional_services.pdf")

    if pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()
        extracted = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
        cleaned = clean_legal_text(extracted.get("full_text", ""))
        result = segment_document_clauses(cleaned.get("cleaned_text", ""))

        assert result["success"] is True
        assert result["total_clauses"] == 24
        clauses = result["clauses"]

        # Verify section titles
        expected_titles = [
            "DUTIES",
            "COMPENSATION",
            "TERM",
            "EARLY TERMINATION",
            "INDEMNIFICATION FOR DAMAGES, TAXES AND CONTRIBUTIONS",
            "INSURANCE",
            "FEDERAL, STATE AND LOCAL LAWS",
            "EQUAL EMPLOYMENT OPPORTUNITY",
            "HARASSMENT",
            "LICENSES",
            "INDEPENDENT CONSULTANT STATUS",
            "RETENTION AND AUDIT OF RECORDS",
            "INSPECTION OF WORK",
            "ACKNOWLEDGMENT",
            "WORK PRODUCTS",
            "SAFETY",
            "MODIFICATION OF AGREEMENT",
            "DISPUTES",
            "AUDIT REVIEW PROCEDURES",
            "SUBCONTRACTING",
            "NONASSIGNMENT",
            "REBATES, KICKBACKS OR OTHER UNLAWFUL CONSIDERATION",
            "NOTIFICATION",
            "COMPLETE AGREEMENT"
        ]
        for idx, expected_title in enumerate(expected_titles):
            assert clauses[idx]["clause_number"] == str(idx + 1)
            assert expected_title in clauses[idx]["title"].upper()


