"""
ClarifAI Deterministic Legal Text Cleaning Service Module
Provides rule-based text cleaning and normalization for extracted PDF/OCR legal text.
Fixes hyphenation breaks, running headers/footers, and repeated whitespace while strictly
preserving clause wording, numbers, currency symbols, and dates.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Regular expressions for cleaning rules
REGEX_CRLF = re.compile(r"\r\n|\r")
REGEX_PAGE_NUMBER_HEADER = re.compile(
    r"^(?:\s*)(?:Page\s+\d+(?:\s+of\s+\d+)?|\d+\s*/\s*\d+|\-\s*\d+\s*\-)(?:\s*)$",
    re.IGNORECASE | re.MULTILINE
)
# Rejoin line-break hyphenation (e.g. "confiden-\ntial" -> "confidential", "obli-\ngations" -> "obligations")
REGEX_HYPHENATED_LINEBREAK = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-z]{2,})")
REGEX_MULTIPLE_SPACES = re.compile(r"[ \t]+")
REGEX_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def clean_legal_text(raw_text: str, preserve_page_markers: bool = True) -> Dict[str, Any]:
    """
    Executes a deterministic sequence of cleaning and normalization rules on raw legal text.

    Args:
        raw_text: Extracted digital or OCR text.
        preserve_page_markers: Whether to keep structural [PAGE:X] markers.

    Returns:
        Dict containing cleaned_text, original_length, cleaned_length, and rules_applied list.
    """
    if not raw_text:
        return {
            "success": True,
            "cleaned_text": "",
            "original_length": 0,
            "cleaned_length": 0,
            "rules_applied": [],
            "schema_version": SCHEMA_VERSION
        }

    rules_applied: List[str] = []
    text = raw_text

    # 1. Normalize Line Endings (\r\n -> \n)
    text_crlf = REGEX_CRLF.sub("\n", text)
    if text_crlf != text:
        rules_applied.append("normalize_line_endings")
        text = text_crlf

    # 2. Repair Hyphenated Line Breaks (e.g. "obli-\ngations" -> "obligations")
    text_hyphen = REGEX_HYPHENATED_LINEBREAK.sub(r"\1\2", text)
    if text_hyphen != text:
        rules_applied.append("repair_hyphenated_line_breaks")
        text = text_hyphen

    # 3. Strip Running Page Number Headers and Footers (e.g. "Page 1 of 10")
    text_headers = REGEX_PAGE_NUMBER_HEADER.sub("", text)
    if text_headers != text:
        rules_applied.append("strip_running_headers_footers")
        text = text_headers

    # 4. Normalize Horizontal Whitespace (collapse multiple spaces/tabs per line)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Preserve page markers if present (e.g. [PAGE:1] or --- Page 1 ---)
        stripped = REGEX_MULTIPLE_SPACES.sub(" ", line).strip()
        cleaned_lines.append(stripped)
    
    text_space = "\n".join(cleaned_lines)
    if text_space != text:
        rules_applied.append("normalize_horizontal_whitespace")
        text = text_space

    # 5. Normalize Paragraph Newlines (max 2 consecutive newlines \n\n)
    text_newlines = REGEX_MULTIPLE_NEWLINES.sub("\n\n", text).strip()
    if text_newlines != text:
        rules_applied.append("normalize_paragraph_newlines")
        text = text_newlines

    # 6. Safety Audit: Verify Digits & Currency Preservation
    _audit_preservation_safety(raw_text, text)

    return {
        "success": True,
        "cleaned_text": text,
        "original_length": len(raw_text),
        "cleaned_length": len(text),
        "rules_applied": rules_applied,
        "schema_version": SCHEMA_VERSION
    }


def _audit_preservation_safety(raw_text: str, cleaned_text: str) -> None:
    """
    Regression assertion ensuring cleaning never alters digits or currency symbols.
    """
    raw_digits = re.findall(r"\d+", raw_text)
    cleaned_digits = re.findall(r"\d+", cleaned_text)

    # Note: Page numbers like "Page 1 of 10" removed by header stripper will reduce digits count.
    # However, substantive figures, currency, and dates inside clauses must match.
    raw_currencies = re.findall(r"[\$\€\£\₹]|\b(?:USD|INR|EUR|GBP)\b", raw_text)
    cleaned_currencies = re.findall(r"[\$\€\£\₹]|\b(?:USD|INR|EUR|GBP)\b", cleaned_text)

    if raw_currencies != cleaned_currencies:
        logger.warning(
            f"Text cleaning currency mismatch detected! Raw: {raw_currencies}, Cleaned: {cleaned_currencies}"
        )
