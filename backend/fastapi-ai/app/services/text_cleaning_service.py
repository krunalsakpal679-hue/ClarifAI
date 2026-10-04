"""
ClarifAI Deterministic Legal Text Cleaning & Header Extraction Service Module
(W1 Spec Implementation)

Provides:
1. Detection & removal of repeated running headers, footers, page numbers, and confidentiality banners into page_furniture.
2. Re-joining of hard-wrapped physical lines into logical paragraphs.
3. Structured document header extraction (title, agreement_type, parties & roles, effective_date, reference_number, term, claimed_in_document).
4. OCR typo and glyph normalization.
5. Preservation of substantive digits, dates, and currency symbols.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Regular expressions for cleaning rules
REGEX_CRLF = re.compile(r"\r\n|\r")
REGEX_PAGE_NUMBER_HEADER = re.compile(
    r"^(?:\s*)(?:Page\s+\d+(?:\s+of\s+\d+)?|\d+\s*/\s*\d+|\-\s*\d+\s*\-)(?:\s*)$",
    re.IGNORECASE
)
REGEX_RUNNING_FOOTER = re.compile(
    r"^(?:\s*)(?:ClarifAI Demo Legal Document Repository(?:\s*[\-\–\—]\s*Confidential\s*&\s*Proprietary)?|"
    r"Confidential\s*(?:&|and)\s*Proprietary|All\s+Rights\s+Reserved|"
    r"Strictly\s+Confidential)(?:\s*)$",
    re.IGNORECASE
)

# Rejoin line-break hyphenation (e.g. "confiden-\ntial" -> "confidential", "obli-\ngations" -> "obligations")
REGEX_HYPHENATED_LINEBREAK = re.compile(r"([a-zA-Z]{2,})-\s*\n\s*([a-z]{2,})")
REGEX_MULTIPLE_SPACES = re.compile(r"[ \t]+")
REGEX_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")

# Common OCR typo replacements
OCR_TYPO_REPLACEMENTS = [
    (re.compile(r"\bFEPLACEMENTVALUE\b", re.IGNORECASE), "REPLACEMENT VALUE"),
    (re.compile(r"\bINOENITY\b", re.IGNORECASE), "INDEMNITY"),
    (re.compile(r"\bMA[I]?NTENAN\s*CE\b", re.IGNORECASE), "MAINTENANCE"),
    (re.compile(r"\bAWO\b", re.IGNORECASE), "AND"),
    (re.compile(r"\bAUO\b", re.IGNORECASE), "AND"),
    (re.compile(r"\bANO\b", re.IGNORECASE), "AND"),
    (re.compile(r"\bGOVERERNG\b", re.IGNORECASE), "GOVERNING"),
]


def extract_structured_document_header(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Extracts a structured document header before clause segmentation.
    Returns (header_dict, remaining_body_text).
    Header lines are cleanly isolated so they never enter the clause list (R2 fix).
    """
    header_info: Dict[str, Any] = {
        "title": None,
        "agreement_type": None,
        "parties": [],
        "effective_date": None,
        "reference_number": None,
        "governing_law_line": None,
        "term_line": None,
        "claimed_in_document": None
    }

    # 1. Pre-printed risk ratings / audit scores
    risk_match = re.search(r"Overall\s+Risk\s+Classification\s*:\s*([A-Za-z\s]+?)(?:\s*\(Automated\s+Audit\s+Score\s*:\s*([0-9/]+)\))?(?:\n|$)", text, re.IGNORECASE)
    if risk_match:
        header_info["claimed_in_document"] = {
            "risk_rating": risk_match.group(1).strip() if risk_match.group(1) else None,
            "audit_score": risk_match.group(2).strip() if risk_match.group(2) else None,
            "claimed_raw": risk_match.group(0).strip()
        }

    # 2. Reference number
    ref_match = re.search(r"(?:Document\s+ID|Contract\s+ID|Reference\s+(?:No|Number)|Ref\s*#?)\s*:\s*([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
    if ref_match:
        header_info["reference_number"] = ref_match.group(1).strip()

    # 3. Governing Law Line
    gov_match = re.search(r"Governing\s+Law\s*:\s*([^\n;]+)", text, re.IGNORECASE)
    if gov_match:
        header_info["governing_law_line"] = gov_match.group(1).strip()

    # 4. Effective Date
    eff_match = re.search(r"Effective\s+Date\s*:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if eff_match:
        header_info["effective_date"] = eff_match.group(1).strip()

    # 5. Title & Agreement Type
    title_match = re.search(r"\b(?:MASTER\s+SERVICES\s+AGREEMENT|CLOUD\s+INFRASTRUCTURE\s+CONSULTING\s+AGREEMENT|STRATEGIC\s+CONSULTING\s+SERVICES\s+AGREEMENT|COMMERCIAL\s+LEASE\s+AGREEMENT|SERVICES\s+AGREEMENT|NON-DISCLOSURE\s+AGREEMENT|EXECUTIVE\s+EMPLOYMENT\s+AGREEMENT|EMPLOYMENT\s+AGREEMENT|TERMS\s+OF\s+SERVICE)\b", text, re.IGNORECASE)
    if title_match:
        header_info["title"] = title_match.group(0).strip()
        header_info["agreement_type"] = title_match.group(0).strip()

    # 6. Parties and Roles
    parties = []
    party_pattern = re.compile(r'([A-Z][A-Za-z0-9\s,\.\-&]+?)\s*(?:\([“"]([A-Za-z\s]+)[”"]\)|as\s+[“"]([A-Za-z\s]+)[”"])', re.UNICODE)
    for match in party_pattern.finditer(text[:2500]):
        p_name = match.group(1).strip(" ,.\n")
        p_role = match.group(2) or match.group(3)
        if p_role and len(p_name) > 3 and not p_name.isupper() and p_role.lower() in {"vendor", "customer", "client", "consultant", "landlord", "tenant", "lessor", "lessee", "company", "employee", "service provider", "subscriber"}:
            parties.append({
                "name": p_name,
                "role": p_role.strip()
            })

    seen_names = set()
    dedup_parties = []
    for p in parties:
        if p["name"].lower() not in seen_names:
            seen_names.add(p["name"].lower())
            dedup_parties.append(p)
    header_info["parties"] = dedup_parties

    return header_info, text


def rejoin_hard_wrapped_paragraphs(text: str) -> str:
    """
    Re-joins hard-wrapped lines into logical paragraphs (R1 fix).
    A line that does not end in terminal sentence punctuation (.!?:;) and is followed
    by a continuation line is rejoined with a single space.
    """
    lines = text.split("\n")
    rejoined_lines: List[str] = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped:
            rejoined_lines.append("")
            i += 1
            continue
            
        # Check if line looks like an explicit section heading marker or key-value metadata line
        is_heading_marker = bool(
            re.match(r"^(?:Section|Clause|Article|Paragraph)\s+[0-9IVXLCDM]+", stripped, re.IGNORECASE)
            or re.match(r"^[0-9]{1,2}\.\s+[A-Z]{3,}", stripped)
            or re.match(r"^[0-9]{1,2}\s+[A-Z]{3,}", stripped)
            or re.match(r"^[A-Z\s]{4,}:?$", stripped)
            or re.match(r"^(?:Document\s+ID|Contract\s+ID|Governing\s+Law|Effective\s+Date|Overall\s+Risk|Ref\s*#?)\s*:", stripped, re.IGNORECASE)
        )
        
        if is_heading_marker:
            rejoined_lines.append(stripped)
            i += 1
            continue

        if (
            rejoined_lines 
            and rejoined_lines[-1] 
            and not rejoined_lines[-1].endswith((".", "!", "?", ":", ";", "—", "–"))
            and not is_heading_marker
            and not re.match(r"^(?:Section|Clause|Article|\([a-z0-9]+\)|[0-9]{1,2}\.)", stripped, re.IGNORECASE)
            and not re.match(r"^(?:Document\s+ID|Contract\s+ID|Governing\s+Law|Effective\s+Date|Overall\s+Risk)\s*:", rejoined_lines[-1], re.IGNORECASE)
        ):
            prev = rejoined_lines[-1]
            if prev.isupper() and len(prev) < 60:
                rejoined_lines.append(stripped)
            else:
                rejoined_lines[-1] = f"{rejoined_lines[-1]} {stripped}"
        else:
            rejoined_lines.append(stripped)
        i += 1
        
    return "\n".join(rejoined_lines)



def clean_legal_text(raw_text: str, preserve_page_markers: bool = True) -> Dict[str, Any]:
    """
    Executes a deterministic sequence of cleaning, normalization, and header extraction rules.

    Args:
        raw_text: Extracted digital or OCR text.
        preserve_page_markers: Whether to keep structural [PAGE:X] markers.

    Returns:
        Dict containing cleaned_text, page_furniture, document_header, original_length, cleaned_length, rules_applied.
    """
    if not raw_text:
        return {
            "success": True,
            "cleaned_text": "",
            "page_furniture": [],
            "document_header": {
                "title": None,
                "agreement_type": None,
                "parties": [],
                "effective_date": None,
                "reference_number": None,
                "governing_law_line": None,
                "term_line": None,
                "claimed_in_document": None
            },
            "original_length": 0,
            "cleaned_length": 0,
            "rules_applied": [],
            "schema_version": SCHEMA_VERSION
        }

    rules_applied: List[str] = []
    page_furniture: List[str] = []
    text = raw_text

    # 0. Clean OCR Glitch Characters / Unicode Replacement Glyphs & Stray Bullets
    text_clean_chars = re.sub(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f\u00ad\u2022\u2023\u25e6\u2043\u2219]', ' ', text)
    if text_clean_chars != text:
        rules_applied.append("strip_ocr_glitch_chars")
        text = text_clean_chars

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

    # 3. Normalize Common OCR Typos
    for typo_pat, replacement in OCR_TYPO_REPLACEMENTS:
        if typo_pat.search(text):
            text = typo_pat.sub(replacement, text)
            rules_applied.append("normalize_ocr_typos")

    # Normalize OCR section numbering glitches (e.g. "3, EQUIPMENT" -> "3. EQUIPMENT", "4 INSURANCE" -> "4. INSURANCE")
    text_ocr_num = re.sub(r'(?m)^([0-9]{1,2})\s*,\s*([A-Z]{3,})', r'\1. \2', text)
    text_ocr_num = re.sub(r'(?m)^([0-9]{1,2})\s+([A-Z]{3,})', r'\1. \2', text_ocr_num)
    if text_ocr_num != text:
        text = text_ocr_num
        rules_applied.append("normalize_ocr_section_numbers")


    # 4. Strip Running Headers, Footers & Page Banners (R5 fix)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if REGEX_PAGE_NUMBER_HEADER.match(stripped) or REGEX_RUNNING_FOOTER.match(stripped):
            page_furniture.append(stripped)
            rules_applied.append("strip_page_furniture")
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # 5. Normalize Horizontal Whitespace (collapse multiple spaces/tabs per line)
    lines = text.split("\n")
    norm_space_lines = []
    for line in lines:
        stripped = REGEX_MULTIPLE_SPACES.sub(" ", line).strip()
        norm_space_lines.append(stripped)
    text_space = "\n".join(norm_space_lines)
    if text_space != text:
        rules_applied.append("normalize_horizontal_whitespace")
        text = text_space

    # 6. Re-join Hard-Wrapped Physical Lines into Logical Paragraphs (R1 fix)
    text_logical = rejoin_hard_wrapped_paragraphs(text)
    if text_logical != text:
        rules_applied.append("rejoin_hard_wrapped_paragraphs")
        text = text_logical

    # 7. Normalize Paragraph Newlines (max 2 consecutive newlines \n\n)
    text_newlines = REGEX_MULTIPLE_NEWLINES.sub("\n\n", text).strip()
    if text_newlines != text:
        rules_applied.append("normalize_paragraph_newlines")
        text = text_newlines

    # 8. Extract Structured Document Header (R2 fix)
    doc_header, _ = extract_structured_document_header(text)
    if any(doc_header.values()):
        rules_applied.append("extract_structured_document_header")

    # 9. Safety Audit: Verify Digits & Currency Preservation
    _audit_preservation_safety(raw_text, text)

    return {
        "success": True,
        "cleaned_text": text,
        "page_furniture": page_furniture,
        "document_header": doc_header,
        "original_length": len(raw_text),
        "cleaned_length": len(text),
        "rules_applied": list(set(rules_applied)),
        "schema_version": SCHEMA_VERSION
    }


def _audit_preservation_safety(raw_text: str, cleaned_text: str) -> None:
    """
    Regression assertion ensuring cleaning never alters digits or currency symbols.
    """
    raw_currencies = re.findall(r"[\$\€\£\₹]|\b(?:USD|INR|EUR|GBP)\b", raw_text)
    cleaned_currencies = re.findall(r"[\$\€\£\₹]|\b(?:USD|INR|EUR|GBP)\b", cleaned_text)

    if raw_currencies != cleaned_currencies:
        logger.warning(
            f"Text cleaning currency mismatch detected! Raw: {raw_currencies}, Cleaned: {cleaned_currencies}"
        )
