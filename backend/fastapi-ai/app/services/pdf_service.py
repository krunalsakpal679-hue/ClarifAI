"""
ClarifAI PDF Validation & PyMuPDF Extraction Service
Handles PDF file validation, size limits (Decision R-11), encryption rejection (Decision R-12),
digital text extraction, and scanned page OCR heuristic detection.
"""

import fitz  # PyMuPDF
import logging
from typing import Dict, Any, List
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Defense-in-depth maximum PDF file size limit (20 MB) per Decision R-11
MAX_PDF_SIZE_BYTES: int = 20 * 1024 * 1024

# Scanned page OCR threshold: pages with < 50 non-whitespace characters are flagged as needing OCR
OCR_CHARACTER_THRESHOLD: int = 50

SCHEMA_VERSION: str = "1.0.0"


def extract_pdf_text_service(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Validates PDF file, checks for encryption, extracts text per page using PyMuPDF,
    and flags pages needing OCR via character count heuristic.
    """
    file_size_bytes = len(pdf_bytes)

    # 1. Empty File Check
    if file_size_bytes == 0:
        logger.warning("PDF extraction failed: Empty byte stream provided.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_PDF_FILE",
                "message": "Uploaded PDF file is empty (0 bytes)."
            }
        )

    # 2. File Size Limit Check (Decision R-11)
    if file_size_bytes > MAX_PDF_SIZE_BYTES:
        size_mb = file_size_bytes / (1024 * 1024)
        logger.warning(f"PDF extraction rejected: File size ({size_mb:.2f} MB) exceeds 20 MB limit.")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "EXCEEDS_FILE_SIZE_LIMIT",
                "message": f"PDF file size ({size_mb:.2f} MB) exceeds maximum allowed limit of 20 MB."
            }
        )

    # 3. Magic Bytes Header Validation (%PDF-)
    if not pdf_bytes.startswith(b"%PDF-"):
        logger.warning("PDF extraction rejected: Missing %PDF- magic header.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PDF_FORMAT",
                "message": "Uploaded file is not a valid PDF document (invalid magic header)."
            }
        )

    # 4. Open PDF Document with PyMuPDF
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"PyMuPDF failed to parse document stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "CORRUPTED_PDF",
                "message": "Failed to parse PDF document. File appears to be corrupted or unreadable."
            }
        )

    # 5. Encryption / Password Protection Check (Decision R-12)
    if doc.is_encrypted or doc.needs_pass:
        doc.close()
        logger.warning("PDF extraction rejected: Document is password-protected or encrypted.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ENCRYPTED_PDF_REJECTED",
                "message": "Password-protected or encrypted PDFs are not supported. Please remove encryption and re-upload."
            }
        )

    # 6. Extract Text & Evaluate Per-Page OCR Heuristic
    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "CORRUPTED_PDF",
                "message": "PDF contains 0 pages."
            }
        )

    pages_list: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []
    ocr_required_count: int = 0

    for page_idx in range(total_pages):
        page = doc.load_page(page_idx)
        raw_text = page.get_text("text") or ""
        stripped_text = raw_text.strip()
        
        # Calculate non-whitespace character count
        non_ws_char_count = len("".join(stripped_text.split()))

        # Evaluate scanned/image OCR heuristic threshold
        ocr_required = non_ws_char_count < OCR_CHARACTER_THRESHOLD
        if ocr_required:
            ocr_required_count += 1

        pages_list.append({
            "page_number": page_idx + 1,  # 1-indexed for user readability
            "text": raw_text,
            "character_count": non_ws_char_count,
            "ocr_required": ocr_required
        })

        if stripped_text:
            full_text_parts.append(stripped_text)

    doc.close()
    full_text = "\n\n".join(full_text_parts)

    logger.info(
        f"PDF Extraction Complete: Total Pages = {total_pages}, "
        f"OCR Required Pages = {ocr_required_count}, Total Chars = {len(full_text)}"
    )

    return {
        "success": True,
        "total_pages": total_pages,
        "ocr_required_pages_count": ocr_required_count,
        "full_text": full_text,
        "pages": pages_list,
        "file_size_bytes": file_size_bytes,
        "is_encrypted": False,
        "schema_version": SCHEMA_VERSION
    }
