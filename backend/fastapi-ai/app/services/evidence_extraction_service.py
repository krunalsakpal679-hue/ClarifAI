"""
ClarifAI Structured Document Evidence Extraction Service Module
Extracts structured semantic evidence from legal clauses and documents:
parties, roles, obligations, rights, prohibitions, amounts, currencies,
dates, deadlines, notice periods, conditions, exceptions, triggers, consequences.
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Role definitions across document archetypes
ROLE_PATTERNS = [
    # Lease / Tenancy
    {"type": "lease", "actor": "tenant / lessee", "counterparty": "landlord / lessor",
     "actor_re": re.compile(r"\b(?:lessee|tenant)\b", re.IGNORECASE),
     "counterparty_re": re.compile(r"\b(?:lessor|landlord)\b", re.IGNORECASE)},
    # Employment
    {"type": "employment", "actor": "employee", "counterparty": "employer / company",
     "actor_re": re.compile(r"\b(?:employee|executive|worker)\b", re.IGNORECASE),
     "counterparty_re": re.compile(r"\b(?:employer|company|firm)\b", re.IGNORECASE)},
    # NDA / Confidentiality
    {"type": "nda", "actor": "receiving party", "counterparty": "disclosing party",
     "actor_re": re.compile(r"\b(?:receiving\s+party|recipient)\b", re.IGNORECASE),
     "counterparty_re": re.compile(r"\b(?:disclosing\s+party|discloser)\b", re.IGNORECASE)},
    # Commercial / Services
    {"type": "services", "actor": "vendor / contractor / provider", "counterparty": "client / customer",
     "actor_re": re.compile(r"\b(?:vendor|contractor|provider|consultant|service\s+provider|supplier)\b", re.IGNORECASE),
     "counterparty_re": re.compile(r"\b(?:client|customer|buyer|purchaser)\b", re.IGNORECASE)},
    # Loan / Finance
    {"type": "loan", "actor": "borrower", "counterparty": "lender",
     "actor_re": re.compile(r"\b(?:borrower|debtor)\b", re.IGNORECASE),
     "counterparty_re": re.compile(r"\b(?:lender|creditor|bank)\b", re.IGNORECASE)},
]

# Modality Patterns
OBLIGATION_PATTERNS = re.compile(
    r"\b(?:shall|must|is\s+required\s+to|agrees\s+to|covenants\s+to|undertakes\s+to|obligated\s+to)\s+([^.,;]+)",
    re.IGNORECASE
)
PROHIBITION_PATTERNS = re.compile(
    r"\b(?:shall\s+not|must\s+not|is\s+prohibited\s+from|cannot|will\s+not|may\s+not|not\s+to)\s+([^.,;]+)",
    re.IGNORECASE
)
RIGHT_PATTERNS = re.compile(
    r"\b(?:may|is\s+entitled\s+to|has\s+the\s+right\s+to|is\s+permitted\s+to|shall\s+be\s+lawful\s+for)\s+([^.,;]+)",
    re.IGNORECASE
)

# Financial & Temporal Patterns
AMOUNT_PATTERN = re.compile(
    r"(?:₹|Rs\.?|\$|€|£|USD|INR|EUR|GBP)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore|million|billion|per\s+month|per\s+annum|only|\/-))?",
    re.IGNORECASE
)
PERCENTAGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*%", re.IGNORECASE)
DEADLINE_PATTERN = re.compile(
    r"\b(?:within\s+\d+\s+(?:days|months|hours|business\s+days)|on\s+or\s+before\s+the\s+\d+(?:st|nd|rd|th)?(?:\s+day)?(?:\s+of\s+[a-z]+)?|by\s+the\s+\d+(?:st|nd|rd|th)?)\b",
    re.IGNORECASE
)
NOTICE_PERIOD_PATTERN = re.compile(
    r"\b(?:\d+|one|two|three|four|five|ten|fifteen|thirty|sixty|ninety)\s+(?:calendar\s+)?(?:days?|months?|weeks?|hours?)\s+(?:prior\s+)?(?:written\s+)?notice\b",
    re.IGNORECASE
)

# Condition, Exception, Trigger, Consequence Patterns
CONDITION_PATTERN = re.compile(
    r"\b(?:if|when|upon|after|before|provided\s+that|subject\s+to|in\s+the\s+event\s+that|on\s+condition\s+that)\s+([^.,;]+)",
    re.IGNORECASE
)
EXCEPTION_PATTERN = re.compile(
    r"\b(?:save\s+and\s+except|except\s+to\s+the\s+extent|other\s+than|excluding|with\s+the\s+exception\s+of|unless\s+otherwise\s+agreed|except\s+as\s+provided)\s+([^.,;]+)",
    re.IGNORECASE
)
CONSEQUENCE_PATTERN = re.compile(
    r"\b(?:re-enter|repossess|forfeit|terminate|determination\s+of\s+the\s+term|vest\s+in|indemnify|liquidated\s+damages|accrue\s+interest|immediate\s+eviction|injunctive\s+relief)\b",
    re.IGNORECASE
)


def extract_clause_evidence(text: str, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts structured legal evidence from a single clause text string.
    """
    if not text or not text.strip():
        return {
            "roles": [],
            "obligations": [],
            "rights": [],
            "prohibitions": [],
            "amounts": [],
            "percentages": [],
            "deadlines": [],
            "notice_periods": [],
            "conditions": [],
            "exceptions": [],
            "consequences": [],
            "has_reentry_or_forfeiture": False,
            "has_vesting_or_assignment_restriction": False,
            "has_quiet_enjoyment": False,
            "has_indemnity_or_repair": False,
        }

    combined = f"{title or ''} {text}".strip()

    # Detect Roles
    detected_roles = []
    for r in ROLE_PATTERNS:
        if r["actor_re"].search(combined) or r["counterparty_re"].search(combined):
            detected_roles.append({
                "contract_type": r["type"],
                "actor": r["actor"],
                "counterparty": r["counterparty"]
            })

    # Modalities
    obligations = [m.group(0).strip() for m in OBLIGATION_PATTERNS.finditer(text)][:5]
    prohibitions = [m.group(0).strip() for m in PROHIBITION_PATTERNS.finditer(text)][:5]
    rights = [m.group(0).strip() for m in RIGHT_PATTERNS.finditer(text)][:5]

    # Financial & Temporal
    amounts = [m.group(0).strip() for m in AMOUNT_PATTERN.finditer(text)]
    percentages = [m.group(0).strip() for m in PERCENTAGE_PATTERN.finditer(text)]
    deadlines = [m.group(0).strip() for m in DEADLINE_PATTERN.finditer(text)]
    notice_periods = [m.group(0).strip() for m in NOTICE_PERIOD_PATTERN.finditer(text)]

    # Conditions & Exceptions
    conditions = [m.group(0).strip() for m in CONDITION_PATTERN.finditer(text)][:4]
    exceptions = [m.group(0).strip() for m in EXCEPTION_PATTERN.finditer(text)][:4]
    consequences = [m.group(0).strip() for m in CONSEQUENCE_PATTERN.finditer(text)]

    # Semantic flags
    t_low = text.lower()
    has_reentry = bool(re.search(r"\b(?:re-enter|re-entry|demise\s+shall\s+(?:absolutely\s+)?determine|arrears?|forfeiture)\b", t_low))
    has_vesting = bool(re.search(r"\b(?:vest\s+in\s+the\s+lessor|not\s+assign|underlet|mortgage|part\s+with\s+(?:the\s+)?possession)\b", t_low))
    has_quiet_enjoyment = bool(re.search(r"\b(?:peaceably\s+hold\s+and\s+enjoy|quiet\s+enjoyment|lawful\s+interruption|disturbance\s+by\s+the\s+lessor)\b", t_low))
    has_indemnity = bool(re.search(r"\b(?:indemnify|hold\s+harmless|rates,\s+taxes|assessments|tenantable\s+repair|good\s+and\s+substantial\s+repair)\b", t_low))

    return {
        "roles": detected_roles,
        "obligations": obligations,
        "rights": rights,
        "prohibitions": prohibitions,
        "amounts": amounts,
        "percentages": percentages,
        "deadlines": deadlines,
        "notice_periods": notice_periods,
        "conditions": conditions,
        "exceptions": exceptions,
        "consequences": consequences,
        "has_reentry_or_forfeiture": has_reentry,
        "has_vesting_or_assignment_restriction": has_vesting,
        "has_quiet_enjoyment": has_quiet_enjoyment,
        "has_indemnity_or_repair": has_indemnity,
    }
