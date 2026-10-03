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

# Regex for explicit legal section markers (e.g. "Section 1.", "Section A.", "Clause 4.2", "Article III", "1.1 ", "1) ", "1. ", "1 LEASED", "{3}", "6 TOTAL")
REGEX_SECTION_MARKER = re.compile(
    r"^(?:[^\w\(\[\{]*)(?:"
    r"(?:Section|Clause|Article|Paragraph)\s+([0-9]+(?:\.[0-9]+)*|[A-Za-z]+|\b[IVXLCDM]+\b)"
    r"|([0-9]+(?:\.[0-9]+){1,3}(?!\d))"
    r"|([0-9]{1,3}\.(?!\d))"
    r"|([0-9]{1,3}(?=\s+[A-Za-z]{3,}))"
    r"|([0-9]{1,3}(?=[A-Z]{3,}))"
    r"|(\b[IVXLCDM]+\b\.)"
    r"|([A-Z]\.\s+)"
    r"|(\([0-9]{1,2}\)|\([a-zA-Z]\))"
    r"|(\{[0-9]{1,2}\})"
    r")(?:\s*[\:\.\-\–\—\)]\s*|\s+|$)(.*)$",
    re.IGNORECASE
)

# Regex for common legal headings across all contract and agreement types
REGEX_LEGAL_HEADING = re.compile(
    r"^(?:[^a-zA-Z0-9]*)(?:"
    r"PAYMENT\s+TERMS|PAYMENT|FEES\s+AND\s+PAYMENT|FEES\s+AND\s+EXPENSES|FEES|COMPENSATION(?:\s+AND\s+PERFORMANCE\s+BONUS)?|"
    r"POSITION\s+AND\s+(?:OPERATIONAL\s+)?DUTIES|DUTIES\s+AND\s+RESPONSIBILITIES|EMPLOYMENT\s+DUTIES|"
    r"PRINCIPAL\s+LOAN\s+COMMITMENT|PRINCIPAL\s+LOAN|INTEREST\s+RATE(?:\s+AND\s+REPAYMENT\s+SCHEDULE)?|"
    r"FINANCIAL\s+COVENANTS(?:\s+AND\s+DEBT\s+SERVICE)?|DEBT\s+SERVICE|PREPAYMENT\s+PREMIUMS?|PREPAYMENT|"
    r"ACCELERATION(?:\s+AND\s+REMEDIES(?:\s+ON\s+DEFAULT)?)?|EVENTS?\s+OF\s+DEFAULT|"
    r"SUBSCRIPTION\s+GRANT(?:\s+AND\s+ACCESS\s+RIGHTS)?|LICENSE\s+GRANT|ACCESS\s+RIGHTS|"
    r"SERVICE\s+AVAILABILITY(?:\s+AND\s+SERVICE\s+CREDITS)?|SERVICE\s+LEVEL\s+AGREEMENT|SERVICE\s+CREDITS?|"
    r"DISCLAIMER\s+OF\s+CONSEQUENTIAL\s+DAMAGES|AGGREGATE\s+(?:MONETARY\s+)?LIABILITY(?:\s+LIMITATION)?|"
    r"UNILATERAL\s+MODIFICATION(?:\s+OF\s+TERMS)?|MODIFICATION\s+OF\s+TERMS|"
    r"PURCHASE\s+ORDERS(?:\s+AND\s+LEAD\s+TIMES)?|PRICE\s+ADJUSTMENTS(?:\s+AND\s+CURRENCY)?|"
    r"PRODUCT\s+WARRANTY(?:\s+AND\s+DEFECT\s+REMEDIES)?|WARRANTY\s+AND\s+REMEDIES|"
    r"PATENT\s+INFRINGEMENT(?:\s+AND\s+PRODUCT\s+INDEMNIFICATION)?|"
    r"LEASED\s+EQ(?:UI|U|I)?PMENT(?:\s+AND\s+T[A-Z]+\s+DURATION)?|MONTHLY\s+RENT(?:AL)?(?:\s+AND\s+SECU?RITY\s+DEPOSIT)?|"
    r"(?:EQ(?:UI|U|I)?PMENT\s+)?MA[I]?NTENAN?CE(?:\s+(?:AND|ANO)\s*REPA[I]?R?S?)?|MA[I]?NTENAN?CE\s+AND\s+REPAIRS?|"
    r"[I1ln]?NSURAN?CE(?:\s+(?:A[NU]D|AUO)?\s*CASUALTY(?:\s*INDEMNITY|INOENITY)?)?|"
    r"TOTAL\s*CASUALTY\s*LOSS(?:\s+AND\s+FEPLACEMENTVALUE|\s+AND\s+REPLACEMENT\s+VALUE)?|"
    r"POST-EMPLOYMENT\s+NON-COMPETE(?:\s+COVENANT)?|NON-COMPETE(?:\s+COVENANT)?|"
    r"TERMINATION\s+AND\s+SEVERANCE(?:\s+ENTITLEMENT)?|TERMINATION(?:\s+RIGHTS)?|TERM\s+AND\s+TERMINATION|"
    r"CANCELLATION|EXPIRATION|SURVIVAL|"
    r"CONFIDENTIALITY|NON-DISCLOSURE|CONFIDENTIAL\s+INFORMATION|PROPRIETARY\s+RIGHTS|PROPRIETARY\s+INFORMATION|"
    r"LIMITATION\s+OF\s+LIABILITY|LIABILITY|DAMAGES\s+CAP|"
    r"INDEMNIFICATION|INDEMNITY|DEFENSE\s+AND\s+INDEMNIFICATION|HOLD\s+HARMLESS|"
    r"INTELLECTUAL\s+PROPERTY(?:\s+ASSIGNMENT)?|INTELLECTUAL\s+PROPERTY\s+RIGHTS|IP\s+RIGHTS|WORK\s+MADE\s+FOR\s+HIRE|OWNERSHIP|"
    r"GOVER?N(?:ING|ERNG)?\s+LAW(?:\s+(?:A[NU]D|AND|AWO)\s*(?:JURISDICTION|VENUE|COURT\s*VENUE))?|GOVERNING\s+FORUM(?:\s+AND\s+VENUE)?|JURISDICTION|VENUE|"
    r"APPLICABLE\s+LAW(?:\s+AND\s+JUDICIAL\s+JURISDICTION)?|"
    r"DISPUTE\s+RESOLUTION|ARBITRATION|BINDING\s+ARBITRATION(?:\s+AND\s+CLASS\s+ACTION\s+WAIVER)?|"
    r"RENEWAL|TERM\s+AND\s+RENEWAL|EXTENSION|"
    r"PRIVACY|DATA\s+PROTECTION|DATA\s+PROTECTION\s+AND\s+PRIVACY|DATA\s+PROCESSING|SECURITY|INFORMATION\s+SECURITY|"
    r"WARRANTIES|REPRESENTATIONS\s+AND\s+WARRANTIES|DISCLAIMER\s+OF\s+WARRANTIES|DISCLAIMER|LIMITED\s+WARRANTY|"
    r"SEVERABILITY|ENTIRE\s+AGREEMENT|INTEGRATION|NOTICES|AMENDMENTS|MODIFICATIONS|"
    r"FORCE\s+MAJEURE|NON-SOLICITATION|RESTRICTIVE\s+COVENANTS|"
    r"ASSIGNMENT|SUCCESSORS\s+AND\s+ASSIGNS|SUBCONTRACTING|"
    r"DEFINITIONS|DEFINED\s+TERMS|INTERPRETATION|"
    r"SCOPE\s+OF\s+SERVICES|SCOPE\s+OF\s+WORK|SERVICES|STATEMENT\s+OF\s+WORK|DELIVERABLES|DUTIES|"
    r"INSURANCE|AUDIT\s+RIGHTS|AUDIT|TAXES|RELATIONSHIP\s+OF\s+PARTIES|MISCELLANEOUS|GENERAL\s+PROVISIONS"
    r")(?:\s*[\:\.\-\–\—\,\;]\s*|\s*$)",
    re.IGNORECASE
)

# Regex for formal document titles (to prevent title headers from masquerading as clauses)
REGEX_DOC_TITLE = re.compile(
    r"^(?:[^\w\(\[\{]*)(?:"
    r"MASTER\s+SERVICES\s+AGREEMENT|SERVICES\s+AGREEMENT|NON-DISCLOSURE\s+AGREEMENT|"
    r"EXECUTIVE\s+EMPLOYMENT\s+AGREEMENT|EMPLOYMENT\s+AGREEMENT|LEASE\s+AGREEMENT|RESIDENTIAL\s+LEASE\s+AGREEMENT|"
    r"COMMERCIAL\s+LEASE\s+AGREEMENT|COMMERCIAL\s+TERM\s+LOAN\s+AGREEMENT|COMMERCIAL\s+LOAN\s+AGREEMENT|"
    r"HEAVY\s+INDUSTRIAL\s+EQUIPMENT\s+LEASE\s+AGREEMENT|EQUIPMENT\s+LEASE\s+AGREEMENT|INDENTURE\s+OF\s+LEASE|"
    r"STRATEGIC\s+COMPONENT\s+SUPPLY\s+AGREEMENT|COMPONENT\s+SUPPLY\s+AGREEMENT|SUPPLY\s+AGREEMENT|"
    r"CLOUD\s+WORKSPACE\s+TERMS\s+OF\s+SERVICE|TERMS\s+OF\s+SERVICE|TERMS\s+AND\s+CONDITIONS|"
    r"CONSULTING\s+AGREEMENT|VENDOR\s+AGREEMENT|PURCHASE\s+AGREEMENT|LOAN\s+AGREEMENT|PARTNERSHIP\s+AGREEMENT|"
    r"PRIVACY\s+POLICY|DATA\s+PROCESSING\s+AGREEMENT"
    r")(?:\s*[\:\.\-\–\—]\s*|\s*$)",
    re.IGNORECASE
)

# Regex for closing / execution / signature / schedule markers
REGEX_CLOSING_MARKER = re.compile(
    r"^(?:\s*)(?:"
    r"IN\s+WITNESS\s+WHEREOF|"
    r"AS\s+WITNESS(?:\s+THE\s+HANDS)?|"
    r"SIGNED\s+AND\s+DELIVERED|"
    r"SIGNED,\s*SEALED\s*AND\s*DELIVERED|"
    r"EXECUTED\s+(?:AS\s+A\s+DEED|BY)|"
    r"THE\s+SCHEDULE(?:\s+ABOVE|\s+HEREUNDER)?\s+REFERRED\s+TO|"
    r"SCHEDULE\s+[A-Z0-9]+|"
    r"ANNEXURE\s+[A-Z0-9]+|"
    r"EXHIBIT\s+[A-Z0-9]+|"
    r"APPENDIX\s+[A-Z0-9]+"
    r")\b",
    re.IGNORECASE
)


def segment_document_clauses(
    text: str,
    pages: Optional[List[dict]] = None
) -> Dict[str, Any]:
    """
    Segments cleaned legal document text into an ordered list of verbatim clause records.
    Distinguishes titles, preambles/recitals, table-of-contents, and signature blocks
    from operative legal clauses across all supported contract structures.

    Args:
        text: Cleaned document text string.
        pages: Optional list of per-page text items for page-number mapping.

    Returns:
        Dict containing total_clauses, clauses list, preamble, signature_block, and schema_version.
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

    # Normalize section boundaries: ensure paragraph break before explicit section/heading/closing markers
    lines = text.split("\n")
    normalized_lines: List[str] = []
    for l in lines:
        stripped = l.strip()
        if (
            REGEX_SECTION_MARKER.match(stripped)
            or REGEX_LEGAL_HEADING.match(stripped)
            or REGEX_CLOSING_MARKER.match(stripped)
        ):
            normalized_lines.append("")
        normalized_lines.append(l)
    normalized_text = "\n".join(normalized_lines)

    paragraphs = [p.strip() for p in normalized_text.split("\n\n") if p.strip()]
    if not paragraphs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ZERO_CLAUSES_DETECTED",
                "message": "Document text contains zero paragraphs or usable clauses."
            }
        )

    # Check if document contains explicit operative section markers or legal headings
    has_operative_markers = any(
        bool(
            (REGEX_SECTION_MARKER.match(p.split("\n")[0].strip()) or REGEX_LEGAL_HEADING.match(p.split("\n")[0].strip()))
            and not REGEX_DOC_TITLE.match(p.split("\n")[0].strip())
        )
        for p in paragraphs
    )

    clause_blocks: List[Dict[str, Any]] = []
    preamble_lines: List[str] = []
    signature_lines: List[str] = []
    current_block: Optional[Dict[str, Any]] = None
    in_closing = False
    seen_first_clause = False

    if has_operative_markers:
        for para in paragraphs:
            lines = para.split("\n")
            first_line = lines[0].strip()

            closing_match = REGEX_CLOSING_MARKER.match(first_line)
            title_match = REGEX_DOC_TITLE.match(first_line)
            section_match = REGEX_SECTION_MARKER.match(first_line)
            heading_match = REGEX_LEGAL_HEADING.match(first_line)

            # If document title appears before first clause, assign to preamble
            if title_match and not seen_first_clause:
                preamble_lines.append(para)
                continue

            if in_closing or closing_match:
                if not in_closing:
                    in_closing = True
                    # Finalize last operative clause
                    if current_block is not None and current_block["lines"]:
                        clause_text = "\n".join(current_block["lines"]).strip()
                        if len("".join(clause_text.split())) >= 15:
                            current_block["text"] = clause_text
                            clause_blocks.append(current_block)
                        current_block = None
                signature_lines.append(para)
                continue

            if section_match or heading_match:
                seen_first_clause = True
                # Finalize previous operative clause block
                if current_block is not None and current_block["lines"]:
                    clause_text = "\n".join(current_block["lines"]).strip()
                    if len("".join(clause_text.split())) >= 15:
                        current_block["text"] = clause_text
                        clause_blocks.append(current_block)

                clause_num: Optional[str] = None
                clause_title: Optional[str] = None

                if section_match:
                    groups = section_match.groups()
                    raw_num = next((g for g in groups[:-1] if g is not None), None)
                    if raw_num:
                        clause_num = raw_num.strip(".)(: ")
                    remaining_text = groups[-1] if groups and groups[-1] else ""
                    if remaining_text:
                        raw_title = remaining_text.split(".")[0].strip()
                        if len(raw_title) <= 80:
                            clause_title = raw_title
                        else:
                            clause_title = raw_title[:77].strip() + "..."
                elif heading_match:
                    clause_title = first_line.strip(":-.")

                current_block = {
                    "clause_number": clause_num,
                    "title": clause_title,
                    "lines": [para]
                }
            else:
                if not seen_first_clause:
                    # Collect into preamble / recitals
                    preamble_lines.append(para)
                else:
                    if current_block is not None:
                        current_block["lines"].append(para)

        # Finalize final block if not in closing
        if current_block is not None and current_block["lines"]:
            clause_text = "\n".join(current_block["lines"]).strip()
            if len("".join(clause_text.split())) >= 15:
                current_block["text"] = clause_text
                clause_blocks.append(current_block)

    else:
        # Fallback for documents without explicit numbering or headings
        for para in paragraphs:
            clause_blocks.append({
                "clause_number": None,
                "title": None,
                "text": para,
                "lines": [para]
            })

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

        src_clause_num = block.get("clause_number")
        src_title = block.get("title")

        clauses.append({
            "position": idx,
            "clause_id": f"c-{idx:03d}",
            "clause_number": src_clause_num if src_clause_num is not None else None,
            "title": src_title or (f"Clause {src_clause_num}" if src_clause_num else f"Section {idx}"),
            "text": verbatim_text,
            "character_count": char_count,
            "page_number": page_num
        })

    logger.info(f"Clause Segmentation Complete: {len(clauses)} clauses segmented successfully.")

    preamble_text = "\n\n".join(preamble_lines).strip() if preamble_lines else None
    signature_text = "\n\n".join(signature_lines).strip() if signature_lines else None

    return {
        "success": True,
        "total_clauses": len(clauses),
        "clauses": clauses,
        "preamble": preamble_text,
        "signature_block": signature_text,
        "schema_version": SCHEMA_VERSION
    }
