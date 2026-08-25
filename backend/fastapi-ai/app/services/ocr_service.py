"""
ClarifAI Tesseract OCR Service Module
Handles adaptive per-page OCR extraction for scanned PDF pages.
Configured per PRD v2.3 Chapters 14, 15, 28.1, and Section 19.
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

# Default page-render resolution (DPI) for converting PDF pages to images for OCR
DEFAULT_OCR_DPI: int = 300

# Default languages for OCR (English + Hindi per PRD Section 19)
DEFAULT_OCR_LANG: str = "eng+hin"


def configure_tesseract_path() -> Optional[str]:
    """
    Configures and discovers the Tesseract executable path.
    1. Checks explicit TESSERACT_CMD environment variable.
    2. Checks system PATH.
    3. Checks standard Windows installation fallback if running on Windows.
    """
    cmd = os.getenv("TESSERACT_CMD")
    if cmd and os.path.exists(cmd):
        pytesseract.pytesseract.tesseract_cmd = cmd
        return cmd

    # Check system PATH
    system_binary = shutil.which("tesseract")
    if system_binary:
        pytesseract.pytesseract.tesseract_cmd = system_binary
        return system_binary

    # Windows fallback search
    if os.name == "nt":
        win_fallback = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(win_fallback):
            pytesseract.pytesseract.tesseract_cmd = win_fallback
            return win_fallback

    return None


# Execute configuration on module import
_tesseract_bin_path = configure_tesseract_path()


def get_tesseract_status() -> Dict[str, Any]:
    """
    Returns diagnostic status of Tesseract binary and pytesseract binding.
    """
    bin_path = configure_tesseract_path()
    if not bin_path:
        return {
            "installed": False,
            "version": None,
            "path": None,
            "error": "Tesseract binary not found in PATH or TESSERACT_CMD."
        }

    try:
        version_str = pytesseract.get_tesseract_version().public
        return {
            "installed": True,
            "version": version_str,
            "path": bin_path,
            "default_dpi": DEFAULT_OCR_DPI,
            "default_lang": DEFAULT_OCR_LANG,
        }
    except Exception as e:
        logger.error(f"Tesseract status check failed: {e}")
        return {
            "installed": False,
            "version": None,
            "path": bin_path,
            "error": str(e)
        }


def extract_text_from_image(
    image: Image.Image,
    lang: str = DEFAULT_OCR_LANG,
    dpi: int = DEFAULT_OCR_DPI
) -> str:
    """
    Performs OCR text extraction on a PIL Image object.
    
    Args:
        image: PIL Image instance (e.g. rendered PDF page).
        lang: Tesseract language string (default: "eng+hin").
        dpi: Target image render resolution (default: 300 DPI).
        
    Returns:
        Extracted plain text string.
    """
    if not configure_tesseract_path():
        raise RuntimeError("Tesseract binary is not installed or configured on system PATH.")

    # Configure custom psm/oem options if needed
    config_flags = f"--dpi {dpi}"
    
    try:
        extracted_text = pytesseract.image_to_string(
            image,
            lang=lang,
            config=config_flags
        )
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"OCR text extraction failed: {e}")
        # Try fallback to English if combined eng+hin pack encounters missing language data
        if lang != "eng":
            logger.info("Retrying OCR with fallback language 'eng'...")
            return pytesseract.image_to_string(image, lang="eng", config=config_flags).strip()
        raise e
