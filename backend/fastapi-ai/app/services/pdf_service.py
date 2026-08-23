"""
ClarifAI PDF Validation, PyMuPDF Extraction & Adaptive OCR Pipeline Service
Handles PDF file validation, size limits (Decision R-11), encryption rejection (Decision R-12),
digital text extraction, and selective page-level Tesseract OCR processing.
"""

import io
import fitz  # PyMuPDF
import logging
from typing import Dict, Any, List
from PIL import Image
from fastapi import HTTPException, status
from app.services.ocr_service import extract_text_from_image

logger = logging.getLogger(__name__)

# Defense-in-depth maximum PDF file size limit (20 MB) per Decision R-11
MAX_PDF_SIZE_BYTES: int = 20 * 1024 * 1024

# Scanned page OCR threshold: pages with < 50 non-whitespace characters are flagged as needing OCR
OCR_CHARACTER_THRESHOLD: int = 50

# Render DPI for converting PyMuPDF pages to images for Tesseract OCR
OCR_RENDER_DPI: int = 150

SCHEMA_VERSION: str = "1.0.0"


def extract_pdf_text_service(pdf_bytes: bytes, enable_ocr: bool = True) -> Dict[str, Any]:
    """
    Validates PDF file, checks for encryption, extracts digital text per page using PyMuPDF,
    evaluates scanned OCR heuristics, and selectively runs Tesseract OCR for flagged pages.
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

    # 6. First Pass: Digital Extraction & Scanned Heuristic Evaluation
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
    ocr_required_count: int = 0

    for page_idx in range(total_pages):
        page = doc.load_page(page_idx)
        raw_text = page.get_text("text") or ""
        stripped_text = raw_text.strip()
        
        non_ws_char_count = len("".join(stripped_text.split()))

        # Evaluate scanned/image OCR heuristic threshold
        ocr_required = non_ws_char_count < OCR_CHARACTER_THRESHOLD
        if ocr_required:
            ocr_required_count += 1

        pages_list.append({
            "page_number": page_idx + 1,
            "text": raw_text,
            "character_count": non_ws_char_count,
            "ocr_required": ocr_required,
            "ocr_performed": False,
            "extraction_method": "digital"
        })

    # 7. Second Pass: Selective OCR Execution for Flagged Pages ONLY
    ocr_performed_count: int = 0

    if enable_ocr and ocr_required_count > 0:
        logger.info(f"Selective OCR Triggered: {ocr_required_count} of {total_pages} pages flagged for OCR.")
        
        for page_item in pages_list:
            if not page_item["ocr_required"]:
                continue

            page_idx = page_item["page_number"] - 1
            page = doc.load_page(page_idx)

            # Render PyMuPDF page to in-memory pixmap image
            pix = page.get_pixmap(dpi=OCR_RENDER_DPI)
            img_bytes = pix.tobytes("png")
            
            # Create PIL image stream in memory
            pil_image = Image.open(io.BytesIO(img_bytes))

            try:
                ocr_text = extract_text_from_image(pil_image, dpi=OCR_RENDER_DPI)
            except Exception as ocr_err:
                doc.close()
                pix = None
                pil_image.close()
                logger.error(f"Tesseract OCR failed on page {page_idx + 1}: {ocr_err}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "OCR_EXTRACTION_FAILED",
                        "message": f"Tesseract OCR extraction failed on scanned page {page_idx + 1}."
                    }
                )

            # Immediate in-memory image cleanup
            pil_image.close()
            pix = None
            img_bytes = None

            stripped_ocr = (ocr_text or "").strip()
            ocr_non_ws_count = len("".join(stripped_ocr.split()))

            # Validate OCR output: fail safely if OCR yielded no usable text
            if ocr_non_ws_count == 0:
                doc.close()
                logger.warning(f"OCR produced 0 usable characters for scanned page {page_idx + 1}.")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "OCR_EXTRACTION_FAILED",
                        "message": f"OCR produced no usable text for scanned page {page_idx + 1}."
                    }
                )

            # Update page extraction metadata
            page_item["text"] = ocr_text
            page_item["character_count"] = ocr_non_ws_count
            page_item["ocr_performed"] = True
            page_item["extraction_method"] = "ocr"
            ocr_performed_count += 1

    doc.close()

    # 8. Merge Page-Ordered Text & Determine Overall Extraction Method
    full_text_parts: List[str] = []
    for item in pages_list:
        t = item["text"].strip()
        if t:
            full_text_parts.append(t)

    full_text = "\n\n".join(full_text_parts)

    if ocr_performed_count == 0:
        overall_method = "digital"
    elif ocr_performed_count == total_pages:
        overall_method = "ocr"
    else:
        overall_method = "hybrid"

    logger.info(
        f"PDF Extraction Complete: Total Pages = {total_pages}, "
        f"Method = '{overall_method}', OCR Performed = {ocr_performed_count}, Total Chars = {len(full_text)}"
    )

    return {
        "success": True,
        "total_pages": total_pages,
        "ocr_required_pages_count": ocr_required_count,
        "ocr_performed_pages_count": ocr_performed_count,
        "extraction_method": overall_method,
        "full_text": full_text,
        "pages": pages_list,
        "file_size_bytes": file_size_bytes,
        "is_encrypted": False,
        "schema_version": SCHEMA_VERSION
    }
