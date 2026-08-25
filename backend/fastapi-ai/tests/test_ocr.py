"""
OCR Service Unit Tests
"""

import pytest
from PIL import Image, ImageDraw
from app.services.ocr_service import get_tesseract_status, extract_text_from_image, DEFAULT_OCR_DPI


def test_tesseract_status():
    status = get_tesseract_status()
    assert status["installed"] is True
    assert status["version"] is not None
    assert status["default_dpi"] == 300


def test_extract_text_from_image():
    # Render a clean image with text
    img = Image.new("RGB", (600, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), "ClarifAI Contract Clause OCR Test", fill=(0, 0, 0))

    extracted = extract_text_from_image(img, lang="eng", dpi=DEFAULT_OCR_DPI)
    assert "ClarifAI" in extracted or "Contract" in extracted or "Clause" in extracted
