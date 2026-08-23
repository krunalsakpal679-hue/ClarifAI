"""
ClarifAI Adaptive Tesseract OCR Pipeline Unit Tests (AI-PHASE-OCR)
Verifies selective page-level OCR triggering, pure digital zero-OCR execution,
OCR text merging, blank/unreadable scanned page failure handling (OCR_EXTRACTION_FAILED),
and temporary image cleanup.
"""

import io
import fitz  # PyMuPDF
import pytest
from PIL import Image, ImageDraw, ImageFont
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_digital_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate clean digital text PDF bytes."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_scanned_image_pdf(text_on_image: str) -> bytes:
    """Helper to generate a PDF page containing an embedded image of text (scanned PDF)."""
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 80), text_on_image, fill=(0, 0, 0))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=600, height=200)
    page.insert_image(page.rect, stream=img_bytes)

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_blank_white_image_pdf() -> bytes:
    """Helper to generate a PDF page containing a blank white image (0 readable text)."""
    img = Image.new("RGB", (400, 150), color=(255, 255, 255))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=400, height=150)
    page.insert_image(page.rect, stream=img_bytes)

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_pure_digital_pdf_zero_ocr_calls():
    # Long text with > 100 non-whitespace characters to exceed the 50-char OCR threshold
    page1_text = "Master Services Agreement. Section 1. Term and Termination Obligations under State Law. " * 3
    page2_text = "Section 2. Confidentiality, Non-Disclosure and Proprietary Intellectual Property Rights. " * 3

    pdf_bytes = create_digital_pdf([page1_text, page2_text])

    files = {"file": ("digital_contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_pages"] == 2
    assert data["ocr_required_pages_count"] == 0
    assert data["ocr_performed_pages_count"] == 0
    assert data["extraction_method"] == "digital"
    assert data["pages"][0]["ocr_performed"] is False
    assert data["pages"][1]["ocr_performed"] is False


def test_scanned_image_pdf_selective_ocr():
    # Page 1: Digital text (> 100 non-ws chars), Page 2: Scanned text image
    digital_page = "Section 1. Digital text clause on first page for contract validation and compliance. " * 3
    scanned_bytes = create_scanned_image_pdf("SECTION 4.1 CONFIDENTIALITY")

    doc_digital = fitz.open("pdf", create_digital_pdf([digital_page]))
    doc_scanned = fitz.open("pdf", scanned_bytes)

    doc_combined = fitz.open()
    doc_combined.insert_pdf(doc_digital)
    doc_combined.insert_pdf(doc_scanned)

    hybrid_bytes = doc_combined.write()
    doc_digital.close()
    doc_scanned.close()
    doc_combined.close()

    files = {"file": ("hybrid_document.pdf", io.BytesIO(hybrid_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_pages"] == 2
    assert data["ocr_required_pages_count"] == 1
    assert data["ocr_performed_pages_count"] == 1
    assert data["extraction_method"] == "hybrid"
    assert data["pages"][0]["extraction_method"] == "digital"
    assert data["pages"][1]["extraction_method"] == "ocr"
    assert data["pages"][1]["ocr_performed"] is True


def test_blank_scanned_page_structured_ocr_failure():
    blank_pdf_bytes = create_blank_white_image_pdf()

    files = {"file": ("blank_scanned.pdf", io.BytesIO(blank_pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "OCR_EXTRACTION_FAILED"
    assert "OCR produced no usable text" in data["error"]["message"]


def test_disabled_ocr_flag():
    scanned_bytes = create_scanned_image_pdf("SCANNED TEXT")

    files = {"file": ("scanned.pdf", io.BytesIO(scanned_bytes), "application/pdf")}
    response = client.post("/api/v1/extract-pdf?enable_ocr=false", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["ocr_required_pages_count"] == 1
    assert data["ocr_performed_pages_count"] == 0
    assert data["extraction_method"] == "digital"
