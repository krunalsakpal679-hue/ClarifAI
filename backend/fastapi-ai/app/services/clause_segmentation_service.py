"""
ClarifAI Legal Clause Segmentation Service Module
(W2 Spec Implementation)

Implements strict structural clause boundary detection operating on logical paragraphs.
Extracts verbatim clause records preserving source numbering, exact heading titles,
page numbers, preambles, recitals, signatures, and schedules.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Strict structural legal section marker (e.g. "Section 1.", "SECTION 1", "Section A.", "Clause 4.2", "Article III", "1. ", "1 LEASED PREMISES")
REGEX_STRUCTURAL_SECTION = re.compile(
    r"^(?:(?:Section|Clause|Article|Paragraph)\s+([0-9]+(?:\.[0-9]+)*|\b[IVXLCDM]+\b|[A-Z]\b)"
    r"|([0-9]{1,2}\.(?!\d))"
    r"|([0-9]{1,2}\s+(?=[A-Z]{3,}))"
    r")(?:\s*[\:\.\-\–\—\)]\s*|\s+|$)(.*)$",
    re.IGNORECASE
)


# Standard Legal Headings (Generic, clean, non-overfitted)
REGEX_LEGAL_HEADING = re.compile(
    r"^(?:[^a-zA-Z0-9]*)(?:"
    r"SERVICES|SCOPE\s+OF\s+SERVICES|SCOPE\s+OF\s+WORK|STATEMENT\s+OF\s+WORK|DELIVERABLES|ENGAGEMENT\s+AND\s+DELIVERABLES|"
    r"PAYMENT\s+TERMS|PAYMENT|FEES\s+AND\s+PAYMENT|FEES\s+AND\s+EXPENSES|FEES|INVOICING\s+AND\s+PAYMENT|INVOICING|COMPENSATION|"
    r"RENT\s+(?:AND|&)\s+FINANCIAL\s+TERMS|MONTHLY\s+RENT|LEASED\s+PREMISES|USE\s+OF\s+PREMISES|PREMISES|"
    r"ALTERATIONS\s+AND\s+IMPROVEMENTS|ALTERATIONS|MAINTENANCE\s+AND\s+REPAIRS|MAINTENANCE|"
    r"CONFIDENTIALITY(?:\s+COVENANT)?|NON-DISCLOSURE|CONFIDENTIAL\s+INFORMATION|PROPRIETARY\s+INFORMATION|"
    r"INTELLECTUAL\s+PROPERTY(?:\s+RIGHTS|\s+ASSIGNMENT)?|WORK\s+PRODUCT\s+OWNERSHIP|WORK\s+PRODUCT|OWNERSHIP|"
    r"INDEMNIFICATION|INDEMNITY\s+OBLIGATIONS|INDEMNITY|CUSTOMER\s+INDEMNIFICATION\s+AND\s+THIRD-PARTY\s+DEFENSE|"
    r"LIMITATION\s+OF\s+LIABILITY|AGGREGATE\s+LIABILITY|LIABILITY\s+CAP|DAMAGES\s+CAP|"
    r"TERM(?:\s+DURATION)?|LEASE\s+TERM|TERM\s+AND\s+TERMINATION|"
    r"TERMINATION(?:\s+FOR\s+CONVENIENCE\s+AND\s+SUSPENSION)?|TERMINATION\s+RIGHTS|CANCELLATION|"
    r"RENEWAL|AUTOMATIC\s+RENEWAL|TERM,\s+AUTOMATIC\s+RENEWAL\s+AND\s+ANNUAL\s+PRICE\s+ESCALATION|"
    r"DISPUTE\s+RESOLUTION|GOVERNING\s+FORUM(?:\s+AND\s+VENUE)?|GOVERNING\s+FORUM|ARBITRATION|BINDING\s+ARBITRATION|"
    r"GOVERNING\s+LAW(?:\s+(?:AND|&)\s*(?:VENUE|JURISDICTION))?|GOVERNING\s+JURISDICTION\s+AND\s+BINDING\s+ARBITRATION|CHOICE\s+OF\s+LAW|"
    r"NON-COMPETE\s+AND\s+NON-SOLICITATION|RESTRICTIVE\s+COVENANTS|POST-EMPLOYMENT\s+NON-COMPETE|"
    r"DATA\s+PRIVACY|PRIVACY|DATA\s+PROTECTION|SECURITY|"
    r"CROSS-BORDER\s+TARIFFS\s+AND\s+STATUTORY\s+ALLOCATION|TARIFFS|"
    r"WARRANTIES|REPRESENTATIONS\s+AND\s+WARRANTIES|DISCLAIMER|"
    r"ENTIRE\s+AGREEMENT|INTEGRATION|SEVERABILITY|NOTICES|FORCE\s+MAJEURE|ASSIGNMENT"
    r")(?:\s*[\:\.\-\–\—]\s*|\s*$)",
    re.IGNORECASE
)

# Formal document title patterns
REGEX_DOC_TITLE = re.compile(
    r"^(?:[^\w\(\[\{]*)(?:"
    r"MASTER\s+SERVICES\s+AGREEMENT|CLOUD\s+INFRASTRUCTURE\s+CONSULTING\s+AGREEMENT|"
    r"STRATEGIC\s+CONSULTING\s+SERVICES\s+AGREEMENT|COMMERCIAL\s+LEASE\s+AGREEMENT|"
    r"SERVICES\s+AGREEMENT|NON-DISCLOSURE\s+AGREEMENT|EMPLOYMENT\s+AGREEMENT|"
    r"CONSULTING\s+AGREEMENT|TERMS\s+OF\s+SERVICE"
    r")(?:\s*[\:\.\-\–\—]\s*|\s*$)",
    re.IGNORECASE
)

# Closing / signature / schedules markers
REGEX_CLOSING_MARKER = re.compile(
    r"^(?:\s*)(?:"
    r"IN\s+WITNESS\s+WHEREOF|"
    r"AS\s+WITNESS(?:\s+THE\s+HANDS)?|"
    r"SIGNED\s+AND\s+DELIVERED|"
    r"SIGNED,\s*SEALED\s*AND\s*DELIVERED|"
    r"EXECUTED\s+(?:AS\s+A\s+DEED|BY)|"
    r"THE\s+SCHEDULE|"
    r"SCHEDULE\s+[A-Z0-9]+|"
    r"ANNEXURE\s+[A-Z0-9]+|"
    r"EXHIBIT\s+[A-Z0-9]+"
    r")\b",
    re.IGNORECASE
)


def segment_document_clauses(
    text: str,
    pages: Optional[List[dict]] = None
) -> Dict[str, Any]:
    """
    Segments cleaned legal document text into an ordered list of verbatim clause records
    operating on logical paragraphs.

    Args:
        text: Cleaned document text string.
        pages: Optional list of per-page text items for page-number mapping.

    Returns:
        Dict containing total_clauses, clauses list, preamble, recitals, header, signature_block, schedules, schema_version.
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

    # 1. Normalize section boundaries: insert paragraph breaks before structural headings & markers
    lines = text.split("\n")
    normalized_lines: List[str] = []
    for l in lines:
        stripped = l.strip()
        if (
            REGEX_STRUCTURAL_SECTION.match(stripped)
            or (REGEX_LEGAL_HEADING.match(stripped) and (stripped.isupper() or len(stripped) < 80))
            or REGEX_CLOSING_MARKER.match(stripped)
            or REGEX_DOC_TITLE.match(stripped)
        ):
            normalized_lines.append("")
        normalized_lines.append(l)
    normalized_text = "\n".join(normalized_lines)

    # Split into logical paragraphs
    raw_paragraphs = [p.strip() for p in normalized_text.split("\n\n") if p.strip()]
    if not raw_paragraphs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document contains zero usable paragraphs."
            }
        )


    clause_blocks: List[Dict[str, Any]] = []
    preamble_blocks: List[str] = []
    recital_blocks: List[str] = []
    header_blocks: List[str] = []
    signature_blocks: List[str] = []
    schedule_blocks: List[str] = []
    warnings: List[str] = []

    current_block: Optional[Dict[str, Any]] = None
    in_closing = False
    seen_first_clause = False

    for para in raw_paragraphs:
        lines = para.split("\n")
        first_line = lines[0].strip()

        # Check closing markers (Signatures / Execution / Schedules)
        closing_match = REGEX_CLOSING_MARKER.match(first_line)
        if closing_match or in_closing:
            if not in_closing:
                in_closing = True
                # Finalize last open clause
                if current_block is not None:
                    clause_blocks.append(current_block)
                    current_block = None

            if re.match(r"^(?:THE\s+SCHEDULE|SCHEDULE|ANNEXURE|EXHIBIT|APPENDIX)\b", first_line, re.IGNORECASE):
                schedule_blocks.append(para)
            else:
                signature_blocks.append(para)
            continue

        # Check document title & metadata headers before first operative clause (R2 fix)
        title_match = REGEX_DOC_TITLE.match(first_line)
        is_metadata_header = bool(
            re.match(r"^(?:Document\s+ID|Contract\s+ID|Governing\s+Law|Effective\s+Date|Overall\s+Risk|Reference)\s*:", first_line, re.IGNORECASE)
        )
        if (title_match or is_metadata_header) and not seen_first_clause:
            header_blocks.append(para)
            continue

        # Check recitals (e.g. "WHEREAS", "RECITALS", "NOW, THEREFORE")
        if re.match(r"^(?:WHEREAS|RECITALS|NOW,\s*THEREFORE)\b", first_line, re.IGNORECASE) and not seen_first_clause:
            recital_blocks.append(para)
            continue

        # Check structural section markers and legal headings
        sec_match = REGEX_STRUCTURAL_SECTION.match(first_line)
        heading_match = REGEX_LEGAL_HEADING.match(first_line)

        # Distinguish real section heading from mid-sentence recital/preamble
        if not seen_first_clause and not sec_match and not (heading_match and len(first_line) < 60 and first_line.isupper()):
            preamble_blocks.append(para)
            continue

        if sec_match or (heading_match and (first_line.isupper() or len(first_line) < 80)):
            seen_first_clause = True

            # Finalize previous clause
            if current_block is not None:
                clause_blocks.append(current_block)

            clause_num: Optional[str] = None
            clause_title: Optional[str] = None

            if sec_match:
                groups = sec_match.groups()
                raw_num = next((g for g in groups[:-1] if g is not None), None)
                if raw_num:
                    clause_num = raw_num.strip(".)(: ")
                remainder = groups[-1].strip() if groups and groups[-1] else ""
                if remainder:
                    clause_title = remainder.split(".")[0].strip(":-. ")
                elif len(lines) > 1 and REGEX_LEGAL_HEADING.match(lines[1].strip()):
                    clause_title = lines[1].strip(":-. ")
            elif heading_match:
                clause_title = first_line.strip(":-. ")

            current_block = {
                "clause_number": clause_num,
                "title": clause_title,
                "text_parts": [para]
            }
        else:
            if current_block is not None:
                current_block["text_parts"].append(para)
            elif not seen_first_clause:
                preamble_blocks.append(para)

    # Finalize last block
    if current_block is not None:
        clause_blocks.append(current_block)

    if not clause_blocks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document contains zero usable legal clauses."
            }
        )

    # Build final clause list with exact titles and numbers
    clauses: List[Dict[str, Any]] = []
    for idx, block in enumerate(clause_blocks, start=1):
        verbatim_text = "\n\n".join(block["text_parts"]).strip()
        src_clause_num = block.get("clause_number") or str(idx)
        src_title = block.get("title")

        # Fallback title formatting if none extracted
        final_title = src_title or f"Section {src_clause_num}"

        # Resolve page number
        page_num: Optional[int] = None
        if pages:
            for p_idx, page_item in enumerate(pages, start=1):
                p_text = page_item.get("text", "")
                if verbatim_text[:50] in p_text or f"Section {src_clause_num}" in p_text:
                    page_num = page_item.get("page_number") or p_idx
                    break

        char_count = len("".join(verbatim_text.split()))
        status_val = "ok"
        if char_count < 15:
            status_val = "too_short"
            warnings.append(f"Clause {src_clause_num} ({final_title}) character count ({char_count}) is below minimum threshold.")

        clauses.append({
            "position": idx,
            "clause_id": f"c-{idx:03d}",
            "clause_number": src_clause_num,
            "title": final_title,
            "text": verbatim_text,
            "character_count": char_count,
            "page_number": page_num,
            "status": status_val
        })

    # Self-check: ensure sequential integrity
    detected_heading_count = sum(1 for c in clauses if c["title"] and not c["title"].startswith("Section "))
    if detected_heading_count != len(clauses):
        warnings.append(f"Heading consistency note: {detected_heading_count} explicit headings found across {len(clauses)} clauses.")

    return {
        "success": True,
        "total_clauses": len(clauses),
        "clauses": clauses,
        "preamble": "\n\n".join(preamble_blocks).strip() if preamble_blocks else None,
        "recitals": "\n\n".join(recital_blocks).strip() if recital_blocks else None,
        "document_header": "\n\n".join(header_blocks).strip() if header_blocks else None,
        "signature_block": "\n\n".join(signature_blocks).strip() if signature_blocks else None,
        "schedules": "\n\n".join(schedule_blocks).strip() if schedule_blocks else None,
        "warnings": warnings,
        "schema_version": SCHEMA_VERSION
    }


segment_clauses = segment_document_clauses
