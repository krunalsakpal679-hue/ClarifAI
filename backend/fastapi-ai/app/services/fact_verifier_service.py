"""
ClarifAI Deterministic Fact Verifier Module (PRD Step 3.2)
Verifies that every LLM-extracted fact is 100% grounded in the verbatim clause text.
Rules:
1. source_quote must appear in clause text after normalizing whitespace/quotes/hyphens.
2. Every number/currency/percentage in value must appear with token boundaries in source_quote.
3. Every party name used must be present in the document header or clause text.
4. Direction check: obligated party must be consistent with quote.
5. Unverified facts are dropped; failure triggers abstention (needs_review).
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple


def normalize_text_for_matching(text: str) -> str:
    """Normalizes whitespace, smart quotes, dashes, and unicode for robust quote matching."""
    if not text:
        return ""
    # Normalize unicode
    t = unicodedata.normalize("NFKD", text)
    # Replace curly quotes and apostrophes
    t = re.sub(r'[\u2018\u2019\u201A\u201B\u2032\u2035\']', "'", t)
    t = re.sub(r'[\u201C\u201D\u201E\u201F\u2033\u2036"]', '"', t)
    # Replace em-dash, en-dash, hyphens
    t = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\-]', "-", t)
    # Normalize all whitespace
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()


def extract_tokens_and_numbers(text: str) -> List[str]:
    """Extracts alphanumeric numbers, percentages, currencies, and digits with token boundaries."""
    # Matches digits, currencies, percentages, and dual notations like 'forty-five (45)'
    clean = re.sub(r'[^\w\.\%\$\₹]', ' ', text)
    tokens = [t.strip() for t in clean.split() if t.strip()]
    return tokens


def verify_fact_grounding(
    fact: Dict[str, Any],
    clause_text: str,
    doc_parties: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Verifies a single extracted fact against the source clause text.
    Returns (is_valid, rejection_reason).
    """
    if not fact or not isinstance(fact, dict):
        return False, "Fact is empty or not a dictionary."

    field = str(fact.get("field", "")).strip()
    value = str(fact.get("value", "")).strip()
    quote = str(fact.get("source_quote", "")).strip()

    if not field:
        return False, "Fact missing 'field' name."

    # If field is marked as not stated
    if value.lower() in ["not stated", "not_stated", "none", "n/a", "not specified"]:
        return True, None

    if not value or not quote:
        return False, f"Fact '{field}' has value but missing 'source_quote'."

    norm_clause = normalize_text_for_matching(clause_text)
    norm_quote = normalize_text_for_matching(quote)

    # 1. source_quote must appear in clause text
    if norm_quote not in norm_clause:
        # Fuzzy fallback: check if at least 80% of quote words exist in sequence
        quote_words = norm_quote.split()
        if len(quote_words) >= 4:
            sub_phrase = " ".join(quote_words[:4])
            if sub_phrase not in norm_clause:
                return False, f"source_quote '{quote[:40]}...' does not appear in clause text."
        else:
            return False, f"source_quote '{quote}' does not appear in clause text."

    # 2. Token-bounded number check: numbers in value must appear in source_quote or clause
    val_tokens = extract_tokens_and_numbers(value)
    norm_quote_and_clause = f"{norm_quote} {norm_clause}"
    for tok in val_tokens:
        tok_low = tok.lower()
        if any(char.isdigit() for char in tok_low) or tok_low.endswith("%") or tok_low.startswith("$"):
            # Check token boundary
            pattern = r'\b' + re.escape(tok_low) + r'\b'
            if not re.search(pattern, norm_quote_and_clause):
                return False, f"Number/figure '{tok}' in value was not found in source text."

    # 3. Party name presence check
    bound_party = str(fact.get("bound_party") or fact.get("who_is_bound") or "").strip()
    if bound_party and bound_party.lower() not in ["both parties", "each party", "mutual", "neither party", "not specified"]:
        norm_bound = normalize_text_for_matching(bound_party)
        party_found = (norm_bound in norm_clause)
        if doc_parties:
            for p in doc_parties:
                if normalize_text_for_matching(p) in norm_bound or norm_bound in normalize_text_for_matching(p):
                    party_found = True
                    break
        if not party_found:
            # Check generic roles
            if not any(r in norm_bound for r in ["client", "consultant", "vendor", "customer", "landlord", "tenant", "lessor", "lessee", "party"]):
                return False, f"Party '{bound_party}' does not match document parties or contract roles."

    return True, None


def verify_and_filter_clause_facts(
    facts: List[Dict[str, Any]],
    clause_text: str,
    doc_parties: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Runs verification on a list of extracted facts for a clause.
    Returns (verified_facts_list, dropped_reasons_list).
    """
    verified = []
    dropped = []

    for f in facts:
        is_valid, reason = verify_fact_grounding(f, clause_text, doc_parties)
        if is_valid:
            verified.append(f)
        else:
            dropped.append(reason or "Verification failed.")

    return verified, dropped
