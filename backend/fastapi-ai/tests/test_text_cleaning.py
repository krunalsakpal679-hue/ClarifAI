"""
ClarifAI Legal Text Cleaning Unit Tests (AI-PHASE-TEXT-CLEANING)
Verifies whitespace normalization, hyphenation break repair, running header/footer stripping,
and strict digit, date, and currency symbol preservation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.text_cleaning_service import clean_legal_text

client = TestClient(app)


def test_whitespace_normalization():
    raw_text = "Section 1.   Term  and   Termination.\n\n\n\n\n  Party A  shall  pay."
    result = clean_legal_text(raw_text)

    assert result["success"] is True
    assert "normalize_horizontal_whitespace" in result["rules_applied"]
    assert "normalize_paragraph_newlines" in result["rules_applied"]
    assert result["cleaned_text"] == "Section 1. Term and Termination.\n\nParty A shall pay."


def test_hyphenation_break_repair():
    raw_text = (
        "The Vendor agrees to maintain confi-\n"
        "dentiality regarding all proprietary information. "
        "All legal obli-\n"
        "gations shall remain binding on both parties."
    )
    result = clean_legal_text(raw_text)

    assert result["success"] is True
    assert "repair_hyphenated_line_breaks" in result["rules_applied"]
    assert "confidentiality" in result["cleaned_text"]
    assert "obligations" in result["cleaned_text"]
    assert "confi-\ndentiality" not in result["cleaned_text"]
    assert "obli-\ngations" not in result["cleaned_text"]


def test_running_header_footer_stripping():
    raw_text = (
        "Page 1 of 10\n"
        "MASTER SERVICES AGREEMENT\n\n"
        "Clause 1. Indemnification obligations.\n"
        "Page 2 of 10\n"
        "Clause 2. Limitation of Liability."
    )
    result = clean_legal_text(raw_text)

    assert result["success"] is True
    assert "strip_running_headers_footers" in result["rules_applied"]
    assert "Page 1 of 10" not in result["cleaned_text"]
    assert "Page 2 of 10" not in result["cleaned_text"]
    assert "Clause 1. Indemnification obligations." in result["cleaned_text"]


def test_digit_date_currency_preservation_regression():
    # Complex legal fixture containing figures, dates, and currencies
    fixture_text = (
        "On 2026-08-24, Party B shall remit $10,000.00 (or ₹750,000) at an annual interest rate of 5.5%. "
        "The late penalty is $250 per day starting from 12/31/2025 under Section 4.2."
    )
    result = clean_legal_text(fixture_text)
    cleaned = result["cleaned_text"]

    # Verify figures & dates are strictly unchanged
    assert "2026-08-24" in cleaned
    assert "$10,000.00" in cleaned
    assert "₹750,000" in cleaned
    assert "5.5%" in cleaned
    assert "$250" in cleaned
    assert "12/31/2025" in cleaned
    assert "Section 4.2" in cleaned


def test_clean_text_api_endpoint():
    payload = {
        "raw_text": "Section 1.   Confi-\ndentiality obligations.\nPage 1 of 5",
        "preserve_page_markers": True
    }
    response = client.post("/api/v1/clean-text", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Confidentiality obligations." in data["cleaned_text"]
    assert "Page 1 of 5" not in data["cleaned_text"]
    assert len(data["rules_applied"]) >= 2
