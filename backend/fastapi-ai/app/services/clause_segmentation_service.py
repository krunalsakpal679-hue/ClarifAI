"""
ClarifAI Legal Clause Segmentation Service Module
Implements rule-based + lightweight regex NLP clause boundary detection.
Segments cleaned document text into an ordered list of verbatim clause records
preserving position, source numbering, title, and page traceability.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Regex for explicit legal section markers (e.g. "Section 1.", "Clause 4.2", "Article III", "1.1 ", "1) ")
REGEX_SECTION_MARKER = re.compile(
    r"^(?:\s*)(?:"
    r"(?:Section|Clause|Article|Paragraph)\s+([0-9]+(?:\.[0-9]+)*|[A-Z]+)"
    r"|([0-9]+(?:\.[0-9]+){1,3})"
    r"|([0-9]{1,2}\.|\([0-9a-zA-Z]{1,2}\))"
    r")(?:\s*[\:\.\-\–\—]\s*|\s+)(.*)$",
    re.IGNORECASE
)

# Regex for common legal headings (e.g. "INDEMNIFICATION", "GOVERNING LAW", "LIMITATION OF LIABILITY")
REGEX_LEGAL_HEADING = re.compile(
    r"^(?:\s*)(?:"
    r"INDEMNIFICATION|CONFIDENTIALITY|TERMINATION|LIMITATION OF LIABILITY|"
    r"GOVERNING LAW|JURISDICTION|PAYMENT TERMS|INTELLECTUAL PROPERTY|"
    r"WARRANTIES|DISCLAIMER|SEVERABILITY|ENTIRE AGREEMENT|NOTICES|"
    r"FORCE MAJEURE|NON-COMPETE|NON-SOLICITATION|ASSIGNMENT|DEFINITIONS|"
    r"SCOPE OF SERVICES|DATA PROTECTION|FEES AND PAYMENT"
    r")(?:\s*[\:\.\-\–\—]\s*|\s*$)",
    re.IGNORECASE
)


def segment_document_clauses(
    text: str,
    pages: Optional[List[dict]] = None
) -> Dict[str, Any]:
    """
    Segments cleaned legal document text into an ordered list of verbatim clause records.

    Args:
        text: Cleaned document text string.
        pages: Optional list of per-page text items for page-number mapping.

    Returns:
        Dict containing total_clauses, clauses list, and schema_version.
    """
    if not text or not text.strip():
        logger.warning("Clause segmentation rejected: Empty text provided.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document contains zero usable legal text or clauses."
            }
        )

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document text contains zero paragraphs or usable clauses."
            }
        )

    clause_blocks: List[Dict[str, Any]] = []
    current_block: Optional[Dict[str, Any]] = None

    for para in paragraphs:
        lines = para.split("\n")
        first_line = lines[0].strip()

        section_match = REGEX_SECTION_MARKER.match(first_line)
        heading_match = REGEX_LEGAL_HEADING.match(first_line)

        is_new_clause_boundary = bool(section_match or heading_match)

        if is_new_clause_boundary or current_block is None:
            # Finalize previous clause block
            if current_block is not None and current_block["lines"]:
                clause_text = "\n".join(current_block["lines"]).strip()
                if len("".join(clause_text.split())) >= 15:
                    current_block["text"] = clause_text
                    clause_blocks.append(current_block)

            # Start new clause block
            clause_num: Optional[str] = None
            clause_title: Optional[str] = None

            if section_match:
                # Extract number group
                groups = section_match.groups()
                clause_num = groups[0] or groups[1] or groups[2]
                if clause_num:
                    clause_num = clause_num.strip(".)")
                remaining_text = groups[3] or ""
                if remaining_text:
                    clause_title = remaining_text.split(".")[0].strip()
            elif heading_match:
                clause_title = first_line.strip(":-.")

            current_block = {
                "clause_number": clause_num,
                "title": clause_title,
                "lines": [para]
            }
        else:
            # Append paragraph to ongoing clause block
            current_block["lines"].append(para)

    # Append final block
    if current_block is not None and current_block["lines"]:
        clause_text = "\n".join(current_block["lines"]).strip()
        if len("".join(clause_text.split())) >= 15:
            current_block["text"] = clause_text
            clause_blocks.append(current_block)

    # Validate output: raise structured failure on zero clauses
    if not clause_blocks:
        logger.warning("Clause segmentation produced 0 valid clause blocks.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document contains zero usable legal clauses."
            }
        )

    # Build final verbatim ClauseItem payload
    clauses: List[Dict[str, Any]] = []
    for idx, block in enumerate(clause_blocks, start=1):
        verbatim_text = block["text"]
        char_count = len("".join(verbatim_text.split()))

        # Infer page number from page reference list if provided
        page_num: Optional[int] = None
        if pages:
            for page_item in pages:
                p_text = page_item.get("text", "")
                if verbatim_text[:40] in p_text:
                    page_num = page_item.get("page_number")
                    break

        clauses.append({
            "position": idx,
            "clause_number": block["clause_number"],
            "title": block["title"],
            "text": verbatim_text,
            "character_count": char_count,
            "page_number": page_num
        })

    logger.info(f"Clause Segmentation Complete: {len(clauses)} clauses segmented successfully.")

    return {
        "success": True,
        "total_clauses": len(clauses),
        "clauses": clauses,
        "schema_version": SCHEMA_VERSION
    }
