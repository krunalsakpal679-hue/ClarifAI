"""
ClarifAI Legal Clause Categorization Service Module
Implements evidence-grounded clause categorization into the fixed PRD-approved 8-category set,
using dominant subject scoring and negative evidence carve-outs.
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException, status
from app.models.clause_categorization import ClauseCategoryEnum, APPROVED_CATEGORIES_SET
from app.services.evidence_extraction_service import extract_clause_evidence

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Dominant Subject Scorer Weights & Specificity Patterns
RULE_CATEGORY_AFFINITY: Dict[str, Tuple[ClauseCategoryEnum, int]] = {
    "R001": (ClauseCategoryEnum.RENEWAL, 10),              # Auto-Renewal
    "R002": (ClauseCategoryEnum.TERMINATION, 10),          # Early-Termination Penalty
    "R003": (ClauseCategoryEnum.PAYMENT, 10),              # Hidden/Add-on Charges
    "R004": (ClauseCategoryEnum.PAYMENT, 10),              # Late-Payment Penalty
    "R005": (ClauseCategoryEnum.LIABILITY, 10),            # Excessive Liability Transfer
    "R006": (ClauseCategoryEnum.LIABILITY, 10),            # Broad Indemnification
    "R007": (ClauseCategoryEnum.TERMINATION, 8),           # Unilateral Modification / Termination
    "R008": (ClauseCategoryEnum.TERMINATION, 10),          # Unfavorable Termination
    "R009": (ClauseCategoryEnum.TERMINATION, 7),           # Unusual Notice Requirement
    "R010": (ClauseCategoryEnum.CONFIDENTIALITY, 10),      # Restrictive Confidentiality
    "R011": (ClauseCategoryEnum.INTELLECTUAL_PROPERTY, 10),# Broad IP Transfer
    "R012": (ClauseCategoryEnum.DISPUTE_RESOLUTION, 10),   # Arbitration/Dispute Restriction
    "R013": (ClauseCategoryEnum.PRIVACY, 10),              # Data/Privacy Obligation
    "R014": (ClauseCategoryEnum.LIABILITY, 8),             # Restrictive Employment/Business Obligation
    "R015": (ClauseCategoryEnum.LIABILITY, 10),            # Uncapped Liability Carve-Out
}

DOMINANT_CONSEQUENCE_PATTERNS = [
    (re.compile(r"\b(?:resulting\s+in|lead\s+to|entitled?\s+to|cause\s+for|triggering|subject\s+to)\s+(?:immediate\s+)?(?:termination|determination|forfeiture|re-entry|cancellation|eviction)\b", re.IGNORECASE), ClauseCategoryEnum.TERMINATION, 9),
    (re.compile(r"\b(?:resolve|settled?|adjudicated?)\s+(?:all\s+)?(?:claims?|disputes?|differences?)\s+through\s+(?:binding\s+)?(?:arbitration|courts?|litigation|mediation)\b", re.IGNORECASE), ClauseCategoryEnum.DISPUTE_RESOLUTION, 9),
    (re.compile(r"\b(?:dispute\s+resolution|exclusive\s+jurisdiction|governing\s+law|arbitration\s+clause)\b", re.IGNORECASE), ClauseCategoryEnum.DISPUTE_RESOLUTION, 6),
    (re.compile(r"\b(?:maintain|keep|hold|preserve)\s+(?:the\s+)?(?:strict\s+)?(?:confidentiality|secrecy|non-disclosure)\b", re.IGNORECASE), ClauseCategoryEnum.CONFIDENTIALITY, 9),
    (re.compile(r"\b(?:assigns?|transfer|vest\s+in|exclusive\s+property\s+of)\s+(?:all\s+)?(?:intellectual\s+property|patents?|copyrights?|inventions?|technology)\b", re.IGNORECASE), ClauseCategoryEnum.INTELLECTUAL_PROPERTY, 9),
    (re.compile(r"\b(?:under\s+no\s+circumstances\s+shall|in\s+no\s+event\s+shall|neither\s+party\s+shall\s+be\s+liable\s+for)\s+(?:any\s+)?(?:indirect|consequential|punitive|special)\s+damages\b", re.IGNORECASE), ClauseCategoryEnum.LIABILITY, 9),
    (re.compile(r"\b(?:renew|extend|continue)\s+(?:the\s+)?(?:term|agreement|lease)\s+(?:for\s+(?:an\s+)?additional|successive)\b", re.IGNORECASE), ClauseCategoryEnum.RENEWAL, 9),
]

CATEGORY_SCORING_RULES = {
    ClauseCategoryEnum.PAYMENT: {
        "positive": [
            (re.compile(r"\b(?:monthly\s+(?:ground\s+)?rent|ground\s+rent|yielding\s+and\s+paying|payable\s+in\s+advance|due\s+by\s+the\s+5th|on\s+or\s+before\s+the\s+5th|undisputed\s+invoices\s+shall\s+be\s+paid|late\s+payment\s+(?:fee|penalty|interest)|accrue\s+interest\s+at\s+(?:the\s+rate\s+of|a\s+rate\s+of))\b", re.IGNORECASE), 6),
            (re.compile(r"\b(?:remit\s+payment|invoices?|billing|payment\s+terms|compensation\s+for\s+services|net\s+30(?:\s+days)?)\b", re.IGNORECASE), 4),
            (re.compile(r"(?:₹|Rs\.?|\$|€|USD|INR)\s*[\d,]+", re.IGNORECASE), 3),
            (re.compile(r"\b(?:pay|payment|price|currency|costs?|charge|deposit)\b", re.IGNORECASE), 1),
        ],
        "negative": [
            (re.compile(r"\b(?:without\s+any\s+(?:payment|compensation|reimbursement|fee)|shall\s+pay\s+no\s+(?:royalties|fees|compensation)|pay\s+no\s+royalties|without\s+financial\s+reimbursement)\b", re.IGNORECASE), -10),
            (re.compile(r"\b(?:even\s+if\s+customer\s+has\s+paid|provided\s+all\s+(?:previous\s+)?(?:service\s+)?fees\s+have\s+been\s+settled)\b", re.IGNORECASE), -6),
            (re.compile(r"\b(?:confidentiality\s+(?:over|of|regarding)|confidential\s+information\s+(?:including|regarding)|maintain\s+(?:the\s+)?confidentiality\s+of)\s+.*?(?:pricing|payment|billing|fees?|structures?)\b", re.IGNORECASE), -8),
            (re.compile(r"\b(?:billing\s+or\s+payment\s+dispute|dispute\s+arising\s+from\s+invoices?)\b", re.IGNORECASE), -4),
            (re.compile(r"\b(?:re-enter|re-entry|demise\s+shall\s+(?:absolutely\s+)?determine|forfeiture)\b", re.IGNORECASE), -3),
        ]
    },
    ClauseCategoryEnum.TERMINATION: {
        "positive": [
            (re.compile(r"\b(?:re-enter|re-entry|demise\s+shall\s+(?:absolutely\s+)?determine|determination\s+of\s+the\s+term|sooner\s+determination|forfeiture|in\s+arrear\s+for\s+the\s+space\s+of)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:terminate\s+this\s+agreement|termination\s+for\s+cause|termination\s+for\s+convenience|right\s+to\s+terminate|notice\s+of\s+termination|early\s+termination\s+fee)\b", re.IGNORECASE), 7),
            (re.compile(r"\b(?:terminate|termination|cancel|cancellation|cure\s+period|default\s+resulting\s+in|material\s+breach)\b", re.IGNORECASE), 4),
            (re.compile(r"\b(?:expire|expiration|end\s+of\s+term)\b", re.IGNORECASE), 2),
        ],
        "negative": []
    },
    ClauseCategoryEnum.RENEWAL: {
        "positive": [
            (re.compile(r"\b(?:peaceably\s+hold\s+and\s+enjoy|quiet\s+enjoyment|peacefully\s+occupy|lawful\s+interruption\s+or\s+disturbance)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:automatically\s+renew|auto-renew|automatic\s+renewal|successive\s+(?:one-year|annual)\s+(?:terms|periods)|notice\s+of\s+non-renewal|extend\s+the\s+term\s+for\s+successive)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:renew|renewal|extension\s+of\s+term|extend\s+the\s+term|term\s+of\s+\d+\s+years)\b", re.IGNORECASE), 4),
            (re.compile(r"\b(?:initial\s+term|duration\s+of\s+agreement)\b", re.IGNORECASE), 2),
        ],
        "negative": []
    },
    ClauseCategoryEnum.LIABILITY: {
        "positive": [
            (re.compile(r"\b(?:indemnify\s+and\s+(?:keep\s+indemnified|hold\s+harmless)|defend,?\s*indemnify|hold\s+harmless\s+from\s+and\s+against|indemnify\s+against\s+any\s+and\s+all\s+claims)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:limitation\s+of\s+liability|liability\s+cap|aggregate\s+liability|consequential\s+damages|indirect\s+damages|punitive\s+damages)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:pay\s+all\s+(?:existing\s+and\s+future\s+)?(?:rates|taxes|assessments|outgoings)|tenantable\s+repair|good\s+and\s+substantial\s+repair|keep\s+in\s+repair|unlawful\s+or\s+offensive\s+purpose)\b", re.IGNORECASE), 5),
            (re.compile(r"\b(?:competing\s+business|non-compete|non-solicitation|restrictive\s+covenant|duty\s+of\s+loyalty)\b", re.IGNORECASE), 5),
            (re.compile(r"\b(?:liable|liability|damages|losses|claims|indemnity)\b", re.IGNORECASE), 2),
        ],
        "negative": []
    },
    ClauseCategoryEnum.INTELLECTUAL_PROPERTY: {
        "positive": [
            (re.compile(r"\b(?:vest\s+in\s+the\s+lessor|vesting\s+of\s+buildings|not\s+assign,?\s*underlet,?\s*mortgage|part\s+with\s+(?:the\s+)?possession|sublet\s+the\s+premises|assignment\s+restriction)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:work\s+made\s+for\s+hire|ownership\s+of\s+deliverables|assigns\s+all\s+right,\s+title\s+and\s+interest|intellectual\s+property|copyrights?|trademarks?|patents?|trade\s+secrets?|license\s+grant|exclusive\s+property\s+of\s+client)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:ip|proprietary\s+rights|ownership|license|licensor|licensee|source\s+code)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.CONFIDENTIALITY: {
        "positive": [
            (re.compile(r"\b(?:confidential\s+information|non-disclosure|nda|strict\s+secrecy|keep\s+confidential|proprietary\s+information|maintain\s+(?:the\s+)?(?:strict\s+)?confidentiality|confidentiality\s+of)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:confidential|confidentiality|secret|disclose|disclosure)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.PRIVACY: {
        "positive": [
            (re.compile(r"\b(?:personal\s+data|personally\s+identifiable|pii|gdpr|data\s+subject|data\s+protection\s+regulation|processing\s+of\s+personal\s+data)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:privacy|data\s+protection|privacy\s+policy)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.DISPUTE_RESOLUTION: {
        "positive": [
            (re.compile(r"\b(?:binding\s+arbitration|american\s+arbitration\s+association|arbitrator|exclusive\s+jurisdiction|governing\s+law|venue\s+shall\s+be|jury\s+trial\s+waiver|class\s+action\s+waiver|courts\s+of)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:arbitrat|litigation|dispute\s+resolution|dispute\s+arising)\b", re.IGNORECASE), 4),
        ],
        "negative": [
            (re.compile(r"\b(?:in\s+pursuance\s+of|the\s+said\s+agreement|lessee\s+covenants|witness\s+whereof)\b", re.IGNORECASE), -4)
        ]
    },
}

CONFIDENCE_FLOOR: int = 3


def validate_category_value(val: str) -> ClauseCategoryEnum:
    """
    Validates that a category string strictly belongs to the fixed 8-value PRD set.
    Raises HTTPException(422) if outside the set.
    """
    if val not in APPROVED_CATEGORIES_SET:
        logger.error(f"Structured output validation failed: Rejected out-of-set category '{val}'.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_CATEGORY_REJECTED",
                "message": f"Category '{val}' is outside the fixed PRD-approved 8-category set."
            }
        )
    return ClauseCategoryEnum(val)


def score_clause_categories(
    text: str,
    title: str = "",
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> List[Tuple[ClauseCategoryEnum, int]]:
    """
    Scores all 8 approved categories based on evidence-weighted scoring:
    (a) count and specificity of positive pattern matches
    (b) negative evidence carve-outs and disqualifiers
    (c) dominant consequence/remedy action proximity
    (d) presence of firing rule-engine findings (R001-R015)
    
    Returns ranked list of (category, score) tuples meeting the confidence floor.
    """
    combined_content = f"{title} {text}".strip()
    clean_content = re.sub(r'\blimited\s+liability\s+(?:company|partnership|llc|llp)\b', '', combined_content, flags=re.IGNORECASE)

    scores: Dict[ClauseCategoryEnum, int] = {cat: 0 for cat in ClauseCategoryEnum}

    # 1. Rule Engine Findings Signal Weighting
    if rule_findings:
        for rf in rule_findings:
            r_id = rf.get("rule_id", "")
            if r_id in RULE_CATEGORY_AFFINITY:
                target_cat, boost = RULE_CATEGORY_AFFINITY[r_id]
                scores[target_cat] += boost

    # 2. Dominant Consequence / Legal Remedy Weighting
    for dom_pat, dom_cat, dom_weight in DOMINANT_CONSEQUENCE_PATTERNS:
        if dom_pat.search(clean_content):
            scores[dom_cat] += dom_weight

    # 3. Category Specificity and Evidence Pattern Scoring
    for cat_enum, rules in CATEGORY_SCORING_RULES.items():
        for pos_pat, weight in rules["positive"]:
            matches = len(pos_pat.findall(clean_content))
            if matches > 0:
                scores[cat_enum] += weight * min(matches, 3)

        for neg_pat, penalty in rules["negative"]:
            if neg_pat.search(clean_content):
                scores[cat_enum] += penalty

    # Filter by confidence floor
    ranked_categories: List[Tuple[ClauseCategoryEnum, int]] = [
        (cat, score) for cat, score in scores.items() if score >= CONFIDENCE_FLOOR
    ]

    # Sort descending by score
    ranked_categories.sort(key=lambda x: x[1], reverse=True)
    return ranked_categories


def categorize_clause_records(
    clauses_input: List[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Categorizes an ordered list of clause records into the fixed 8-value PRD category set
    with evidence-weighted dominant subject ranking and rule signal integration.
    """
    if not clauses_input:
        logger.warning("Categorization received empty clause list.")
        return {
            "success": True,
            "total_clauses": 0,
            "clauses": [],
            "schema_version": SCHEMA_VERSION
        }

    categorized_records: List[Dict[str, Any]] = []

    for idx, clause in enumerate(clauses_input, start=1):
        c_id = str(clause.get("clause_id") or clause.get("position") or idx)
        text = clause.get("text", "")
        title = clause.get("title", "") or ""

        # Filter clause-specific rule findings if provided
        clause_rfs = []
        if rule_findings:
            clause_rfs = [
                rf for rf in rule_findings
                if str(rf.get("clause_id")) == c_id or str(rf.get("position")) == c_id
            ]
        elif "rule_findings" in clause and isinstance(clause["rule_findings"], list):
            clause_rfs = clause["rule_findings"]

        # Evidence-weighted scoring
        ranked = score_clause_categories(text=text, title=title, rule_findings=clause_rfs)

        assigned_categories: List[ClauseCategoryEnum] = [
            validate_category_value(cat.value) for cat, _ in ranked
        ]

        record = dict(clause)
        record["categories"] = assigned_categories
        categorized_records.append(record)

    logger.info(f"Clause Categorization Complete: {len(categorized_records)} clauses processed.")

    return {
        "success": True,
        "total_clauses": len(categorized_records),
        "clauses": categorized_records,
        "schema_version": SCHEMA_VERSION
    }
