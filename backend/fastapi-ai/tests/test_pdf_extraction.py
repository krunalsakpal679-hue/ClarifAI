"""
ClarifAI PDF Text Extraction & Validation Unit Tests (AI-PHASE-PDF-EXTRACTION)
Verifies PyMuPDF digital extraction, page ordering, scanned OCR heuristic, encryption rejection (Decision R-12),
file size limits (Decision R-11), and corrupted PDF safe handling.
"""

import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate clean synthetic PDF bytes in memory."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_encrypted_pdf(text: str, password: str = "secret123") -> bytes:
    """Helper to generate encrypted/password-protected PDF bytes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    # Encrypt using PyMuPDF AES-256
    pdf_bytes = doc.write(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw=password
    )
    doc.close()
    return pdf_bytes


def test_valid_digital_pdf_extraction():
    page1_text = "Master Services Agreement. Section 1. Term and Termination." + " " * 50
    page2_text = "Section 2. Confidentiality and Data Security Obligations." + " " * 50
    
    pdf_bytes = create_synthetic_pdf([page1_text, page2_text])

    files = {"file": ("test_contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_pages"] == 2
    assert data["ocr_required_pages_count"] == 0
    assert data["is_encrypted"] is False
    assert "Master Services Agreement" in data["full_text"]
    assert len(data["pages"]) == 2
    assert data["pages"][0]["page_number"] == 1
    assert data["pages"][0]["ocr_required"] is False
    assert data["pages"][1]["page_number"] == 2
    assert data["pages"][1]["ocr_required"] is False


def test_scanned_page_ocr_heuristic_flag():
    normal_page = "This is a full legal text page with adequate characters." * 5
    short_image_page = "Short"  # 5 characters < 50 threshold

    pdf_bytes = create_synthetic_pdf([normal_page, short_image_page])

    files = {"file": ("scanned_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["total_pages"] == 2
    assert data["ocr_required_pages_count"] == 1
    assert data["pages"][0]["ocr_required"] is False
    assert data["pages"][1]["ocr_required"] is True


def test_encrypted_pdf_rejection_r12():
    encrypted_bytes = create_encrypted_pdf("Confidential text", password="secret_pass_123")

    files = {"file": ("encrypted.pdf", io.BytesIO(encrypted_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "ENCRYPTED_PDF_REJECTED"
    assert "Password-protected or encrypted PDFs are not supported" in data["error"]["message"]


def test_corrupted_pdf_safe_failure():
    corrupted_bytes = b"%PDF-1.4\n1 0 obj\n<<Corrupted Garbage Bytes Stream>>\nendobj\ntrailer\n"

    files = {"file": ("corrupt.pdf", io.BytesIO(corrupted_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CORRUPTED_PDF"


def test_empty_pdf_file_rejection():
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMPTY_PDF_FILE"


def test_exceeds_20mb_file_size_limit_r11():
    # 21 MB synthetic bytes stream with PDF header
    over_size_bytes = b"%PDF-1.4\n" + b"X" * (21 * 1024 * 1024)

    files = {"file": ("large_file.pdf", io.BytesIO(over_size_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EXCEEDS_FILE_SIZE_LIMIT"
    assert "exceeds maximum allowed limit of 20 MB" in data["error"]["message"]
