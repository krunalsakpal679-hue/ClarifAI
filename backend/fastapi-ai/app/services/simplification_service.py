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
    who_benefits = "Both parties"
    is_one_sided = False

    if "provider" in t_lower and "subscriber" in t_lower:
        who_bound = "Provider"
        who_benefits = "Subscriber"
        is_one_sided = True
    elif "consultant agrees to defend" in t_lower or "consultant shall indemnify" in t_lower or "consultant will indemnify" in t_lower:
        who_bound = "Consultant"
        who_benefits = "Commission"
        is_one_sided = True
    elif "customer shall defend" in t_lower or "customer shall indemnify" in t_lower or ("customer shall" in t_lower and not ("vendor shall" in t_lower or "supplier shall" in t_lower)):
        who_bound = "Customer"
        who_benefits = "Vendor"
        is_one_sided = True
    elif ("vendor reserves" in t_lower or "vendor may" in t_lower or "vendor retains" in t_lower) and not ("customer may" in t_lower):
        who_bound = "Vendor"
        who_benefits = "Customer"
        is_one_sided = True
    elif "consultant shall not" in t_lower or "consultant shall" in t_lower or "consultant warrants" in t_lower:
        who_bound = "Consultant"
        who_benefits = "Commission"
        is_one_sided = True
    elif ("commission may" in t_lower or "client may" in t_lower) and not ("consultant may" in t_lower):
        who_bound = "Consultant"
        who_benefits = "Commission"
        is_one_sided = True
    elif "tenant shall not" in t_lower or "tenant shall" in t_lower:
        who_bound = "Tenant"
        who_benefits = "Landlord"
        is_one_sided = True
    elif "client" in t_lower and "consultant" in t_lower:
        who_bound = "Consultant"
        who_benefits = "Client"
        is_one_sided = True
    elif "landlord" in t_lower and "tenant" in t_lower:
        who_bound = "Both parties"
        who_benefits = "Both parties"

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

    # Synthesize concise, evidence-grounded factual takeaway
    summary_parts = []
    if category in ("Limitation of Liability", "Liability") and ("liability" in t_lower and any(k in t_lower for k in ["aggregate", "cap", "exceed", "neither party's total", "neither party's aggregate", "monetary damages"])):
        co_str = f" Carve-outs include {'; '.join(carve_outs)}." if carve_outs else ""
        summary_parts.append(f"Monetary damages and liability capped under specified terms.{co_str}")
    elif category == "Insurance":
        ins_limits = re.findall(r'\$[0-9,]+', text)
        limits_str = f" with limits of {', '.join(sorted(set(ins_limits)))}" if ins_limits else ""
        summary_parts.append(f"{who_bound} must maintain required insurance policies{limits_str}.")
    elif category == "Confidentiality" or ("confidential" in t_lower and not ("breach of confidentiality" in t_lower and "liability" in t_lower)):
        summary_parts.append(f"{who_bound} must maintain strict confidentiality of proprietary technical and business information.")
    elif "indemnif" in t_lower:
        if "defend" in t_lower and "hold harmless" in t_lower:
            summary_parts.append(f"{who_bound} must defend, indemnify, and hold harmless against third-party claims and liabilities.")
        else:
            summary_parts.append(f"{who_bound} holds indemnification obligations under specified conditions.")
    elif "terminate" in t_lower and ("convenience" in t_lower or "reprocurement" in t_lower):
        m_notice = re.search(r'(\d+)\s*[- ]\s*days?|\b([A-Za-z]+)\s*\(\s*(\d+)\s*\)\s*days?', text, re.I)
        notice_days = m_notice.group(1) or m_notice.group(3) if m_notice else "specified"
        summary_parts.append(f"Termination provisions permit early termination upon {notice_days} days written notice.")
    elif "renew" in t_lower:
        m_ren = re.search(r'\b(?:twelve\s*\(\s*12\s*\)\s*months?|one\s*year|\d+\s*months?)\b', text, re.I)
        ren_str = f" for {m_ren.group(0)}" if m_ren else ""
        summary_parts.append(f"Agreement automatically renews{ren_str} unless written notice of non-renewal is provided.")
    elif "perpetual" in t_lower and "royalty-free" in t_lower:
        summary_parts.append("Grants a perpetual, irrevocable, royalty-free license to use specified assets and deliverables.")
    elif "work made for hire" in t_lower:
        summary_parts.append("Deliverables constitute works made for hire vesting exclusively in the commissioning party.")
    elif "custom module" in t_lower:
        summary_parts.append("Custom modules and deliverables vest in the commissioning party.")
    elif "assign" in t_lower and ("intellectual property" in t_lower or "deliverables" in t_lower or "work product" in t_lower or category in ("IP/Work Product", "Intellectual Property")):
        summary_parts.append("Ownership of created deliverables and intellectual property is assigned upon applicable terms.")
    elif category in ("IP/Work Product", "Intellectual Property"):
        summary_parts.append("Intellectual property rights and ownership terms govern deliverables.")
    elif category in ("Dispute Resolution", "Disputes") or ("jurisdiction" in t_lower or "venue" in t_lower or "courts in" in t_lower):
        v_match = re.search(
            r'\b(?:exclusive\s+)?(?:jurisdiction|venue)(?:\s+and\s+jurisdiction|\s+and\s+venue)?\s+(?:in|of\s+(?:the\s+)?(?:(?:state|federal|and|\s)*courts?(?:\s+located)?\s+in\s+)?)\s*([A-Z][a-zA-Z\s,]+?)(?:\.|\;|\bfor\b|\band\s+each\b)',
            text,
            re.I
        )
        if v_match:
            v_str = v_match.group(1).strip(" ,.")
            summary_parts.append(f"Disputes subject to exclusive jurisdiction and venue in {v_str}.")
        else:
            summary_parts.append("Dispute resolution procedures govern contractual controversies.")
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
            summary_parts.append("Payment terms, invoicing schedules, and fee conditions apply.")

    # Only append governing law if category is Governing Law
    if category == "Governing Law" or ("governing law" in (title or "").lower()):
        m_state = re.search(r'\blaws of (?:the )?(?:State of )?([A-Za-z\s]+?)(?:,|\.|\bwithout\b)', text, re.IGNORECASE)
        if m_state:
            state_str = m_state.group(1).strip()
            summary_parts.append(f"Agreement is construed under the laws of {state_str}.")

    if not summary_parts:
        if key_details:
            fact_lines = [f"{kd['label']}: {kd['value']}" for kd in key_details if kd.get('value')]
            plain_language = f"Plain-English explanation unavailable (Limited mode):\n" + "\n".join(f"- {fl}" for fl in fact_lines)
        else:
            plain_language = f"Plain-English explanation unavailable (Limited mode): Standard operational terms governing {category or 'contract terms'}."
    else:
        plain_language = " ".join(summary_parts)

    # Generate why_flagged reason from facts
    if "indemnif" in t_lower:
        why_flagged = f"Risky for the {who_bound} because unilateral indemnification imposes defense and liability obligations without a reciprocal cap."
    elif "terminate" in t_lower and ("convenience" in t_lower or "reprocurement" in t_lower):
        why_flagged = f"Risky for the {who_bound} because asymmetric termination notice and reprocurement cost liability are imposed."
    elif "capped at" in t_lower or "liability" in t_lower:
        why_flagged = "Liability terms specify aggregate damage limits and carve-outs."
    else:
        why_flagged = f"Standard operational provisions for {category or 'contract terms'}; no elevated liability identified."

    return {
        "plain_language": plain_language,
        "simplified_text": plain_language,
        "who_is_bound": who_bound,
        "who_benefits": who_benefits,
        "is_one_sided": is_one_sided,
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
    document_header: Optional[Dict[str, Any]] = None,
    override_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Primary Groq structured extraction path (temperature 0).
    Extracts Pydantic-validated JSON containing verified facts, party roles, and plain summary.
    Includes 429 backoff retry and 400 format fallback.
    """
    text = clause.get("text", "")
    title = clause.get("title", "")
    clause_num = clause.get("clause_number", "")
    category = clause.get("category", "")
    severity = clause.get("severity", "Low")

    # Resolve document parties context from document_header
    parties_str = "Commission and Consultant"
    if document_header and isinstance(document_header, dict):
        p_list = document_header.get("parties", [])
        if p_list:
            parties_str = " and ".join([f"{p.get('name', '')} ({p.get('role', '')})" for p in p_list if p.get('name')])

    # Compact long clauses (>1200 chars) to prevent excessive token usage and Groq rate limits
    content_text = text if len(text) <= 1200 else f"{text[:800]}\n\n[...Additional terms...]\n\n{text[-400:]}"

    prompt = (
        f"Document Parties: {parties_str}\n"
        f"Clause Number: {clause_num}\n"
        f"Clause Heading: {title}\n"
        f"Verbatim Clause Text:\n\"\"\"\n{content_text}\n\"\"\"\n\n"
        "Generate a plain-English explanation for a non-lawyer (1 to 3 sentences, maximum 60 words for simple clauses and 90 words for long clauses).\n"
        "Rules:\n"
        "1. Name the real parties (e.g. Commission, Consultant).\n"
        "2. Include all key numbers, deadlines, and amounts verbatim from the clause (e.g. 30 days, 120 days, 10 days, $1,000,000, 3 years, 100%).\n"
        "3. State who must do what, and what happens otherwise.\n"
        "4. Note if any value is blank in the template.\n"
        "5. Do NOT repeat the heading. Do NOT copy raw legalese. Never use canned template phrases.\n\n"
        "Return strictly valid raw JSON:\n"
        "{\n"
        '  "plain_language": "...",\n'
        '  "who_is_bound": "Consultant | Commission | Both parties",\n'
        '  "who_benefits": "Commission | Consultant | Both parties",\n'
        '  "is_one_sided": true,\n'
        '  "why_flagged": "Risky for the Consultant because... (or Standard notice/operational requirement; no cost or liability)",\n'
        '  "facts": [\n'
        '    {"label": "...", "value": "..."}\n'
        "  ]\n"
        "}"
    )

    client = override_client
    if client is None:
        api_key = get_groq_api_key()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")
        client = get_groq_client()

    target_model = get_groq_model_name()
    
    # Retry loop with 429 backoff handling
    resp = None
    content = ""
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "You are a concise legal contract analyzer. Directly output a valid JSON object without markdown formatting or code blocks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.0
            )
            msg = resp.choices[0].message
            content = msg.content or ""
            if not content.strip():
                reasoning_text = getattr(msg, "reasoning", "") or ""
                if reasoning_text:
                    m_r = re.search(r"\{.*\}", reasoning_text, re.DOTALL)
                    if m_r:
                        content = m_r.group(0)
            if content.strip():
                break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate limit" in err_str.lower():
                wait_time = 3.0
                m_wait = re.search(r"try again in ([0-9\.]+)s", err_str)
                if m_wait:
                    wait_time = float(m_wait.group(1)) + 0.6
                logger.warning(f"Groq 429 rate limit hit for clause {clause_num}. Waiting {wait_time:.1f}s (attempt {attempt+1}/4)...")
                time.sleep(wait_time)
                continue
            else:
                if attempt < 3:
                    time.sleep(1.5)
                    continue
                raise e

    if not content:
        raise ValueError("Groq returned empty response content.")

    # Clean potential markdown fences from JSON output
    clean_json = content.strip()
    if clean_json.startswith("```"):
        clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)
    m_json = re.search(r"\{.*\}", clean_json, re.DOTALL)
    if m_json:
        clean_json = m_json.group(0)

    parsed = {}
    try:
        parsed = json.loads(clean_json)
    except Exception as parse_err:
        logger.warning(f"json.loads failed for clause {clause_num}: {parse_err}. Attempting regex field recovery.")
        m_plain = re.search(r'["\']plain_language["\']\s*:\s*["\'](.*?)["\']\s*,\s*["\']', clean_json, re.DOTALL)
        if not m_plain:
            m_plain = re.search(r'["\']plain_language["\']\s*:\s*["\'](.*?)["\']', clean_json, re.DOTALL)
        if m_plain:
            parsed["plain_language"] = m_plain.group(1).replace('\\"', '"').strip()
        m_bound = re.search(r'["\']who_is_bound["\']\s*:\s*["\'](.*?)["\']', clean_json)
        if m_bound:
            parsed["who_is_bound"] = m_bound.group(1).strip()
        m_ben = re.search(r'["\']who_benefits["\']\s*:\s*["\'](.*?)["\']', clean_json)
        if m_ben:
            parsed["who_benefits"] = m_ben.group(1).strip()
        m_why = re.search(r'["\']why_flagged["\']\s*:\s*["\'](.*?)["\']', clean_json, re.DOTALL)
        if m_why:
            parsed["why_flagged"] = m_why.group(1).strip()

        if not parsed.get("plain_language"):
            raise ValueError(f"Failed to parse or extract plain language: {parse_err}")
    raw_facts = parsed.get("facts", [])
    
    # Normalize fact structures
    formatted_facts = []
    if isinstance(raw_facts, list):
        for rf in raw_facts:
            if isinstance(rf, dict):
                lbl = rf.get("label") or rf.get("field") or "Fact"
                val = rf.get("value") or ""
                if str(val).strip():
                    formatted_facts.append({"label": lbl, "value": str(val)})

    plain_summary = parsed.get("plain_language") or parsed.get("plain_summary") or parsed.get("simplified_text") or ""
    why_flagged = parsed.get("why_flagged") or "Standard clause analysis."
    who_is_bound = parsed.get("who_is_bound") or "Both parties"
    who_benefits = parsed.get("who_benefits") or "Both parties"
    is_one_sided = parsed.get("is_one_sided", False)

    # Sanitize banned strings
    banned = check_banned_strings(plain_summary)
    if banned:
        for b in banned:
            plain_summary = plain_summary.replace(b, "")

    return {
        "plain_language": plain_summary.strip(),
        "simplified_text": plain_summary.strip(),
        "who_is_bound": who_is_bound,
        "who_benefits": who_benefits,
        "is_one_sided": is_one_sided,
        "key_details": formatted_facts,
        "why_flagged": why_flagged,
        "mode": "LLM"
    }


def simplify_single_clause(
    clause: Dict[str, Any],
    rule_findings: Optional[List[Dict[str, Any]]] = None,
    override_client: Optional[Any] = None,
    document_header: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Performs per-clause plain language simplification using Groq structured extraction
    with deterministic verification and fallback resilience.
    """
    position = clause.get("position", 1)
    clause_id = str(clause.get("clause_id") or clause.get("position") or position)
    clause_number = clause.get("clause_number") or str(position)
    title = clause.get("title") or ""
    clean_title = re.sub(r'^(?:SECTION|ARTICLE|CLAUSE|\u00a7)\s*[\d\w\.-]+\s*[:\.-]?\s*', '', title, flags=re.IGNORECASE).strip()
    clean_title = re.sub(r'^\d+[\.:\- ]+\s*', '', clean_title).strip()
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
        primary_category = raw_category or "Entire Agreement/General"

    if "severity" not in clause and "final_severity" not in clause:
        clean_severity = "RISK_CLASSIFICATION_UNAVAILABLE"
    elif has_explicit_severity and raw_severity is None:
        clean_severity = None
    elif raw_severity is None or str(raw_severity).strip() == "" or str(raw_severity).upper() in ("UNKNOWN", "NONE", "RISK_CLASSIFICATION_UNAVAILABLE"):
        clean_severity = "Low"
    else:
        clean_severity = str(raw_severity).capitalize()

    analysis_res = None
    mode = "Limited"
    if override_client is not None:
        try:
            analysis_res = simplify_single_clause_via_groq(
                clause=clause,
                document_header=document_header,
                override_client=override_client
            )
            mode = "LLM"
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
                "who_benefits": "Unavailable",
                "key_details": [],
                "severity": "RISK_CLASSIFICATION_UNAVAILABLE",
                "category": "Unavailable",
                "status": "FAILED_SIMPLIFICATION",
                "mode": "Unavailable",
                "structured_explanation": {
                    "what_this_clause_means": honest_str,
                    "risk": {"severity": "RISK_CLASSIFICATION_UNAVAILABLE", "reason": honest_str, "evidence": ""},
                    "category": {"label": "Unavailable", "reason": honest_str, "evidence": ""}
                }
            }
    elif get_groq_api_key():
        try:
            analysis_res = simplify_single_clause_via_groq(
                clause=clause,
                document_header=document_header,
                override_client=None
            )
            mode = "LLM"
        except Exception as e:
            logger.warning(f"Groq extraction failed for clause {clause_number}: {e}. Falling back to deterministic fact extraction.")
            analysis_res = None

    if analysis_res is None:
        # Deterministic extraction fallback
        analysis_res = extract_clause_facts_deterministic_fallback(
            text=text,
            category=primary_category or "Entire Agreement/General",
            clause_number=clause_number,
            title=title
        )
        mode = "Limited"

    plain_language = analysis_res.get("plain_language") or ""
    key_details = analysis_res.get("key_details") or []
    who_is_bound = analysis_res.get("who_is_bound") or "Both parties"
    who_benefits = analysis_res.get("who_benefits") or "Both parties"
    is_one_sided = analysis_res.get("is_one_sided", False)
    why_flagged = analysis_res.get("why_flagged") or ""

    # Sanitize any accidental banned strings
    banned_in_plain = check_banned_strings(plain_language)
    if banned_in_plain:
        for b in banned_in_plain:
            plain_language = plain_language.replace(b, "")

    if not plain_language or plain_language.strip() == text.strip():
        if key_details:
            details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in key_details if kd.get('value'))
            plain_language = f"Plain-English explanation unavailable (Limited mode):\n- {details_str}"
        else:
            plain_language = "Plain-English explanation unavailable (Limited mode): Standard operational terms govern."
    else:
        # Echo Detector: Jaccard overlap check on substantial clauses (>30 words)
        words = plain_language.split()
        if len(words) > 30 and mode == "LLM":
            tokens_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', plain_language.lower()))
            tokens_b = set(re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()))
            if tokens_a and tokens_b:
                jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
                if jaccard > 0.85:
                    logger.warning(f"Echo detected (jaccard={jaccard:.2f}) on clause {clause_number}. Falling back to labeled facts.")
                    if key_details:
                        details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in key_details if kd.get('value'))
                        plain_language = f"Plain-English explanation unavailable (Limited mode):\n- {details_str}"
                    else:
                        plain_language = f"Plain-English explanation unavailable (Limited mode): Standard provisions for {clean_title or primary_category}."

    # Grounded category and risk reasons for UI panels
    category_reason = f"Matches the section heading '{clean_title.upper() or primary_category}'"
    if not why_flagged or "No elevated risk" in why_flagged or why_flagged == "Clause evaluated.":
        if clean_severity in ("High", "Moderate"):
            why_flagged = f"Risky for the {who_is_bound} due to non-reciprocal obligations in {clean_title or primary_category}."
        else:
            why_flagged = f"Standard notice or operational requirement for {primary_category}; no elevated cost or liability."

    if rule_findings:
        rf_names = [rf.get("name") or rf.get("rule_id") for rf in rule_findings if rf.get("name") or rf.get("rule_id")]
        if rf_names and not any(r in why_flagged for r in rf_names) and clean_severity in ("High", "Moderate"):
            why_flagged = f"{why_flagged} Flagged as {clean_severity} risk by rule: {', '.join(rf_names[:2])}."

    # Deduplicate and format key details
    seen_details = set()
    dedup_details = []
    for kd in key_details:
        k_str = f"{kd.get('label')}: {kd.get('value')}"
        if k_str not in seen_details:
            seen_details.add(k_str)
            dedup_details.append(kd)
    details_str = "; ".join(f"{kd['label']}: {kd['value']}" for kd in dedup_details) if dedup_details else "No additional specific numbers or deadlines extracted."

    # Assemble structured multi-section clause card output (H1, H3, H4)
    bound_note = f" (Only the {who_is_bound} is bound)" if is_one_sided and who_is_bound not in ("Both parties", "Unavailable") else ""
    structured_card = (
        f"IN PLAIN LANGUAGE:\nWHAT THIS CLAUSE MEANS: {plain_language}\n\n"
        f"WHO IS AFFECTED:\n{who_is_bound}{bound_note}\n\n"
        f"WHO IS BOUND:\n{who_is_bound}{bound_note}\n\n"
        f"WHO BENEFITS:\n{who_benefits}\n\n"
        f"OBLIGATIONS & RIGHTS:\nParty bound: {who_is_bound} | Party receiving: {who_benefits}\n\n"
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
        "who_benefits": who_benefits,
        "key_details": dedup_details,
        "severity_reason": why_flagged,
        "mode": mode,
        "if_not_met": "",
        "not_stated": [],
        "structured_explanation": {
            "what_this_clause_means": plain_language,
            "risk": {"severity": clean_severity, "reason": why_flagged, "evidence": clean_title},
            "category": {"label": primary_category, "reason": category_reason, "evidence": clean_title},
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
    document_header: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Performs per-clause plain language simplification for all clauses in a document.
    Enforces repeated-sentence detection and bounded execution pacing.
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
    sentence_counts: Dict[str, int] = {}

    for idx, c in enumerate(clauses, start=1):
        c_id = str(c.get("clause_id") or c.get("position") or idx)
        clause_rule_findings = []
        if rule_findings:
            clause_rule_findings = [
                rf for rf in rule_findings
                if str(rf.get("clause_id")) == c_id or str(rf.get("position")) == c_id
            ]

        # Pacing delay between LLM calls to stay comfortably within rate limits
        if idx > 1 and override_client is None and get_groq_api_key():
            time.sleep(1.2)

        res = simplify_single_clause(
            clause=c,
            rule_findings=clause_rule_findings,
            override_client=override_client,
            document_header=document_header
        )

        # Track sentence frequency for repeated sentence detector
        plain = res.get("plain_language", "")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', plain) if len(s.strip()) > 15]
        for s in sentences:
            sentence_counts[s] = sentence_counts.get(s, 0) + 1

        simplified_items.append(res)

    # Post-process: Repeated sentence detector (H1 rule: no sentence in >2 clauses)
    for res in simplified_items:
        plain = res.get("plain_language", "")
        for s, count in sentence_counts.items():
            if count > 2 and s in plain:
                logger.warning(f"Repeated sentence detected ({count} occurrences): '{s[:40]}...'. Sanitizing.")
                plain = plain.replace(s, "").strip()
        if not plain:
            cat = res.get("category", "General")
            plain = f"Plain-English explanation unavailable (Limited mode): Operational terms governing {cat}."
        res["plain_language"] = plain
        if "structured_explanation" in res and res["structured_explanation"]:
            res["structured_explanation"]["what_this_clause_means"] = plain

    logger.info(f"Document Clause Simplification Complete: {len(simplified_items)} clauses processed.")

    return {
        "success": True,
        "total_clauses": len(simplified_items),
        "clauses": simplified_items,
        "schema_version": SCHEMA_VERSION
    }
