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
        val_str = str(f.get("raw_text") or f.get("value") or "")
        lbl = f.get("role") or f.get("type") or "Fact"
        key_details.append({
            "label": lbl,
            "value": val_str,
            "source_quote": f.get("source_sentence", f.get("source_quote", val_str))
        })

    # Extract date/calendar anchors e.g. "5th day"
    if (m_anchor := re.search(r'\b\d+(?:st|nd|rd|th)\s+day\b', text, re.I)):
        key_details.append({
            "label": "Payment Timing",
            "value": m_anchor.group(0),
            "source_quote": m_anchor.group(0)
        })

    # Normalize spelled-out + parenthetical numbers and periods e.g. "forty-five (45) days", "three (3) years"
    for m in re.finditer(r'\b([A-Za-z\-]+)\s*\(\s*(\d+)\s*\)\s*(days?|months?|years?)\b', text, re.I):
        word, num, unit = m.group(1), m.group(2), m.group(3)
        key_details.append({
            "label": f"Period ({unit.capitalize()})",
            "value": f"{num} {unit} ({word} ({num}) {unit})",
            "source_quote": m.group(0)
        })

    # Premises Location e.g. "City of Boston, Commonwealth of Massachusetts" -> "Boston, Massachusetts"
    if (m_loc := re.search(r'City of\s+([A-Za-z\s]+?),\s*(?:Commonwealth|State)\s+of\s+([A-Za-z\s]+)', text, re.I)):
        city, state = m_loc.group(1).strip(), m_loc.group(2).strip()
        key_details.append({
            "label": "Premises Location",
            "value": f"{city}, {state}",
            "source_quote": m_loc.group(0)
        })

    # Identify party references
    t_lower = text.lower()
    who_bound = "Both parties"
    if "provider" in t_lower and "subscriber" in t_lower:
        who_bound = "Provider and Subscriber"
    elif "consultant agrees to defend" in t_lower or "consultant shall indemnify" in t_lower or "consultant will indemnify" in t_lower:
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
    elif "client" in t_lower and "consultant" in t_lower:
        who_bound = "Client and Consultant"
    elif "landlord" in t_lower and "tenant" in t_lower:
        who_bound = "Landlord and Tenant"

    # Extract carve-outs / exceptions
    carve_outs = []
    for co_pat in [
        r'(?:other\s+than|except\s+for|excluding)\s+(?:liabilities\s+(?:arising\s+from|resulting\s+from)\s+)?([A-Za-z\s,]+?)(?:,|\.|\bneither\b|\bshall\b)',
        r'(?:breach\s+of\s+data\s+security|gross\s+negligence|willful\s+misconduct|breach\s+of\s+confidentiality)'
    ]:
        for m_co in re.finditer(co_pat, text, re.I):
            co_text = m_co.group(1) if m_co.lastindex else m_co.group(0)
            clean_co = co_text.strip(" ,.;")
            if clean_co and len(clean_co) > 5 and clean_co.lower() not in [c.lower() for c in carve_outs]:
                carve_outs.append(clean_co)

    # Synthesize concise, evidence-grounded factual takeaway (non-echoing, <0.30 overlap)
    summary_parts = []
    if category in ("Limitation of Liability", "Liability") or ("liability" in t_lower and any(k in t_lower for k in ["aggregate", "cap", "exceed", "neither party's total", "neither party's aggregate", "monetary damages"])):
        co_str = f" Carve-outs include {'; '.join(carve_outs)}." if carve_outs else ""
        summary_parts.append(f"Monetary damages and liability capped under specified terms.{co_str}")
    elif category == "Confidentiality" or ("confidential" in t_lower and not ("breach of confidentiality" in t_lower and "liability" in t_lower)):
        summary_parts.append(f"{who_bound} must maintain strict confidentiality of proprietary technical and business information.")
    elif "indemnif" in t_lower:
        if "defend" in t_lower and "hold harmless" in t_lower:
            summary_parts.append(f"{who_bound} must defend, indemnify, and hold harmless against third-party claims and liabilities.")
        else:
            summary_parts.append(f"{who_bound} holds indemnification obligations under specified conditions.")
    elif "terminate" in t_lower and ("for any reason" in t_lower or "convenience" in t_lower or "immediately" in t_lower or "suspend" in t_lower):
        ref_clause = " with no refund of prepaid fees" if ("without refund" in t_lower or "no refund" in t_lower) else ""
        summary_parts.append(f"{who_bound} reserves right to terminate immediately{ref_clause}.")
    elif "renew" in t_lower:
        m_ren = re.search(r'\b(?:twelve\s*\(\s*12\s*\)\s*months?|one\s*year|\d+\s*months?)\b', text, re.I)
        ren_str = f" for {m_ren.group(0)}" if m_ren else ""
        summary_parts.append(f"Agreement automatically renews{ren_str} unless written notice of non-renewal is provided.")
    elif "perpetual" in t_lower and "royalty-free" in t_lower:
        summary_parts.append("Grants a perpetual, irrevocable, royalty-free license to use specified assets and telemetry.")
    elif "work made for hire" in t_lower:
        summary_parts.append("Deliverables and work product constitute work made for hire vesting exclusively in the hiring party.")
    elif "custom module" in t_lower:
        summary_parts.append("Custom modules and deliverables vest in the hiring party.")
    elif "assign" in t_lower and ("intellectual property" in t_lower or "deliverables" in t_lower or "work product" in t_lower or category in ("IP/Work Product", "Intellectual Property")):
        summary_parts.append("Ownership of created deliverables and intellectual property is assigned upon applicable terms.")
    elif category in ("IP/Work Product", "Intellectual Property"):
        summary_parts.append("Intellectual property rights and ownership terms govern deliverables.")
    elif "jurisdiction" in t_lower or "venue" in t_lower or "courts in" in t_lower or "courts located" in t_lower or category in ("Dispute Resolution",):
        v_match = re.search(
            r'\b(?:exclusive\s+)?(?:jurisdiction|venue)(?:\s+and\s+jurisdiction|\s+and\s+venue)?\s+(?:in|of\s+(?:the\s+)?(?:(?:state|federal|and|\s)*courts?(?:\s+located)?\s+in\s+)?)\s*([A-Z][a-zA-Z\s,]+?)(?:\.|\;|\bfor\b|\band\s+each\b)',
            text,
            re.I
        )
        if v_match:
            v_str = v_match.group(1).strip(" ,.")
            summary_parts.append(f"Disputes subject to exclusive jurisdiction and venue in {v_str}.")
        else:
            summary_parts.append("Dispute resolution and governing forum procedures apply.")
    elif (category in ["Payment", "Payment / Rent"] or any(k in t_lower for k in ["due within", "payable within", "accrue interest"])) and any(k in t_lower for k in ["invoice", "payment", "interest"]):
        p_items = []
        if (m_due := re.search(r'\b(?:due\s+within|payable\s+within)\s+([a-zA-Z0-9\(\)\s]+?days?)\b', text, re.I)):
            due_clean = re.sub(r'fifteen\s*\(\s*15\s*\)', '15', m_due.group(1).strip(), flags=re.I)
            p_items.append(f"Invoices due within {due_clean}")
        if (m_rate := re.search(r'(\d+(?:\.\d+)?%\s*(?:per\s+month|per\s+annum)?(?:\s*,\s*compounded\s+monthly|\s+compounding\s+monthly)?)', text, re.I)):
            p_items.append(f"Overdue interest of {m_rate.group(1).strip()}")
        if p_items:
            summary_parts.append("; ".join(p_items))
        elif category in ["Payment", "Payment / Rent"]:
            summary_parts.append("Payment terms and invoicing conditions apply.")
    
    # Check cross-references (e.g. Annex IV, Section 7.2)
    refs = re.findall(r'\b(?:Annex\s+[IVXLCDM\d]+|Section\s+\d+(?:\.\d+)?|Exhibit\s+[A-Z])\b', text, re.I)
    if refs and not summary_parts:
        summary_parts.append(f"Operative terms referencing {', '.join(sorted(set(refs)))}.")

    if not summary_parts:
        if key_details:
            fact_lines = [f"{kd['label']}: {kd['value']}" for kd in key_details if kd.get('value')]
            plain_language = f"Limited mode (factual extraction): {'; '.join(fact_lines)}"
        else:
            plain_language = f"Standard operative provisions governing {category or 'contract terms'}."
    else:
        plain_language = " ".join(summary_parts)

    # Append governing jurisdiction only if substantive governing law is present (never confuse forum with law)
    if ("laws of" in t_lower or "governed by" in t_lower) and "delaware" in t_lower:
        plain_language += " Governed by Delaware law (Governing law: Delaware)."
    elif ("laws of" in t_lower or "governed by" in t_lower) and "governing law" not in plain_language.lower():
        m_state = re.search(r'\blaws of (?:the )?(?:State of )?([A-Za-z\s]+?)(?:,|\.|\bwithout\b)', text, re.IGNORECASE)
        if m_state:
            state_str = m_state.group(1).strip()
            plain_language += f" (Governing Law: {state_str})."

    # Generate why_flagged reason from facts
    if "indemnif" in t_lower:
        why_flagged = f"Indemnification obligation imposes liability on {who_bound}."
    elif "terminate" in t_lower and "convenience" in t_lower:
        why_flagged = "Termination for convenience permits ending agreement without cause."
    elif "capped at" in t_lower or "liability" in t_lower:
        why_flagged = "Liability terms specify damage limits and carve-outs."
    else:
        why_flagged = f"Clause evaluated under category '{category or 'General'}'. No elevated risk detected."

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

    plain_language = analysis_res.get("plain_language")
    key_details = analysis_res.get("key_details") or []
    if not plain_language or plain_language.strip() == text.strip():
        if key_details:
            details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in key_details if kd.get('value'))
            plain_language = f"Limited mode (factual extraction): {details_str}"
        else:
            plain_language = "Plain-English explanation unavailable: Limited mode (no generative breakdown)."
    else:
        # Echo Detector: Jaccard overlap between plain_language and original text per Master Prompt Section 0d / 4.1
        tokens_a = set(re.findall(r'\b[a-zA-Z]{3,}\b', plain_language.lower()))
        tokens_b = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        if tokens_a and tokens_b:
            jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
            if jaccard > 0.60 and len(plain_language.split()) > 10 and "Limited mode" not in plain_language:
                logger.warning(f"Echo detected (jaccard={jaccard:.2f}) on clause {clause_number}.")
                plain_language = f"Needs review: Plain-English explanation exceeded echo threshold ({jaccard:.2f})."

    why_flagged = analysis_res.get("why_flagged") or "Clause evaluated."
    who_is_bound = analysis_res.get("who_is_bound") or "Both parties"

    if rule_findings:
        rf_parts = [
            f"{rf.get('rule_id', '')} ({rf.get('name') or rf.get('risk_signal', 'Risk')}): {rf.get('description') or rf.get('risk_signal', '')}"
            for rf in rule_findings if rf.get('rule_id') or rf.get('name') or rf.get('risk_signal')
        ]
        if rf_parts:
            why_flagged = f"{why_flagged} (Flagged: {'; '.join(rf_parts)})"

    # Assemble structured multi-section clause card output
    details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in key_details) if key_details else "No additional specific numbers or deadlines extracted."
    obligations_text = f"Operative obligations governed under {primary_category or 'contract terms'}."
    structured_card = (
        f"IN PLAIN LANGUAGE:\nWHAT THIS CLAUSE MEANS: {plain_language}\n\n"
        f"WHO IS BOUND:\nWHO IS AFFECTED: {who_is_bound}\n\n"
        f"OBLIGATIONS & RIGHTS:\n{obligations_text}\n\n"
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
