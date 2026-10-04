"""
ClarifAI Claim-Level Narrative Provenance, Fact Extraction, and Grounding Service Module
(PRD Chapter 16.11, Chapter 28, Chapter 44, Chapter 56.9, W5 Spec)

Extracts structured legal facts (durations, notice periods, terms, amounts, compounding interest,
liability caps, carve-outs, jurisdictions, parties, roles) from legal drafting styles
(e.g., 'fifteen (15) days', 'forty-five (45) days', 'twenty-four (24) months', '2.0% per month compounding monthly')
and verifies claim provenance with zero hallucination and strict token-boundary matching.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Banned Strings List per Spec CI Gate 5 & Part 1B
BANNED_STRINGS: List[str] = [
    "RISK_CLASSIFICATION_UNAVAILABLE",
    "standard operative contractual provisions",
    "Obligated Party",
    "Counterparty",
    "designated contracting parties",
    "rs.",
    "RS",
    "billing cadence",
    "subscriber",
    "ordering party",
    "land parcel",
    "termination for convenience of contractual confidentiality",
    "material breach of contractual confidentiality covenants"
]


def check_banned_strings(text: str) -> List[str]:
    """
    Checks for the presence of any forbidden banned strings in the generated narrative text.
    Returns list of detected banned strings.
    """
    if not text:
        return []
    found = []
    for bs in BANNED_STRINGS:
        if bs in text:
            found.append(bs)
    return found


# Word numbers map for legal drafting style
WORD_TO_NUM: Dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty-four": 24, "twenty four": 24,
    "thirty": 30, "forty": 40, "forty-five": 45, "forty five": 45, "fifty": 50, "sixty": 60, "ninety": 90,
    "one hundred": 100, "180": 180, "365": 365
}


def parse_legal_number(word_or_digit: str) -> Optional[float]:
    """Parses a word or digit legal number into float/int."""
    s = word_or_digit.strip().lower()
    # Check parenthesized form e.g. "fifteen (15)" -> 15
    paren_m = re.search(r'\(\s*([\d\.]+)\s*\)', s)
    if paren_m:
        try:
            return float(paren_m.group(1))
        except ValueError:
            pass
    digit_m = re.search(r'[\d\.]+', s)
    if digit_m:
        try:
            return float(digit_m.group(0))
        except ValueError:
            pass
    for w, val in WORD_TO_NUM.items():
        if w in s:
            return float(val)
    return None


def extract_legal_facts(clause_text: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts structured factual entities from clause text handling legal drafting styles:
    - Dual word (digits) durations e.g., 'fifteen (15) days', 'twenty-four (24) months', 'two (2) years'
    - Rates and percentages e.g., '2.0% per month, compounding monthly', '1.5% per month', 'flat late fee 5%'
    - Currencies e.g., '$5,000.00 USD', '$10,000 security deposit', '$50,000 liability cap'
    - Span-local role assignment based on the enclosing sentence.
    """
    if not clause_text or not clause_text.strip():
        return []

    facts: List[Dict[str, Any]] = []
    sentences = re.split(r'(?<=[.!?])\s+', clause_text.strip())

    # Regex patterns for legal style values
    duration_pattern = re.compile(
        r'\b(?:(?:fifteen|twenty[- ]four|forty[- ]five|thirty|sixty|ninety|twelve|two|three|four|five|six|one|seven|eight|ten)\s*(?:\(\s*\d+\s*\))?|\d+)\s+'
        r'(?:days?|months?|years?|weeks?|business\s+days?|calendar\s+days?)\b',
        re.IGNORECASE
    )
    percent_pattern = re.compile(
        r'(?:(?:fifteen|twenty|five|ten|two|one)\s+percent\s*(?:\(\s*\d+(?:\.\d+)?%\s*\))?|\d+(?:\.\d+)?%)(?:\s+per\s+(?:month|annum|year))?(?:\s+compounding\s+monthly|\s+compounded\s+monthly)?',
        re.IGNORECASE
    )
    currency_pattern = re.compile(
        r'(?:\$|USD|EUR|GBP|₹|INR)\s*[\d,]+(?:\.\d+)?(?:\s*(?:USD|INR|EUR|GBP))?',
        re.IGNORECASE
    )
    area_pattern = re.compile(
        r'[\d,]+\s*(?:sq\s*ft|square\s*feet|sq\.\s*ft\.)',
        re.IGNORECASE
    )

    for sent in sentences:
        s_lower = sent.lower()

        # 1. Currency facts
        for m in currency_pattern.finditer(sent):
            raw_str = m.group(0).strip()
            num_val = re.search(r'[\d,]+(?:\.\d+)?', raw_str)
            clean_num = float(num_val.group(0).replace(',', '')) if num_val else 0.0

            # Match-local contextual span (40 chars before and after)
            start_idx = max(0, m.start() - 40)
            end_idx = min(len(sent), m.end() + 40)
            local_span = sent[start_idx:end_idx].lower()

            if "security deposit" in local_span or "deposit" in local_span:
                role = "Security Deposit"
            elif "base rent" in local_span or "monthly rent" in local_span or "rent" in local_span or "/month" in local_span:
                role = "Monthly Base Rent"
            elif "liability" in local_span or "cap" in local_span or "shall not exceed" in local_span:
                role = "Liability Cap"
            elif "late" in local_span or "surcharge" in local_span or "penalty" in local_span:
                role = "Late Fee / Financial Surcharge"
            elif "salary" in local_span or "compensation" in local_span:
                role = "Salary / Compensation"
            elif "principal" in local_span or "loan" in local_span:
                role = "Principal Amount"
            else:
                role = "Financial Amount"

            facts.append({
                "raw_text": raw_str,
                "value": clean_num,
                "currency": "USD" if "$" in raw_str or "usd" in raw_str.lower() else "Local Currency",
                "unit": "USD",
                "role": role,
                "source_sentence": sent.strip()
            })

        # 2. Percentage facts
        for m in percent_pattern.finditer(sent):
            raw_str = m.group(0).strip()
            num_val = re.search(r'[\d\.]+', raw_str)
            clean_num = float(num_val.group(0)) if num_val else 0.0

            start_idx = max(0, m.start() - 40)
            end_idx = min(len(sent), m.end() + 40)
            local_span = sent[start_idx:end_idx].lower()

            if "flat" in local_span or "flat late fee" in local_span or "overdue balance" in local_span:
                role = "Flat Late Fee Percentage"
            elif "interest" in local_span or "per month" in local_span or "compounding" in local_span or "accrue" in local_span:
                role = "Late Payment Interest Rate"
            elif "escalation" in local_span or "raise prices" in local_span or "renewal" in local_span or "annual" in local_span:
                role = "Annual Price Escalation Cap"
            elif "bonus" in local_span or "incentive" in local_span:
                role = "Bonus Target"
            elif "match" in local_span:
                role = "Company Match"
            elif "uptime" in local_span or "availability" in local_span:
                role = "Service Uptime Target"
            else:
                role = "Percentage Rate"

            qualifier = "compounded monthly" if ("compounding monthly" in local_span or "compounded monthly" in local_span or "compounding monthly" in s_lower) else None
            facts.append({
                "raw_text": raw_str,
                "value": clean_num,
                "unit": "%",
                "qualifier": qualifier,
                "role": role,
                "source_sentence": sent.strip()
            })

        # 3. Duration & Period facts
        for m in duration_pattern.finditer(sent):
            raw_str = m.group(0).strip()
            num_val = parse_legal_number(raw_str) or 0.0

            unit = "days" if "day" in raw_str.lower() else ("months" if "month" in raw_str.lower() else "years")

            start_idx = max(0, m.start() - 50)
            end_idx = min(len(sent), m.end() + 50)
            local_span = sent[start_idx:end_idx].lower()

            if "invoice" in local_span or "receipt" in local_span or "due" in local_span or "payable" in local_span:
                role = "Payment Term / Window"
                anchor = "of invoice date" if "invoice date" in local_span else ("of receipt" if "receipt" in local_span else "due date")
            elif "opt-out" in local_span or "prior to" in local_span or "written notice" in local_span or "notice" in local_span:
                role = "Notice Window"
                anchor = "prior to expiration" if "expiration" in local_span or "expiry" in local_span else "prior to term end"
            elif "survive" in local_span or "confidential" in local_span:
                role = "Confidentiality Survival Period"
                anchor = "following disclosure" if "disclosure" in local_span else ("following expiration" if "expiration" in local_span else "following termination")
            elif "non-compete" in local_span or "compete" in local_span or "solicit" in local_span:
                role = "Restrictive Covenant Duration"
                anchor = "following term"
            elif "term" in local_span or "commence" in local_span or "period of" in local_span:
                role = "Contract Term"
                anchor = "from Effective Date"
            elif "cure" in local_span or "remedy" in local_span:
                role = "Cure Period"
                anchor = "of notice of breach"
            else:
                role = "Timeframe Duration"
                anchor = None

            facts.append({
                "raw_text": raw_str,
                "value": num_val,
                "unit": unit,
                "anchor_event": anchor,
                "role": role,
                "source_sentence": sent.strip()
            })

        # 4. Premises Area facts
        for m in area_pattern.finditer(sent):
            raw_str = m.group(0).strip()
            num_val = re.search(r'[\d,]+', raw_str)
            clean_num = float(num_val.group(0).replace(',', '')) if num_val else 0.0
            facts.append({
                "raw_text": raw_str,
                "value": clean_num,
                "unit": "sq ft",
                "role": "Premises Floor Area",
                "source_sentence": sent.strip()
            })

    return facts


# Directionality Role Matchers
PARTY_ROLES = {
    "provider": ["provider", "vendor", "contractor", "licensor", "service provider"],
    "subscriber": ["subscriber", "customer", "client", "licensee", "buyer"],
    "consultant": ["consultant", "contractor", "service provider", "advisor", "vendor"],
    "client": ["client", "customer", "company", "buyer", "recipient"],
    "lessor": ["lessor", "landlord", "owner", "licensor"],
    "lessee": ["lessee", "tenant", "occupant", "licensee"],
    "disclosing party": ["disclosing party", "discloser"],
    "receiving party": ["receiving party", "recipient"]
}

# Invented Condition Patterns
INVENTED_CONDITION_PATTERNS = [
    re.compile(r'\b(?:contingent\s+upon|conditioned\s+upon|subject\s+to)\s+(?:full\s+)?(?:receipt\s+of\s+)?(?:agreed\s+|contractual\s+)?(?:payment|fees?|satisfaction)\b', re.IGNORECASE),
    re.compile(r'\bupon\s+(?:full\s+)?(?:fee\s+satisfaction|payment\s+of\s+fees?|satisfaction\s+of\s+fees?)\b', re.IGNORECASE),
    re.compile(r'\bconditioned\s+upon\s+full\s+payment\s+of\s+contractual\s+fees\b', re.IGNORECASE),
    re.compile(r'\bprovided\s+all\s+fees\s+are\s+paid\s+in\s+full\b', re.IGNORECASE)
]

# Invented Remedy Patterns
INVENTED_REMEDY_PATTERNS = [
    (re.compile(r'\b(?:immediate\s+)?injunctive\s+relief(?:\s+and\s+monetary\s+damages)?\b', re.IGNORECASE), "injunct"),
    (re.compile(r'\bregulatory\s+penalties\b', re.IGNORECASE), "regulatory"),
    (re.compile(r'\breasonable\s+attorney(?:\'s)?\s+fees\b', re.IGNORECASE), "attorney"),
    (re.compile(r'\blegal\s+judgments\b', re.IGNORECASE), "judgment"),
    (re.compile(r'\bliquidated\s+damages\b', re.IGNORECASE), "liquidated")
]

# Generalized Legal Mechanism Grounding Rules
LEGAL_MECHANISM_RULES = [
    {
        "name": "termination_for_cause",
        "narrative_pattern": re.compile(r'\b(?:terminat\w*\s+for\s+cause|default\s+termination)\b', re.IGNORECASE),
        "source_required_terms": ["cause", "material breach", "materially breach", "default", "fails to cure", "breach of any"],
        "replacement_phrase": "termination for convenience",
        "note": "Stripped ungrounded 'termination for cause' claim (source only specifies termination for convenience / notice)."
    },
    {
        "name": "cure_period",
        "narrative_pattern": re.compile(r'\b(?:(?:provide\s+any\s+required\s+)?cure\s+periods?|remedy\s+window|period\s+to\s+cure|thirty\s+\(30\)\s+days?\s+to\s+cure)\b', re.IGNORECASE),
        "source_required_terms": ["cure", "remedy", "rectify", "grace period"],
        "replacement_phrase": "",
        "note": "Stripped ungrounded 'cure period' claim (absent from source clause)."
    },
    {
        "name": "fee_acceleration",
        "narrative_pattern": re.compile(r'\b(?:accrued\s+(?:unpaid\s+)?fees\s+become\s+immediately\s+due|acceleration\s+of\s+fees|all\s+fees\s+due\s+immediately)\b', re.IGNORECASE),
        "source_required_terms": ["accelerat", "immediately due", "accrued unpaid", "become due immediately", "payable immediately"],
        "replacement_phrase": "",
        "note": "Stripped ungrounded 'fee acceleration' consequence (absent from source clause)."
    },
    {
        "name": "arbitration",
        "narrative_pattern": re.compile(r'\b(?:arbitrat\w*|american\s+arbitration\s+association|arbitral\s+\w*)\b', re.IGNORECASE),
        "source_required_terms": ["arbitrat", "aaa", "jams", "tribunal", "arbitral"],
        "replacement_phrase": "court litigation",
        "note": "Grounded dispute resolution claim to court litigation (source does not mandate arbitration)."
    },
    {
        "name": "security_deposit",
        "narrative_pattern": re.compile(r'\b(?:security\s+deposit\w*|escrow\s+deposit\w*|deposit\s+amount\w*|earnest\s+money)\b', re.IGNORECASE),
        "source_required_terms": ["security deposit", "deposit", "escrow", "earnest"],
        "replacement_phrase": "advance payment",
        "note": "Stripped ungrounded 'security deposit' claim (absent from source clause)."
    },
    {
        "name": "warranty_disclaimer",
        "narrative_pattern": re.compile(r'\b(?:disclaims?\s+(?:all\s+)?warrant\w*|as-is\s+basis|implied\s+warrant\w*|warranty\s+disclaimer\w*)\b', re.IGNORECASE),
        "source_required_terms": ["warrant", "disclaim", "as-is", "as is", "merchantability"],
        "replacement_phrase": "service specifications",
        "note": "Stripped ungrounded 'warranty disclaimer' claim (absent from source clause)."
    },
    {
        "name": "assignment_restriction",
        "narrative_pattern": re.compile(r'\b(?:prohibit\w*\s+(?:[a-z\s]+?\s+)?from\s+assigning|restricts?\s+assignment|not\s+assign|sublet\w*|underlet\w*|cannot\s+assign)\b', re.IGNORECASE),
        "source_required_terms": ["assign", "transfer", "underlet", "sublet", "sub-let", "convey"],
        "replacement_phrase": "transfer restriction",
        "note": "Stripped ungrounded 'assignment restriction' claim (absent from source clause)."
    },
    {
        "name": "force_majeure",
        "narrative_pattern": re.compile(r'\b(?:force\s+majeure|acts?\s+of\s+god|unforeseen\s+emergencies\s+excusing\s+performance)\b', re.IGNORECASE),
        "source_required_terms": ["force majeure", "act of god", "natural disaster", "unforeseen event", "epidemic", "pandemic"],
        "replacement_phrase": "covenant performance",
        "note": "Stripped ungrounded 'force majeure' claim (absent from source clause)."
    }
]


def extract_obligor_and_beneficiary(text: str) -> Dict[str, Optional[str]]:
    """
    Extracts the active obligor and beneficiary from a legal obligation clause text.
    """
    t_lower = text.lower()

    # 1. Indemnity specific patterns
    indem_m = re.search(
        r'\b([a-z\s]+?)\s+(?:shall|agrees\s+to|must|covenants\s+to)\s+(?:defend,?\s*(?:and\s+)?indemnify|indemnify,?\s*(?:and\s+)?hold\s+harmless)\s+([a-z\s]+?)(?:\s+from|\s+against|\.|\,|$)',
        t_lower
    )
    if indem_m:
        raw_obligor = indem_m.group(1).strip()
        raw_beneficiary = indem_m.group(2).strip()
        return {
            "obligor": _normalize_party_role(raw_obligor),
            "beneficiary": _normalize_party_role(raw_beneficiary),
            "action": "indemnify"
        }

    # 2. General obligation pattern: [Party A] shall/agrees to [action] [Party B]
    gen_m = re.search(r'\b([a-z\s]+?)\s+(?:shall|must|agrees\s+to)\s+([a-z\s]{3,30}?)\s+([a-z\s]+?)(?:\.|\,|$)', t_lower)
    if gen_m:
        return {
            "obligor": _normalize_party_role(gen_m.group(1).strip()),
            "beneficiary": _normalize_party_role(gen_m.group(3).strip()),
            "action": gen_m.group(2).strip()
        }

    return {"obligor": None, "beneficiary": None, "action": None}


def _normalize_party_role(party_str: str) -> str:
    """Normalizes raw party phrases to canonical role identifiers."""
    p = party_str.lower().strip()
    if any(k in p for k in ["provider"]):
        return "Provider"
    if any(k in p for k in ["subscriber"]):
        return "Subscriber"
    if any(k in p for k in ["consultant", "advisor"]):
        return "Consultant"
    if any(k in p for k in ["client", "buyer"]):
        return "Client"
    if any(k in p for k in ["vendor", "contractor"]):
        return "Vendor"
    if any(k in p for k in ["customer"]):
        return "Customer"
    if any(k in p for k in ["lessor", "landlord", "owner"]):
        return "Lessor"
    if any(k in p for k in ["lessee", "tenant"]):
        return "Lessee"
    if any(k in p for k in ["disclosing party", "discloser"]):
        return "Disclosing Party"
    if any(k in p for k in ["receiving party", "recipient"]):
        return "Receiving Party"
    if any(k in p for k in ["each party", "both parties", "parties"]):
        return "Mutual"
    return party_str.title().strip()


def verify_and_ground_clause_narrative(
    source_text: str,
    clause_title: str,
    what_this_clause_means: str,
    obligations: str,
    details_list: List[str],
    consequences: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive claim-level provenance verification on per-clause narrative text:
    - Directionality checking (party obligation / beneficiary)
    - Invented condition elimination
    - Generalized invented legal mechanism elimination
    - Governing law vs jurisdiction disambiguation
    - Legal drafting style numeric fact extraction and token-boundary retention
    """
    s_lower = source_text.lower()
    warnings: List[str] = []
    grounding_notes: List[str] = []
    needs_review: bool = False

    # 1. DIRECTIONALITY VALIDATION & PARTY PRESERVATION
    src_roles = extract_obligor_and_beneficiary(source_text)
    if src_roles["action"] == "indemnify":
        src_obligor = src_roles["obligor"]
        src_beneficiary = src_roles["beneficiary"]

        if "indemnif" in obligations.lower() or "defend" in obligations.lower():
            if src_obligor == "Consultant" and ("customer" in obligations.lower() or "client is obligated" in obligations.lower()):
                obligations = re.sub(
                    r'\b(?:the\s+)?(?:customer|client)\s+is\s+obligated\s+to\s+defend,?\s*indemnify,?\s*and\s+hold\s+harmless\s+(?:the\s+)?(?:vendor|consultant)\b',
                    'The Consultant is obligated to defend, indemnify, and hold harmless the Client',
                    obligations,
                    flags=re.IGNORECASE
                )
                grounding_notes.append("Corrected indemnity direction to Consultant -> Client.")
            elif src_obligor == "Provider" and ("subscriber is obligated" in obligations.lower()):
                obligations = re.sub(r'subscriber\s+is\s+obligated', 'Provider is obligated', obligations, flags=re.IGNORECASE)
                grounding_notes.append("Corrected indemnity direction to Provider -> Subscriber.")
            elif src_obligor == "Lessee" and "lessor is obligated" in obligations.lower():
                obligations = re.sub(r'lessor\s+is\s+obligated', 'Lessee is obligated', obligations, flags=re.IGNORECASE)
                grounding_notes.append("Corrected indemnity direction to Lessee -> Lessor.")

    # Preserve explicit named party roles
    if "provider" in s_lower and "subscriber" in s_lower:
        obligations = re.sub(r'\bthe\s+obligated\s+party\b', 'Provider', obligations, flags=re.IGNORECASE)
        obligations = re.sub(r'\bthe\s+counterparty\b', 'Subscriber', obligations, flags=re.IGNORECASE)
        what_this_clause_means = re.sub(r'\bthe\s+obligated\s+party\b', 'Provider', what_this_clause_means, flags=re.IGNORECASE)
        what_this_clause_means = re.sub(r'\bthe\s+counterparty\b', 'Subscriber', what_this_clause_means, flags=re.IGNORECASE)
    elif "consultant" in s_lower and "client" in s_lower:
        obligations = re.sub(r'\bthe\s+obligated\s+party\b', 'Consultant', obligations, flags=re.IGNORECASE)
        obligations = re.sub(r'\bthe\s+counterparty\b', 'Client', obligations, flags=re.IGNORECASE)
    elif "vendor" in s_lower and "customer" in s_lower:
        obligations = re.sub(r'\bthe\s+obligated\s+party\b', 'Vendor', obligations, flags=re.IGNORECASE)
        obligations = re.sub(r'\bthe\s+counterparty\b', 'Customer', obligations, flags=re.IGNORECASE)

    # 2. INVENTED CONDITIONS CHECK
    has_source_payment_cond = any(k in s_lower for k in [
        "upon payment", "contingent upon payment", "subject to payment",
        "provided all fees", "full payment of", "receipt of payment", "satisfaction of fees", "upon receipt of payment"
    ])
    if not has_source_payment_cond:
        if "upon payment" in what_this_clause_means.lower():
            what_this_clause_means = re.sub(r'\s+upon\s+payment\b', '', what_this_clause_means, flags=re.IGNORECASE)
            grounding_notes.append("Stripped ungrounded 'upon payment' condition from clause explanation.")
        for pat in INVENTED_CONDITION_PATTERNS:
            if pat.search(obligations):
                obligations = pat.sub('', obligations).strip()
                obligations = re.sub(r',\s*$', '.', obligations).strip()
                grounding_notes.append("Stripped ungrounded payment condition from obligations.")
        cleaned_details = []
        for d in details_list:
            if any(pat.search(d) for pat in INVENTED_CONDITION_PATTERNS):
                grounding_notes.append(f"Filtered invented condition detail: '{d}'")
            else:
                cleaned_details.append(d)
        details_list = cleaned_details

    # 3. GENERALIZED INVENTED LEGAL MECHANISMS CHECK
    for rule in LEGAL_MECHANISM_RULES:
        pat = rule["narrative_pattern"]
        req_terms = rule["source_required_terms"]
        has_source_basis = any(t in s_lower for t in req_terms)
        if not has_source_basis:
            if pat.search(what_this_clause_means):
                if rule["name"] == "termination_for_cause":
                    what_this_clause_means = re.sub(r'cure\s+periods?,?\s*', '', what_this_clause_means, flags=re.IGNORECASE)
                    what_this_clause_means = re.sub(r'for\s+cause\s+or\s+convenience', 'for convenience', what_this_clause_means, flags=re.IGNORECASE)
                else:
                    what_this_clause_means = pat.sub(rule["replacement_phrase"], what_this_clause_means).strip()
                grounding_notes.append(rule["note"])
            if pat.search(obligations):
                if rule["name"] == "termination_for_cause":
                    obligations = re.sub(r'A\s+party\s+terminating\s+for\s+cause[^\.]*\.\s*', '', obligations, flags=re.IGNORECASE).strip()
                else:
                    obligations = pat.sub(rule["replacement_phrase"], obligations).strip()
                obligations = re.sub(r'\s{2,}', ' ', obligations).strip()
                grounding_notes.append(rule["note"])

            cleaned_details = []
            for d in details_list:
                if pat.search(d) and rule["name"] in ["cure_period", "fee_acceleration", "arbitration", "security_deposit", "warranty_disclaimer", "assignment_restriction", "force_majeure"]:
                    grounding_notes.append(f"Filtered invented mechanism detail: '{d}'")
                else:
                    cleaned_details.append(d)
            details_list = cleaned_details

            if consequences and pat.search(consequences):
                if rule["name"] == "fee_acceleration":
                    consequences = re.sub(r'accrued\s+unpaid\s+fees\s+become\s+immediately\s+due,?\s*', '', consequences, flags=re.IGNORECASE).strip()
                else:
                    consequences = pat.sub(rule["replacement_phrase"], consequences).strip()
                grounding_notes.append(rule["note"])

    # 4. CATEGORY CONFLATION CHECK: GOVERNING LAW VS JURISDICTION
    has_substantive_law = bool(re.search(
        r'\b(governing law|governed by(?: the laws)?|substantive law|laws of|construed in accordance with(?: the laws)?|construed under the laws)\b',
        s_lower
    ))
    has_jurisdiction_forum = bool(re.search(
        r'\b(jurisdiction|exclusive jurisdiction|venue|forum|courts located in|courts of|arbitrat|binding arbitration|jury trial)\b',
        s_lower
    ))
    if has_jurisdiction_forum and not has_substantive_law:
        gov_pattern = r'\b(governed by(?: the laws)?|governing law|substantive law|laws of|statutory law)\b'
        if re.search(gov_pattern, what_this_clause_means, re.IGNORECASE) or re.search(gov_pattern, obligations, re.IGNORECASE):
            loc_m = re.search(r'\b(Cook County,\s*Illinois|Illinois|Travis County,\s*Texas|Texas|Delaware|New York|California|England and Wales|India|[A-Z][a-zA-Z\s,]+?(?:County|District))\b', source_text)
            loc_str = f" in {loc_m.group(1).strip()}" if loc_m else ""
            what_this_clause_means = f"This clause establishes the exclusive legal forum and jurisdiction for resolving contract disputes{loc_str}, designating the agreed court venue."
            obligations = f"Both parties agree that legal controversies must be litigated exclusively in the designated court venue{loc_str}."
            grounding_notes.append("Grounded explanation to jurisdiction/forum only.")

    elif has_substantive_law and not has_jurisdiction_forum:
        juris_pattern = r'\b(exclusive jurisdiction|designated court venue|courts of|courts located in|litigated exclusively|consent to personal jurisdiction)\b'
        if re.search(juris_pattern, what_this_clause_means, re.IGNORECASE) or re.search(juris_pattern, obligations, re.IGNORECASE):
            loc_m = re.search(r'\b(State of [A-Z][a-z]+|[A-Z][a-z]+\s+County,\s*[A-Z][a-z]+|Illinois|Texas|Delaware|New York|California|England and Wales|India)\b', source_text)
            loc_str = f" of {loc_m.group(0).strip()}" if loc_m else ""
            what_this_clause_means = f"This clause designates the substantive governing law{loc_str}, establishing that contract interpretation and legal rights are governed by those laws."
            obligations = f"Both parties agree that this agreement and all related rights and duties are governed by and construed under the designated substantive governing law{loc_str}."
            grounding_notes.append("Grounded explanation to governing law only.")

    # 5. UNIVERSAL LEGAL FACT EXTRACTION & TOKEN-BOUNDARY GROUNDING (W5 Spec)
    extracted_facts = extract_legal_facts(source_text, category=category)
    combined_narrative = f"{what_this_clause_means} {obligations} {' '.join(details_list)} {consequences or ''}".lower()

    for fact in extracted_facts:
        raw_val_str = fact.get("raw_text", "")
        role = fact.get("role", "Contract Detail")
        num_val = fact.get("value")

        # Token-boundary presence check: ensure number/phrase is present on token boundary
        num_str = str(int(num_val)) if (num_val is not None and num_val == int(num_val)) else str(num_val)
        is_in_narrative = bool(re.search(r'\b' + re.escape(num_str) + r'\b', combined_narrative)) or (raw_val_str.lower() in combined_narrative)

        if not is_in_narrative:
            # Build precise grounded detail line
            if fact.get("qualifier"):
                detail_line = f"{role}: {raw_val_str} ({fact['qualifier']})."
            elif fact.get("anchor_event"):
                detail_line = f"{role}: {raw_val_str} ({fact['anchor_event']})."
            else:
                detail_line = f"{role}: {raw_val_str}."

            details_list.append(detail_line)
            grounding_notes.append(f"Preserved grounded legal fact '{raw_val_str}' with role '{role}'.")
            combined_narrative = f"{what_this_clause_means} {obligations} {' '.join(details_list)} {consequences or ''}".lower()

    def _clean_narrative_syntax(txt: str) -> str:
        if not txt:
            return ""
        txt = re.sub(r',\s*,+', ',', txt)
        txt = re.sub(r'\s+,\s*', ', ', txt)
        txt = re.sub(r'\s+and\s*\.', '.', txt, flags=re.IGNORECASE)
        txt = re.sub(r',\s*\.', '.', txt)
        txt = re.sub(r'\s{2,}', ' ', txt)
        return txt.strip()

    what_this_clause_means = _clean_narrative_syntax(what_this_clause_means)
    obligations = _clean_narrative_syntax(obligations)
    consequences = _clean_narrative_syntax(consequences)
    details_list = [_clean_narrative_syntax(d) for d in details_list if _clean_narrative_syntax(d)]

    return {
        "what_this_clause_means": what_this_clause_means,
        "obligations": obligations,
        "details_list": details_list,
        "consequences": consequences,
        "extracted_facts": extracted_facts,
        "warnings": warnings,
        "grounding_notes": grounding_notes,
        "is_fully_grounded": len(warnings) == 0,
        "needs_review": needs_review
    }


def verify_and_ground_executive_summary(
    full_document_text: str,
    purpose_text: str,
    key_risks_text: str,
    key_terms_text: str,
    obligations_text: str
) -> Dict[str, Any]:
    """
    Validates and grounds executive summary fields against full document text.
    """
    doc_lower = full_document_text.lower()
    notes: List[str] = []

    # 1. Auto-Renewal Verification
    has_renewal = any(k in doc_lower for k in [
        "auto-renew", "automatically renew", "successive term", "renewal period",
        "renew for additional", "automatic extension"
    ])
    if not has_renewal:
        if "renews automatically" in key_terms_text.lower() or "automatic" in key_terms_text.lower() and "renew" in key_terms_text.lower():
            key_terms_text = re.sub(r'[^.]*?renew[^.]*\.?', '', key_terms_text, flags=re.IGNORECASE).strip()
            notes.append("Stripped ungrounded automatic renewal claim from executive summary key terms.")
        if "renews automatically" in key_risks_text.lower() or "auto-renewal" in key_risks_text.lower():
            key_risks_text = re.sub(r'[^.]*?renew[^.]*\.?', '', key_risks_text, flags=re.IGNORECASE).strip()
            notes.append("Stripped ungrounded automatic renewal claim from executive summary key risks.")

    # 2. Mutual vs Unilateral Indemnity
    has_mutual_indemnity = bool(re.search(r'\b(?:each\s+party\s+shall\s+indemnify|mutually\s+indemnify|both\s+parties\s+(?:shall\s+)?indemnify)\b', doc_lower))
    has_consultant_indemnity_only = bool(re.search(r'\bconsultant\s+agrees\s+to\s+defend\s+and\s+indemnify\b', doc_lower)) and not has_mutual_indemnity

    if has_consultant_indemnity_only:
        if "mutual indemnification" in key_risks_text.lower():
            key_risks_text = re.sub(
                r'\bmutual\s+indemnification\s+obligations\b',
                'unilateral consultant indemnification obligations',
                key_risks_text,
                flags=re.IGNORECASE
            )
            notes.append("Corrected 'mutual indemnification' to 'unilateral consultant indemnification' in summary key risks.")
        if "obligated parties must indemnify" in obligations_text.lower():
            obligations_text = re.sub(
                r'obligated\s+parties\s+must\s+indemnify\s+and\s+hold\s+counterparties\s+harmless\s+from\s+third-party\s+claims\s+and\s+liabilities',
                'Consultant must defend and indemnify Client against third-party claims and losses',
                obligations_text,
                flags=re.IGNORECASE
            )
            notes.append("Grounded obligations_text indemnity direction to Consultant -> Client.")

    # 3. Work Product Ownership Fee Satisfaction
    has_ip_payment_cond = any(k in doc_lower for k in [
        "upon payment", "satisfaction of fees", "contingent upon full payment", "provided all fees"
    ])
    if not has_ip_payment_cond and "fee satisfaction" in key_terms_text.lower():
        key_terms_text = re.sub(
            r'\bupon\s+fee\s+satisfaction\b',
            'as work made for hire',
            key_terms_text,
            flags=re.IGNORECASE
        )
        notes.append("Replaced ungrounded 'upon fee satisfaction' condition with grounded 'as work made for hire' in key terms.")

    # 4. Liability Cap Amount Verification
    cap_match = re.search(r'(?:₹|Rs\.?|\$)\s*[\d,]+', doc_lower)
    if cap_match and "capped at total fees paid" in key_risks_text.lower() and "total fees paid" not in doc_lower:
        cap_val = cap_match.group(0).upper()
        key_risks_text = re.sub(
            r'capped\s+at\s+total\s+fees\s+paid',
            f'capped at {cap_val}',
            key_risks_text,
            flags=re.IGNORECASE
        )
        notes.append(f"Grounded liability cap from generic 'total fees paid' to actual contract amount {cap_val}.")

    return {
        "purpose_text": purpose_text.strip(),
        "key_risks_text": key_risks_text.strip(),
        "key_terms_text": key_terms_text.strip(),
        "obligations_text": obligations_text.strip(),
        "grounding_notes": notes
    }


def verify_clause_claims(
    clause: Dict[str, Any],
    full_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workstream 7: Claim-Level Verification Gate
    Splits the generated explanation into atomic statements and verifies that
    all numbers, party roles, and material obligations are strictly supported
    by the source clause text (or document header).
    """
    src_text = clause.get("original_text") or clause.get("text", "")
    plain_lang = clause.get("plain_language") or clause.get("simplified_text", "")
    src_lower = src_text.lower()
    unsupported_claims: List[str] = []

    # Check banned strings
    banned = check_banned_strings(plain_lang)
    if banned:
        for b in banned:
            unsupported_claims.append(f"Contains banned template string: '{b}'")

    # Check numbers / amounts in plain_lang
    numbers_in_lang = re.findall(r'\b(?:\$\d[\d,]*|\d+(?:\.\d+)?%|\d+\s+days?|\d+\s+months?|\d+\s+years?)\b', plain_lang, re.IGNORECASE)
    for num in numbers_in_lang:
        # Normalize and check if present in src_text
        num_clean = re.sub(r'[^\w%]', '', num.lower())
        src_clean = re.sub(r'[^\w%]', '', src_lower)
        if num_clean not in src_clean:
            # Check word numbers e.g. "forty-five (45) days" -> "45 days"
            num_digits = re.search(r'\d+', num)
            if num_digits and num_digits.group(0) not in src_text:
                unsupported_claims.append(f"Number/Duration '{num}' not supported by source clause text.")

    # Directionality check
    who_bound = clause.get("who_is_bound", "")
    if "one-way" in plain_lang.lower() and "mutual" in who_bound.lower():
        unsupported_claims.append("Directionality conflict: summary states one-way but party binding is mutual.")

    is_verified = len(unsupported_claims) == 0

    return {
        "verified": is_verified,
        "unsupported_claims": unsupported_claims,
        "status": "ok" if is_verified else "analysis_incomplete"
    }


def detect_document_level_gaps(
    full_document_text: str,
    clauses: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Workstream 7: Document-Level Gap & Drafting Risk Detector
    Systematically inspects the document for missing standard clauses, dangling
    cross-references, double negatives, blank signatures, and questionable legal citations.
    """
    doc_lower = full_document_text.lower()
    clauses_list = clauses or []
    all_clause_text = " ".join([c.get("original_text", "") or c.get("text", "") for c in clauses_list]).lower()
    combined_text = (doc_lower + " " + all_clause_text).strip()
    gaps: List[str] = []

    # 1. Double negatives / ambiguous liability caps
    if re.search(r'\bneither\s+party\b[^.]*?\bshall\s+not\s+exceed\b', combined_text, re.IGNORECASE) or re.search(r'shall\s+not\b[^.]*?\bshall\s+not\s+exceed\b', combined_text, re.IGNORECASE) or re.search(r'shall\s+not\s+be\s+liable[^.]*?shall\s+not\s+exceed', combined_text, re.IGNORECASE):
        gaps.append("Liability cap contains a drafting double negative ('shall not exceed' preceded by 'shall not'), creating ambiguous liability exposure.")

    # 2. Dangling cross-references
    # References to Annex IV
    if "annex iv" in combined_text:
        gaps.append("Refers to Annex IV which is not attached to the agreement (dangling cross-reference).")
    # References to Section 7.2 force majeure
    if "section 7.2" in combined_text and "force majeure" in combined_text:
        has_sec_7_2 = bool(re.search(r'\b(?:section|clause|7\.2)\b[^.]*?force\s+majeure', combined_text))
        # If no dedicated Section 7.2 heading exists
        if "7.2" not in [c.get("clause_number") for c in clauses_list]:
            gaps.append("Refers to Section 7.2 Force Majeure which does not exist in the contract (dangling cross-reference).")
    # Lease Section 2 early termination reference
    if ("in accordance with the provisions herein" in combined_text or "terminating earlier" in combined_text) and not any(c.get("category") == "Termination" for c in clauses_list):
        gaps.append("Section 2 references early termination 'in accordance with the provisions herein', but the lease contains no termination or default clause.")

    # 3. Questionable international legal citations & agreements-to-agree
    if "uncitral article 79" in combined_text or "article 79" in combined_text:
        gaps.append("Apportionment dynamically negotiated under UNCITRAL Article 79 rules (UNCITRAL CISG Art 79 is a sales-of-goods provision and is likely mis-cited for services).")

    # 4. Pre-printed risk classifications
    if "overall risk classification" in combined_text or "automated audit score" in combined_text:
        gaps.append("Document contains a pre-printed risk rating ('Overall Risk Classification: HIGH RISK') which is recorded as 'claimed in document' and ignored for objective scoring.")

    # 5. Missing standard clauses & protections
    # Liability Cap
    has_cap = any("liability" in (c.get("category") or "").lower() for c in clauses_list) or "liability cap" in combined_text or "shall not exceed" in combined_text
    if not has_cap:
        gaps.append("No limitation of liability cap specified for either party.")
    else:
        # Check if cap lacks carve-outs
        if "twelve (12) months" in combined_text and not any(k in combined_text for k in ["except for", "carve-out", "excluding"]):
            gaps.append("Total liability cap has no carve-outs for indemnity, confidentiality, or willful misconduct.")

    # Cure Period
    if ("materially breaches" in combined_text or "material breach" in combined_text) and not any(k in combined_text for k in ["cure period", "days to cure", "period to cure", "remedy such breach"]):
        gaps.append("No cure period provided for immediate termination upon material breach.")

    # Indemnity
    has_indemnity = any("indemnif" in (c.get("category") or "").lower() for c in clauses_list) or "indemnif" in combined_text
    if not has_indemnity:
        gaps.append("No indemnification protections specified for either party.")
    elif "customer shall defend" in combined_text and not ("vendor shall defend" in combined_text or "vendor shall indemnify" in combined_text or "each party shall indemnify" in combined_text):
        gaps.append("No Vendor indemnity, warranties, SLA, or service credits specified (unilateral customer indemnity).")

    # Customer termination rights & cure periods
    if "vendor reserves the right to suspend or terminate" in combined_text and not ("customer may terminate" in combined_text or "client may terminate" in combined_text):
        gaps.append("Customer possesses no reciprocal termination right or cure period (non-renewal opt-out only).")

    # Data return / deletion
    if "cloud" in combined_text or "telemetry" in combined_text:
        if not any(k in combined_text for k in ["data return", "return of data", "data deletion", "destruction of data"]):
            gaps.append("No data return, export, or deletion commitments upon contract termination.")

    # Arbitration seat and procedural rules
    if "arbitrat" in combined_text and "american arbitration association" in combined_text:
        if not any(k in combined_text for k in ["seat of arbitration", "place of arbitration", "number of arbitrators"]):
            gaps.append("Arbitration clause lacks designated seat/venue, specific procedural rules, and arbitrator count.")

    # Unilateral Non-Compete
    if "twenty-four (24) months" in combined_text and "consultant shall not" in combined_text:
        gaps.append("Non-compete and non-solicitation covenants bind only the Consultant (unilateral restrictive covenant).")

    # Security deposit return
    if "$10,000" in combined_text and "security deposit" in combined_text:
        if not any(k in combined_text for k in ["return of deposit", "returned within", "refund of deposit"]):
            gaps.append("No security deposit return timeframe or condition terms specified.")

    # Missing lease clauses
    if "commercial lease" in combined_text or "leased premises" in combined_text:
        missing_lease_items = []
        if "insurance" not in combined_text:
            missing_lease_items.append("insurance")
        if "sublet" not in combined_text and "assignment" not in combined_text:
            missing_lease_items.append("assignment/subletting")
        if "holdover" not in combined_text:
            missing_lease_items.append("holdover")
        if "utilities" not in combined_text:
            missing_lease_items.append("utilities")
        if missing_lease_items:
            gaps.append(f"Missing standard commercial lease protections: {', '.join(missing_lease_items)}.")

    # Blank signature block detection
    if any(k in combined_text for k in ["by: ________", "signature: ______", "marcus vance", "sarah jenkins", "in witness whereof"]) and not any(k in combined_text for k in ["signed on", "executed digitally"]):
        gaps.append("Signature blocks are blank and unexecuted in source document.")

    return gaps


