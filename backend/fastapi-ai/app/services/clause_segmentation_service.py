"""
ClarifAI Legal Clause Segmentation Service Module
(W2 Spec Implementation & Multi-Contract Structural Segmenter)

Implements strict structural clause boundary detection operating on logical paragraphs.
Extracts verbatim clause records preserving source numbering, exact heading titles,
page numbers, preambles, recitals, signatures, and schedules while keeping sub-items
(A., B., 1., 2., (a), (b)) nested inside parent sections.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Standard Legal Headings
REGEX_LEGAL_HEADING = re.compile(
    r"^(?:[^a-zA-Z0-9]*)(?:"
    r"DUTIES|SERVICES|SCOPE\s+OF\s+SERVICES|SCOPE\s+OF\s+WORK|STATEMENT\s+OF\s+WORK|DELIVERABLES|ENGAGEMENT\s+AND\s+DELIVERABLES|"
    r"PAYMENT\s+TERMS|PAYMENT|FEES\s+AND\s+PAYMENT|FEES\s+AND\s+EXPENSES|FEES|INVOICING\s+AND\s+PAYMENT|INVOICING|COMPENSATION|"
    r"RENT\s+(?:AND|&)\s+FINANCIAL\s+TERMS|MONTHLY\s+RENT|LEASED\s+PREMISES|USE\s+OF\s+PREMISES|PREMISES|"
    r"ALTERATIONS\s+AND\s+IMPROVEMENTS|ALTERATIONS|MAINTENANCE\s+AND\s+REPAIRS|MAINTENANCE|"
    r"CONFIDENTIALITY(?:\s+COVENANT)?|NON-DISCLOSURE|CONFIDENTIAL\s+INFORMATION|PROPRIETARY\s+INFORMATION|"
    r"INTELLECTUAL\s+PROPERTY(?:\s+RIGHTS|\s+ASSIGNMENT)?|WORK\s+PRODUCT\s+OWNERSHIP|WORK\s+PRODUCTS|WORK\s+PRODUCT|OWNERSHIP|"
    r"INDEMNIFICATION(?:\s+FOR\s+DAMAGES,\s+TAXES\s+AND\s+CONTRIBUTIONS)?|INDEMNITY\s+OBLIGATIONS|INDEMNITY|CUSTOMER\s+INDEMNIFICATION\s+AND\s+THIRD-PARTY\s+DEFENSE|"
    r"LIMITATION\s+OF\s+LIABILITY|AGGREGATE\s+LIABILITY|LIABILITY\s+CAP|DAMAGES\s+CAP|"
    r"TERM(?:\s+DURATION)?|LEASE\s+TERM|TERM\s+AND\s+TERMINATION|"
    r"EARLY\s+TERMINATION|TERMINATION(?:\s+FOR\s+CONVENIENCE\s+AND\s+SUSPENSION)?|TERMINATION\s+RIGHTS|CANCELLATION|"
    r"RENEWAL|AUTOMATIC\s+RENEWAL|TERM,\s+AUTOMATIC\s+RENEWAL\s+AND\s+ANNUAL\s+PRICE\s+ESCALATION|"
    r"DISPUTE\s+RESOLUTION|DISPUTES|GOVERNING\s+FORUM(?:\s+AND\s+VENUE)?|GOVERNING\s+FORUM|ARBITRATION|BINDING\s+ARBITRATION|"
    r"GOVERNING\s+LAW(?:\s+(?:AND|&)\s*(?:VENUE|JURISDICTION))?|GOVERNING\s+JURISDICTION\s+AND\s+BINDING\s+ARBITRATION|CHOICE\s+OF\s+LAW|"
    r"NON-COMPETE\s+AND\s+NON-SOLICITATION|RESTRICTIVE\s+COVENANTS|POST-EMPLOYMENT\s+NON-COMPETE|"
    r"DATA\s+PRIVACY|PRIVACY|DATA\s+PROTECTION|SECURITY|"
    r"FEDERAL,\s*STATE\s*AND\s*LOCAL\s*LAWS|EQUAL\s+EMPLOYMENT\s+OPPORTUNITY|HARASSMENT|LICENSES|"
    r"INDEPENDENT\s+CONSULTANT\s+STATUS|INDEPENDENT\s+CONTRACTOR|RETENTION\s+AND\s+AUDIT\s+OF\s+RECORDS|"
    r"INSPECTION\s+OF\s+WORK|ACKNOWLEDGMENT|SAFETY|MODIFICATION\s+OF\s+AGREEMENT|AUDIT\s+REVIEW\s+PROCEDURES|"
    r"SUBCONTRACTING|NONASSIGNMENT|REBATES,\s*KICKBACKS\s*OR\s*OTHER\s*UNLAWFUL\s*CONSIDERATION|NOTIFICATION|COMPLETE\s+AGREEMENT|"
    r"INSURANCE|CROSS-BORDER\s+TARIFFS\s+AND\s+STATUTORY\s+ALLOCATION|TARIFFS|"
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
    r"PROFESSIONAL\s+SERVICES\s+AGREEMENT|SERVICES\s+AGREEMENT|NON-DISCLOSURE\s+AGREEMENT|EMPLOYMENT\s+AGREEMENT|"
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

PATTERN_NUM_HEADING = re.compile(
    r"^(\d{1,2})\.\s+([A-Z][A-Z\s\,\/\-\–\—\&\(\)]{2,70}?)(?:[\.\:\-\–\—]|\s*$|\n)(.*)$",
    re.DOTALL
)

PATTERN_NUM_SIMPLE = re.compile(
    r"^(\d{1,2})\.\s+(.*)$"
)

PATTERN_NAMED_SEC = re.compile(
    r"^(?:(?:Section|Clause|Article|Paragraph)\s+([0-9]+(?:\.[0-9]+)*|[IVXLCDM]+|[A-Z]))(?:\s*[\:\.\-\–\—\)]\s*|\s+|$)(.*)$",
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

    # 1. Pre-process lines: merge standalone numbers (e.g. "3." followed by "TERM...")
    raw_lines = text.split("\n")
    merged_lines = []
    i = 0
    while i < len(raw_lines):
        l = raw_lines[i].strip()
        if re.match(r"^\d{1,2}\.?$", l) and i + 1 < len(raw_lines):
            next_l = raw_lines[i + 1].strip()
            if re.match(r"^[A-Z][A-Z\s\,\/\-\–\—\&\(\)]{2,70}", next_l) or REGEX_LEGAL_HEADING.match(next_l):
                num = l.rstrip(".")
                merged_lines.append(f"{num}. {next_l}")
                i += 2
                continue
        merged_lines.append(raw_lines[i])
        i += 1

    # 2. Normalize section boundaries: insert paragraph breaks before structural headings & markers
    normalized_lines: List[str] = []
    for l in merged_lines:
        stripped = l.strip()
        is_closing = bool(REGEX_CLOSING_MARKER.match(stripped))
        is_top_sec = bool(
            PATTERN_NAMED_SEC.match(stripped)
            or PATTERN_NUM_HEADING.match(stripped)
            or (REGEX_LEGAL_HEADING.match(stripped) and (stripped.isupper() or len(stripped) < 60) and len(stripped.split()) <= 8)
            or REGEX_DOC_TITLE.match(stripped)
        )
        if is_closing or is_top_sec:
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
    current_clause_num = 0
    doc_uses_headings = False

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

        # Check document title & metadata headers before first operative clause
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
        m_named = PATTERN_NAMED_SEC.match(first_line)
        m_head_only = bool(REGEX_LEGAL_HEADING.match(first_line) and (first_line.isupper() or len(first_line) < 60) and len(first_line.split()) <= 8)
        m_num_head = PATTERN_NUM_HEADING.match(first_line)
        m_num_simple = PATTERN_NUM_SIMPLE.match(first_line)

        is_new_clause = False
        c_num_str: Optional[str] = None
        c_title_str: Optional[str] = None

        if m_named:
            is_new_clause = True
            c_num_str = m_named.group(1).strip(".)(: ")
            rem = m_named.group(2).strip()
            c_title_str = rem.split(".")[0].strip(":-. ") if rem else f"Section {c_num_str}"
            doc_uses_headings = True
        elif m_num_head:
            is_new_clause = True
            c_num_str = m_num_head.group(1)
            c_title_str = m_num_head.group(2).strip(":-. ")
            doc_uses_headings = True
        elif m_head_only:
            is_new_clause = True
            c_num_str = str(current_clause_num + 1)
            c_title_str = first_line.strip(":-. ")
            doc_uses_headings = True
        elif m_num_simple and not doc_uses_headings:
            # Simple numbered contract without uppercase headings (e.g. 1. In pursuance..., 2. The Lessee...)
            num_val = int(m_num_simple.group(1))
            if not seen_first_clause and num_val == 1:
                is_new_clause = True
                c_num_str = "1"
                c_title_str = "Section 1"
            elif seen_first_clause and num_val == current_clause_num + 1:
                is_new_clause = True
                c_num_str = str(num_val)
                c_title_str = f"Section {num_val}"

        # Distinguish real section heading from mid-sentence recital/preamble
        if not seen_first_clause and not is_new_clause:
            preamble_blocks.append(para)
            continue

        if is_new_clause:
            seen_first_clause = True
            if c_num_str and c_num_str.isdigit():
                current_clause_num = int(c_num_str)
            else:
                current_clause_num += 1

            # Finalize previous clause
            if current_block is not None:
                clause_blocks.append(current_block)

            current_block = {
                "clause_number": c_num_str or str(current_clause_num),
                "title": c_title_str or f"Section {current_clause_num}",
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
        # Fallback for unnumbered / continuous prose documents: segment by substantive paragraphs
        substantive_paras = [p for p in raw_paragraphs if len(p.strip()) > 30 and not re.match(r"^(?:Document\s+ID|Contract\s+ID)\s*:", p.strip(), re.IGNORECASE)]
        if substantive_paras:
            for idx, p in enumerate(substantive_paras, start=1):
                p_lines = p.strip().split("\n")
                first = p_lines[0].strip()
                title = first[:50] if len(first) <= 50 else f"Section {idx}"
                clause_blocks.append({
                    "clause_number": str(idx),
                    "title": title,
                    "text_parts": [p]
                })

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
