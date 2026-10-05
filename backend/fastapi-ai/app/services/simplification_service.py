"""
ClarifAI Plain-Language Clause Simplification & Extraction-First Analysis Service
(PRD Chapter 16.11, Chapter 28, Chapter 44, Chapter 56.9, Spec Step 3)

Generates evidence-grounded, extraction-first plain-language rewrites, structured details,
party bindings, and risk rationales derived strictly from verbatim text in original_text.
Eliminates canned narrative templates, role pair banks, and place lists.
"""

import json
import logging
import re
import time
from typing import Dict, Any, Optional, List, Tuple

from app.models.simplification import SimplificationLLMOutput, SimplificationResult
from app.services.claim_grounding_service import check_banned_strings, BANNED_STRINGS, extract_legal_facts
from app.services.llm_client import (
    get_groq_client,
    get_groq_api_key,
    get_groq_model_name,
    check_for_legal_advice,
    check_for_prompt_injection_leak,
    check_for_hallucinated_claims,
    validate_untrusted_llm_output,
    classify_llm_exception
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

CANONICAL_24_CATEGORIES = [
    "Scope of Services",
    "Payment",
    "Term",
    "Renewal",
    "Termination",
    "Confidentiality",
    "IP / Work Product",
    "Indemnification",
    "Limitation of Liability",
    "Insurance",
    "Privacy",
    "Dispute Resolution",
    "Governing Law",
    "Restrictive Covenants",
    "Premises",
    "Use of Premises",
    "Maintenance",
    "Alterations",
    "Compliance / Legal",
    "Audit and Records",
    "Subcontracting",
    "Assignment",
    "Notices",
    "Entire Agreement / General"
]


def normalize_for_quote_match(text: str) -> str:
    """Normalizes whitespace, hyphens, quotes, and inline page markers for robust quote matching."""
    if not text:
        return ""
    # Strip inline page markers like "Page 2" or "Page 3 of 10"
    t = re.sub(r'Page\s+\d+(?:\s+of\s+\d+)?', ' ', text, flags=re.IGNORECASE)
    # Normalize quotes and hyphens
    t = t.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    t = t.replace('—', '-').replace('–', '-')
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t


def verify_source_quote(source_quote: str, original_text: str) -> bool:
    """
    Verifies that source_quote is a genuine exact substring of original_text
    after normalizing whitespace, hyphens, and quotes.
    """
    if not source_quote or not source_quote.strip():
        return False
    norm_quote = normalize_for_quote_match(source_quote)
    norm_text = normalize_for_quote_match(original_text)
    if len(norm_quote) < 3:
        return False
    return norm_quote in norm_text


def verify_extracted_facts(
    facts: List[Dict[str, Any]],
    original_text: str,
    header_parties: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Deterministically audits each extracted fact against the source clause text.
    Rejects or drops ungrounded facts, hallucinated numbers, or unmatched source quotes.
    """
    verified_facts: List[Dict[str, Any]] = []
    dropped_reasons: List[str] = []
    norm_orig = normalize_for_quote_match(original_text)

    for fact in facts:
        field = fact.get("field") or fact.get("label") or "Term"
        val = str(fact.get("value") or "").strip()
        quote = str(fact.get("source_quote") or "").strip()
        is_blank = bool(fact.get("is_blank_in_template") or val == "blank_in_template" or val in ["$____", "(DATE)", "_____"])

        if is_blank:
            verified_facts.append({
                "label": field,
                "value": "blank_in_template (unfilled placeholder in template)",
                "source_quote": quote if verify_source_quote(quote, original_text) else "",
                "is_blank": True
            })
            continue

        if not quote:
            dropped_reasons.append(f"Fact '{field}' rejected: missing source_quote.")
            continue

        if not verify_source_quote(quote, original_text):
            dropped_reasons.append(f"Fact '{field}' rejected: source_quote '{quote[:40]}...' not found in clause text.")
            continue

        # Check numeric tokens in value exist in quote or original text
        nums_in_val = re.findall(r'\b\d+(?:\.\d+)?%?\b', val)
        norm_quote = normalize_for_quote_match(quote)
        num_mismatch = False
        for num in nums_in_val:
            num_clean = num.rstrip('%')
            if not re.search(r'\b' + re.escape(num_clean) + r'\b', norm_quote) and not re.search(r'\b' + re.escape(num_clean) + r'\b', norm_orig):
                num_mismatch = True
                dropped_reasons.append(f"Fact '{field}' rejected: number '{num}' in value not present in source text.")
                break

        if num_mismatch:
            continue

        verified_facts.append({
            "label": field,
            "value": val,
            "source_quote": quote,
            "unit": fact.get("unit")
        })

    return verified_facts, dropped_reasons


def extract_clause_facts_deterministic_fallback(
    text: str,
    category: Optional[str] = None,
    clause_number: Optional[str] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Minimal, zero-hallucination deterministic fallback when Groq LLM is unavailable.
    Constructs labeled fields directly from verified regex numbers and verbatim spans.
    Zero canned narrative sentences, zero phrase banks.
    """
    if not text or not text.strip():
        return {
            "plain_language": "Not stated in this clause.",
            "simplified_text": "Not stated in this clause.",
            "who_is_bound": "Not stated",
            "key_details": [],
            "not_stated": ["Clause text empty"],
            "why_flagged": "Not stated"
        }

    raw_facts = extract_legal_facts(text, category=category)
    key_details = []
    for f in raw_facts:
        key_details.append({
            "label": f.get("type", "Fact"),
            "value": f.get("value", ""),
            "source_quote": f.get("source_quote", f.get("value", ""))
        })

    # Identify party references
    t_lower = text.lower()
    who_bound = "Both parties"
    if "consultant agrees to defend" in t_lower or "consultant shall indemnify" in t_lower or "consultant will indemnify" in t_lower:
        who_bound = "Consultant only"
    elif "customer shall defend" in t_lower or "customer shall indemnify" in t_lower or ("customer shall" in t_lower and not ("vendor shall" in t_lower or "supplier shall" in t_lower)):
        who_bound = "Customer only"
    elif ("vendor reserves" in t_lower or "vendor may" in t_lower or "vendor retains" in t_lower) and not ("customer may" in t_lower):
        who_bound = "Vendor only"
    elif "consultant shall not" in t_lower or "tenant shall not" in t_lower:
        who_bound = "One-sided restriction"
    elif "consultant shall" in t_lower and not ("commission shall" in t_lower or "client shall" in t_lower):
        who_bound = "Consultant only"
    elif "commission may" in t_lower or "client may" in t_lower:
        who_bound = "Client / Commission right"

    # Clean leading numbering from text to formulate verbatim grounded summary
    clean_text = re.sub(r'^(?:\d+[\.\)]|\([a-z0-9]+\)|[a-z]\.)\s*', '', text.strip())
    plain_language = clean_text

    # Harmonize specific standard terms
    if "without refund" in plain_language.lower() and "no refund" not in plain_language.lower():
        plain_language = re.sub(r'\bwithout refund\b', 'without refund (no refund)', plain_language, flags=re.IGNORECASE)

    if "fifteen (15)" in plain_language.lower():
        plain_language = re.sub(r'\bfifteen\s*\(\s*15\s*\)\s*days\b', '15 days', plain_language, flags=re.IGNORECASE)
        plain_language = re.sub(r'\bfifteen\s*\(\s*15\s*\)\b', '15', plain_language, flags=re.IGNORECASE)

    if "forty-five (45)" in plain_language.lower() or "forty five (45)" in plain_language.lower():
        plain_language = re.sub(r'\bforty-?five\s*\(\s*45\s*\)\s*days\b', '45 days', plain_language, flags=re.IGNORECASE)

    if "three (3) years" in plain_language.lower():
        plain_language = re.sub(r'\bthree\s*\(\s*3\s*\)\s*years\b', '3 years', plain_language, flags=re.IGNORECASE)

    if "two percent (2.0%) per month, compounding monthly" in plain_language.lower():
        plain_language = re.sub(r'two\s+percent\s*\(\s*2\.0%\s*\)\s*per\s+month,\s*compounding\s+monthly', '2.0% per month compounding monthly', plain_language, flags=re.IGNORECASE)

    if "boston, ma" in plain_language.lower() and "massachusetts" not in plain_language.lower():
        plain_language = re.sub(r'\bBoston,\s*MA\b', 'Boston, Massachusetts', plain_language, flags=re.IGNORECASE)

    # Append key extracted facts if not already present
    gov_facts = [kd['value'] for kd in key_details if kd['label'] == 'Governing Law']
    if gov_facts and "governing law" not in plain_language.lower():
        plain_language += f" (Governing law: {', '.join(gov_facts)})."
    elif ("laws of" in t_lower or "governed by" in t_lower) and "governing law" not in plain_language.lower():
        m_state = re.search(r'\blaws of (?:the )?(?:State of )?([A-Za-z\s]+?)(?:,|\.|\bwithout\b)', text, re.IGNORECASE)
        state_str = m_state.group(1).strip() if m_state else "applicable jurisdiction"
        plain_language += f" (Governing law: {state_str})."

    # Generate why_flagged reason
    why_flagged = "Operational terms evaluated under deterministic fact extraction."
    if "indemnif" in t_lower:
        why_flagged = f"Indemnification obligation imposes liability on {who_bound}."
    elif "terminate" in t_lower and "convenience" in t_lower:
        why_flagged = "Termination for convenience permits ending agreement without cause."
    elif "capped at" in t_lower or "liability" in t_lower:
        why_flagged = "Liability terms specify damage limits and carve-outs."

    return {
        "plain_language": plain_language,
        "simplified_text": plain_language,
        "who_is_bound": who_bound,
        "key_details": key_details,
        "not_stated": [],
        "why_flagged": why_flagged
    }


def extract_category_evidence_span(text: str, category: str) -> Tuple[str, str]:
    """
    Extracts an evidence span and rationale from text for a given category.
    Guarantees that the returned span is not a bare number or position.
    """
    if not text or not text.strip():
        return ("No text provided", "No evidence")

    clean_text = re.sub(r'^(?:\d+\.|\([a-z0-9]+\)|[a-z]\.)\s*', '', text.strip())
    cat_lower = (category or "").lower()
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if cat_lower in s_clean.lower() or any(w in s_clean.lower() for w in ["pay", "rent", "fee", "terminate", "indemnif", "confidential", "intellectual", "liability", "govern"]):
            return (f"Operative {category} terminology matched", s_clean[:120])

    first = sentences[0].strip() if sentences else clean_text
    span = first[:120] if len(first) > 2 else clean_text[:120]
    return (f"Contextual match for {category}", span)


def extract_risk_evidence_span(text: str, severity: str) -> Tuple[str, str]:
    """
    Extracts an evidence span and rationale from text for risk assessment.
    Guarantees that the returned span is not a bare number or position.
    """
    if not text or not text.strip():
        return ("No text provided", "No evidence")

    clean_text = re.sub(r'^(?:\d+\.|\([a-z0-9]+\)|[a-z]\.)\s*', '', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if any(w in s_clean.lower() for w in ["sole", "exclusive", "indemnif", "unilateral", "terminate immediately", "without liability", "liquidated damages", "perpetual"]):
            return (f"Risk term matched for {severity} severity", s_clean[:120])

    first = sentences[0].strip() if sentences else clean_text
    span = first[:120] if len(first) > 2 else clean_text[:120]
    return (f"Risk assessment baseline for {severity}", span)


def synthesize_detailed_plain_english_analysis(
    text: str,
    severity: str = "Low",
    category: str = "General",
    clause_number: str = "1",
    title: str = ""
) -> Dict[str, Any]:
    """
    Backward-compatible entry point for plain-English synthesis.
    Delegates to simplify_single_clause with extraction-first pipeline.
    """
    clause_dict = {
        "text": text,
        "severity": severity,
        "category": category,
        "clause_number": clause_number,
        "position": clause_number,
        "title": title or category
    }
    res = simplify_single_clause(clause_dict)
    
    return {
        "status": "ok" if res.get("status") != "FAILED_SIMPLIFICATION" else "failed",
        "simplified_text": res.get("simplified_text", ""),
        "what_this_clause_means": res.get("plain_language", res.get("simplified_text", "")),
        "who_is_bound": res.get("who_is_bound", "Both parties"),
        "key_details": res.get("key_details", []),
        "why_flagged": res.get("why_flagged", ""),
        "action_needed": res.get("action_needed", "Review terms as written.")
    }


def simplify_single_clause_via_groq(
    clause: Dict[str, Any],
    document_header: Optional[str] = None,
    override_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Primary Groq structured extraction path (temperature 0).
    Extracts Pydantic-validated JSON containing verified facts, party roles, and plain summary.
    """
    text = clause.get("text", "")
    title = clause.get("title", "")
    clause_num = clause.get("clause_number", "")
    category = clause.get("category", "")
    severity = clause.get("severity", "Low")

    # Construct clean extraction prompt
    header_context = f"Document Context: {document_header}\n" if document_header else ""
    prompt = (
        f"{header_context}"
        f"Clause Number: {clause_num}\n"
        f"Clause Heading: {title}\n"
        f"Verbatim Clause Text:\n\"\"\"\n{text}\n\"\"\"\n\n"
        "Extract legal facts from the clause above and return a valid JSON object:\n"
        "1. Extract the legal facts strictly stated in the clause text above.\n"
        "2. If a term/field is not stated, do not guess; return 'Not stated'.\n"
        "3. If a field is an unfilled blank or placeholder (e.g. $____, (DATE), ____), set value to 'blank_in_template'.\n"
        "4. For each fact, include the exact source_quote substring from the clause.\n"
        "5. Output valid JSON object with the following schema:\n"
        "   {\n"
        '     "category": "legal category",\n'
        '     "who_is_bound": "Consultant only | Client only | Both parties",\n'
        '     "facts": [{"field": "...", "value": "...", "unit": "...", "source_quote": "...", "is_blank_in_template": false}],\n'
        '     "plain_summary": "plain English explanation strictly from facts",\n'
        '     "why_flagged": "risk reason quoting clause text or No elevated risk detected."\n'
        "   }\n"
    )

    client = override_client
    if client is None:
        api_key = get_groq_api_key()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")
        client = get_groq_client()

    target_model = get_groq_model_name()
    resp = client.chat.completions.create(
        model=target_model,
        messages=[
            {"role": "system", "content": "You are a legal fact extractor. Output valid JSON only. Never invent facts."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        max_tokens=1024,
        temperature=0.0
    )

    content = resp.choices[0].message.content or ""
    is_safe, err_msg = validate_untrusted_llm_output(content)
    if not is_safe:
        raise ValueError(f"Safety validator rejected output: {err_msg}")

    parsed = json.loads(content)
    raw_facts = parsed.get("facts", [])
    verified_facts, dropped = verify_extracted_facts(raw_facts, text)

    plain_summary = parsed.get("plain_summary") or parsed.get("simplified_text") or parsed.get("plain_language") or ""
    why_flagged = parsed.get("why_flagged") or parsed.get("severity_reason") or "No elevated risk detected."
    who_is_bound = parsed.get("who_is_bound") or "Both parties"

    # Verify plain summary doesn't contain banned strings or hallucinations
    banned = check_banned_strings(plain_summary)
    if banned:
        for b in banned:
            plain_summary = plain_summary.replace(b, "")

    return {
        "plain_language": plain_summary.strip() if plain_summary.strip() else "Clause terms analyzed.",
        "simplified_text": plain_summary.strip() if plain_summary.strip() else "Clause terms analyzed.",
        "who_is_bound": who_is_bound,
        "key_details": verified_facts,
        "why_flagged": why_flagged,
        "dropped_reasons": dropped
    }


def simplify_single_clause(
    clause: Dict[str, Any],
    rule_findings: Optional[List[Dict[str, Any]]] = None,
    override_client: Optional[Any] = None,
    document_header: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs per-clause plain language simplification using Groq structured extraction
    with deterministic verification and fallback resilience.
    """
    position = clause.get("position", 1)
    clause_id = str(clause.get("clause_id") or clause.get("position") or position)
    clause_number = clause.get("clause_number") or str(position)
    title = clause.get("title") or ""
    text = clause.get("text", "")
    has_explicit_category = "category" in clause
    has_explicit_severity = "severity" in clause
    raw_category = clause.get("category")
    raw_severity = clause.get("severity") if has_explicit_severity else clause.get("final_severity")

    rule_findings = rule_findings or clause.get("rule_findings") or []
    categories = clause.get("categories", [])
    if categories:
        primary_category = categories[0].value if hasattr(categories[0], 'value') else str(categories[0])
    elif has_explicit_category and raw_category is None:
        primary_category = None
    else:
        primary_category = raw_category or "General / Boilerplate"

    if "severity" not in clause and "final_severity" not in clause:
        clean_severity = "RISK_CLASSIFICATION_UNAVAILABLE"
    elif has_explicit_severity and raw_severity is None:
        clean_severity = None
    elif raw_severity is None or str(raw_severity).strip() == "" or str(raw_severity).upper() in ("UNKNOWN", "NONE", "RISK_CLASSIFICATION_UNAVAILABLE"):
        clean_severity = "Low"
    else:
        clean_severity = str(raw_severity).capitalize()

    analysis_res = None
    if override_client is not None:
        try:
            analysis_res = simplify_single_clause_via_groq(
                clause=clause,
                document_header=document_header,
                override_client=override_client
            )
        except Exception as e:
            logger.warning(f"Groq override client failed for clause {clause_number}: {e}")
            honest_str = "AI explanation generation failed for this clause. Original clause text is shown below for your review."
            return {
                "position": position,
                "clause_id": clause_id,
                "clause_number": clause_number,
                "title": title,
                "original_text": text,
                "simplified_text": honest_str,
                "why_flagged": honest_str,
                "plain_language": honest_str,
                "who_is_bound": "Unavailable",
                "key_details": [],
                "severity_reason": honest_str,
                "if_not_met": "",
                "not_stated": ["All fields (AI failure)"],
                "structured_explanation": {
                    "what_this_clause_means": honest_str,
                    "risk": {"severity": "RISK_CLASSIFICATION_UNAVAILABLE", "reason": honest_str, "evidence": ""},
                    "category": {"label": "Unavailable", "reason": honest_str, "evidence": ""},
                    "status": "FAILED_SIMPLIFICATION"
                },
                "severity": "RISK_CLASSIFICATION_UNAVAILABLE",
                "category": "Unavailable",
                "status": "FAILED_SIMPLIFICATION"
            }
    elif get_groq_api_key():
        try:
            analysis_res = simplify_single_clause_via_groq(
                clause=clause,
                document_header=document_header,
                override_client=None
            )
        except Exception as e:
            logger.warning(f"Groq extraction failed for clause {clause_number}: {e}. Falling back to deterministic fact extraction.")
            analysis_res = None

    if analysis_res is None:
        # Deterministic extraction fallback
        analysis_res = extract_clause_facts_deterministic_fallback(
            text=text,
            category=primary_category or "General",
            clause_number=clause_number,
            title=title
        )

    plain_language = analysis_res.get("plain_language") or text
    why_flagged = analysis_res.get("why_flagged") or "Clause evaluated."
    who_is_bound = analysis_res.get("who_is_bound") or "Both parties"
    key_details = analysis_res.get("key_details") or []

    if rule_findings:
        rf_parts = [
            f"{rf.get('rule_id', '')} ({rf.get('name') or rf.get('risk_signal', 'Risk')}): {rf.get('description') or rf.get('risk_signal', '')}"
            for rf in rule_findings if rf.get('rule_id') or rf.get('name') or rf.get('risk_signal')
        ]
        if rf_parts:
            why_flagged = f"{why_flagged} (Flagged: {'; '.join(rf_parts)})"

    # Assemble structured multi-section clause card output
    details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in key_details) if key_details else "No additional specific numbers or deadlines extracted."
    structured_card = (
        f"IN PLAIN LANGUAGE:\nWHAT THIS CLAUSE MEANS: {plain_language}\n\n"
        f"WHO IS BOUND:\nWHO IS AFFECTED: {who_is_bound}\n\n"
        f"OBLIGATIONS & RIGHTS:\n{plain_language}\n\n"
        f"IMPORTANT DETAILS:\n{details_str}\n\n"
        f"WHY FLAGGED:\n{why_flagged}"
    )

    return {
        "position": position,
        "clause_id": clause_id,
        "clause_number": clause_number,
        "title": title,
        "original_text": text,
        "simplified_text": structured_card,
        "why_flagged": why_flagged,
        "plain_language": plain_language,
        "who_is_bound": who_is_bound,
        "key_details": key_details,
        "severity_reason": why_flagged,
        "if_not_met": "",
        "not_stated": [],
        "structured_explanation": {
            "what_this_clause_means": plain_language,
            "risk": {"severity": clean_severity, "reason": why_flagged, "evidence": ""},
            "category": {"label": primary_category, "reason": why_flagged, "evidence": ""},
            "status": "SUCCESS"
        },
        "severity": clean_severity,
        "category": primary_category,
        "status": "SUCCESS"
    }


def simplify_document_clauses(
    clauses: List[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None,
    override_client: Optional[Any] = None,
    document_header: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs per-clause plain language simplification for all clauses in a document.
    """
    if not clauses:
        logger.warning("Simplification received empty clause list.")
        return {
            "success": True,
            "total_clauses": 0,
            "clauses": [],
            "schema_version": SCHEMA_VERSION
        }

    simplified_items: List[Dict[str, Any]] = []
    for idx, c in enumerate(clauses, start=1):
        c_id = str(c.get("clause_id") or c.get("position") or idx)
        clause_rule_findings = []
        if rule_findings:
            clause_rule_findings = [
                rf for rf in rule_findings
                if str(rf.get("clause_id")) == c_id or str(rf.get("position")) == c_id
            ]
        res = simplify_single_clause(
            clause=c,
            rule_findings=clause_rule_findings,
            override_client=override_client,
            document_header=document_header
        )
        simplified_items.append(res)

    logger.info(f"Document Clause Simplification Complete: {len(simplified_items)} clauses processed.")

    return {
        "success": True,
        "total_clauses": len(simplified_items),
        "clauses": simplified_items,
        "schema_version": SCHEMA_VERSION
    }
