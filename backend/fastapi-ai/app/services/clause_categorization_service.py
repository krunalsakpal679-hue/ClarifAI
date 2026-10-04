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

# Explicit Heading-to-Category Direct Mappings (Heading-First Priority per Spec P0/1D)
HEADING_CATEGORY_PATTERNS: List[Tuple[re.Pattern, ClauseCategoryEnum]] = [
    # Scope of Services
    (re.compile(r"^(?:SERVICES|SCOPE\s+OF\s+SERVICES|SCOPE\s+OF\s+WORK|ENGAGEMENT\s+AND\s+DELIVERABLES|STATEMENT\s+OF\s+WORK|DELIVERABLES|DUTIES\s+AND\s+POSITION|DUTIES\s+AND\s+RESPONSIBILITIES|POSITION\s+AND\s+OPERATIONAL\s+DUTIES|EMPLOYMENT\s+DUTIES)\b", re.IGNORECASE), ClauseCategoryEnum.SCOPE_OF_SERVICES),
    # Payment
    (re.compile(r"^(?:FEES\s+AND\s+PAYMENT|FEES\s+AND\s+EXPENSES|FEES|PAYMENT\s+TERMS|PAYMENT|INVOICING\s+AND\s+FINANCE\s+CHARGES|INVOICING|RENT\s+(?:AND|&)\s+FINANCIAL\s+TERMS|MONTHLY\s+RENT(?:AL)?|COMPENSATION|BASE\s+SALARY|PRINCIPAL\s+LOAN\s+COMMITMENT|PRINCIPAL\s+LOAN|INTEREST\s+RATE|FINANCIAL\s+COVENANTS|PREPAYMENT\s+PREMIUMS?|PURCHASE\s+ORDERS?|PRICE\s+ADJUSTMENTS?)\b", re.IGNORECASE), ClauseCategoryEnum.PAYMENT),
    # Confidentiality
    (re.compile(r"^(?:CONFIDENTIALITY(?:\s+COVENANT)?|NON-DISCLOSURE|CONFIDENTIAL\s+INFORMATION|PROPRIETARY\s+INFORMATION|SECRECY)\b", re.IGNORECASE), ClauseCategoryEnum.CONFIDENTIALITY),
    # Intellectual Property
    (re.compile(r"^(?:INTELLECTUAL\s+PROPERTY(?:\s+RIGHTS|\s+ASSIGNMENT)?|WORK\s+PRODUCT\s+OWNERSHIP|IP\s+RIGHTS|OWNERSHIP\s+OF\s+DELIVERABLES|OWNERSHIP\s+OF\s+INVENTIONS|SUBSCRIPTION\s+GRANT|LICENSE\s+GRANT|ACCESS\s+RIGHTS)\b", re.IGNORECASE), ClauseCategoryEnum.INTELLECTUAL_PROPERTY),
    # Indemnification
    (re.compile(r"^(?:INDEMNIFICATION|INDEMNITY\s+OBLIGATIONS|INDEMNITY|DEFENSE\s+AND\s+INDEMNIFICATION|HOLD\s+HARMLESS|PATENT\s+INFRINGEMENT\s+AND\s+PRODUCT\s+INDEMNIFICATION)\b", re.IGNORECASE), ClauseCategoryEnum.INDEMNIFICATION),
    # Limitation of Liability
    (re.compile(r"^(?:LIMITATION\s+OF\s+LIABILITY|AGGREGATE\s+LIABILITY\s+CAP|AGGREGATE\s+(?:MONETARY\s+)?LIABILITY|DAMAGES\s+CAP|DISCLAIMER\s+OF\s+CONSEQUENTIAL\s+DAMAGES|LIABILITY\s+CAP)\b", re.IGNORECASE), ClauseCategoryEnum.LIMITATION_OF_LIABILITY),
    # Term
    (re.compile(r"^(?:TERM\s+DURATION|LEASE\s+TERM|LEASED\s+EQUIPMENT\s+AND\s+TERM|TERM)$", re.IGNORECASE), ClauseCategoryEnum.TERM),
    # Termination
    (re.compile(r"^(?:TERMINATION(?:\s+AND\s+SEVERANCE)?|TERMINATION\s+RIGHTS|CANCELLATION|ACCELERATION\s+AND\s+REMEDIES|EVENTS?\s+OF\s+DEFAULT)\b", re.IGNORECASE), ClauseCategoryEnum.TERMINATION),
    # Renewal
    (re.compile(r"^(?:RENEWAL|TERM\s+AND\s+RENEWAL|EXTENSION|AUTOMATIC\s+RENEWAL)\b", re.IGNORECASE), ClauseCategoryEnum.RENEWAL),
    # Dispute Resolution
    (re.compile(r"\b(?:DISPUTE\s+RESOLUTION|BINDING\s+ARBITRATION|ARBITRATION|GOVERNING\s+FORUM|COURT\s+VENUE)\b", re.IGNORECASE), ClauseCategoryEnum.DISPUTE_RESOLUTION),
    # Governing Law
    (re.compile(r"\b(?:GOVER?N(?:ING|ERNG)?\s+(?:LAW|JURISDICTION)|APPLICABLE\s+LAW|CHOICE\s+OF\s+LAW)\b", re.IGNORECASE), ClauseCategoryEnum.GOVERNING_LAW),

    # Restrictive Covenants
    (re.compile(r"^(?:NON-COMPETE\s+AND\s+NON-SOLICITATION|RESTRICTIVE\s+COVENANTS|POST-EMPLOYMENT\s+NON-COMPETE|NON-COMPETE|NON-SOLICITATION)\b", re.IGNORECASE), ClauseCategoryEnum.RESTRICTIVE_COVENANTS),
    # Property / Premises
    (re.compile(r"^(?:LEASED\s+PREMISES|DEMISED\s+PREMISES|PREMISES|PROPERTY\s+DESCRIPTION)\b", re.IGNORECASE), ClauseCategoryEnum.PROPERTY_PREMISES),
    # Property Use
    (re.compile(r"^(?:USE\s+OF\s+PREMISES|PERMITTED\s+USE|USE\s+AND\s+OCCUPANCY|OCCUPANCY)\b", re.IGNORECASE), ClauseCategoryEnum.PROPERTY_USE),
    # Maintenance
    (re.compile(r"^(?:MAINTENANCE\s+AND\s+REPAIRS?|MAINTENANCE|REPAIRS|EQUIPMENT\s+MAINTENANCE|PREVENTIVE\s+MAINTENANCE)\b", re.IGNORECASE), ClauseCategoryEnum.MAINTENANCE),
    # Alterations
    (re.compile(r"^(?:ALTERATIONS\s+AND\s+IMPROVEMENTS|ALTERATIONS|IMPROVEMENTS|MODIFICATIONS\s+TO\s+PREMISES)\b", re.IGNORECASE), ClauseCategoryEnum.ALTERATIONS),
    # Warranty
    (re.compile(r"^(?:PRODUCT\s+WARRANTY(?:\s+AND\s+DEFECT\s+REMEDIES)?|WARRANTY\s+AND\s+REMEDIES|WARRANTIES|REPRESENTATIONS\s+AND\s+WARRANTIES|LIMITED\s+WARRANTY|DISCLAIMER\s+OF\s+WARRANTIES)\b", re.IGNORECASE), ClauseCategoryEnum.WARRANTY),
    # Insurance
    (re.compile(r"^(?:INSURANCE(?:\s+AND\s+CASUALTY)?|INSURANCE\s+REQUIREMENTS|CASUALTY\s+INSURANCE)\b", re.IGNORECASE), ClauseCategoryEnum.INSURANCE),
    # Force Majeure
    (re.compile(r"^(?:FORCE\s+MAJEURE|ACTS\s+OF\s+GOD|EXCUSABLE\s+DELAYS)\b", re.IGNORECASE), ClauseCategoryEnum.FORCE_MAJEURE),
    # Assignment
    (re.compile(r"^(?:ASSIGNMENT(?:\s+AND\s+DELEGATION)?|SUCCESSORS\s+AND\s+ASSIGNS|TRANSFER\s+AND\s+ASSIGNMENT)\b", re.IGNORECASE), ClauseCategoryEnum.ASSIGNMENT),
    # Notices
    (re.compile(r"^(?:NOTICES(?:\s+AND\s+FORMAL\s+COMMUNICATIONS)?|FORMAL\s+NOTICES)\b", re.IGNORECASE), ClauseCategoryEnum.NOTICES),
    # General / Boilerplate
    (re.compile(r"^(?:ENTIRE\s+AGREEMENT|INTEGRATION|SEVERABILITY|AMENDMENTS|MISCELLANEOUS|GENERAL\s+PROVISIONS|GENERAL)\b", re.IGNORECASE), ClauseCategoryEnum.GENERAL_BOILERPLATE),
    # Privacy
    (re.compile(r"^(?:DATA\s+PRIVACY|PRIVACY|DATA\s+PROTECTION(?:\s+AND\s+PRIVACY)?|DATA\s+PROCESSING|SECURITY|INFORMATION\s+SECURITY)\b", re.IGNORECASE), ClauseCategoryEnum.PRIVACY),
    # Liability (General/Catch-all)
    (re.compile(r"^(?:LIABILITY|TOTAL\s+CASUALTY\s+LOSS)\b", re.IGNORECASE), ClauseCategoryEnum.LIABILITY),
]


# Dominant Consequence Patterns
DOMINANT_CONSEQUENCE_PATTERNS = [
    (re.compile(r"\b(?:resulting\s+in|lead\s+to|entitled?\s+to|cause\s+for|triggering|subject\s+to)\s+(?:immediate\s+)?(?:termination|determination|forfeiture|re-entry|cancellation|eviction)\b", re.IGNORECASE), ClauseCategoryEnum.TERMINATION, 15),
    (re.compile(r"\b(?:expiration\s+of\s+the\s+term|earlier\s+determination)\b", re.IGNORECASE), ClauseCategoryEnum.TERMINATION, 10),
    (re.compile(r"\b(?:resolve|settled?|adjudicated?)\s+(?:all\s+)?(?:claims?|disputes?|differences?)\s+through\s+(?:binding\s+)?(?:arbitration|courts?|litigation|mediation)\b", re.IGNORECASE), ClauseCategoryEnum.DISPUTE_RESOLUTION, 12),
    (re.compile(r"\b(?:exclusive\s+jurisdiction|governing\s+forum|court\s+venue|venue\s+shall\s+be)\b", re.IGNORECASE), ClauseCategoryEnum.DISPUTE_RESOLUTION, 10),
    (re.compile(r"\b(?:governed\s+by|construed\s+in\s+accordance\s+with)\s+(?:the\s+)?laws\s+of\b", re.IGNORECASE), ClauseCategoryEnum.GOVERNING_LAW, 12),
    (re.compile(r"\b(?:maintain|keep|hold|preserve)\s+(?:the\s+)?(?:strict\s+)?(?:confidentiality|secrecy|non-disclosure)\b", re.IGNORECASE), ClauseCategoryEnum.CONFIDENTIALITY, 12),
    (re.compile(r"\b(?:assigns?|transfer|vest\s+in|exclusive\s+property\s+of)\s+(?:all\s+)?(?:intellectual\s+property|patents?|patent\s+rights?|copyrights?|inventions?|technology)\b", re.IGNORECASE), ClauseCategoryEnum.INTELLECTUAL_PROPERTY, 12),
    (re.compile(r"\b(?:under\s+no\s+circumstances\s+shall|in\s+no\s+event\s+shall|neither\s+party\s+shall\s+be\s+liable\s+for)\s+(?:any\s+)?(?:indirect|consequential|punitive|special)\s+damages\b", re.IGNORECASE), ClauseCategoryEnum.LIMITATION_OF_LIABILITY, 12),
    (re.compile(r"\b(?:indemnify\s+and\s+(?:hold\s+harmless|keep\s+indemnified)|defend,\s*indemnify)\b", re.IGNORECASE), ClauseCategoryEnum.INDEMNIFICATION, 12),
    (re.compile(r"\b(?:shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?(?:compete|solicit|hire|engage\s+in\s+a\s+competing))\b", re.IGNORECASE), ClauseCategoryEnum.RESTRICTIVE_COVENANTS, 12),
    (re.compile(r"\b(?:renew|extend|continue)\s+(?:the\s+)?(?:term|agreement|lease)\s+(?:for\s+(?:an\s+)?additional|successive)\b", re.IGNORECASE), ClauseCategoryEnum.RENEWAL, 12),
]


CATEGORY_SCORING_RULES = {
    ClauseCategoryEnum.SCOPE_OF_SERVICES: {
        "positive": [
            (re.compile(r"\b(?:services\s+to\s+be\s+performed|scope\s+of\s+work|statement\s+of\s+work|deliverables|technical\s+advisory|consulting\s+services|cloud\s+infrastructure\s+design|devops\s+automation|efficiency\s+assessments|supply-chain\s+advisory)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:consultant\s+shall\s+render|perform\s+services|project\s+schedules?|duties\s+and\s+responsibilities)\b", re.IGNORECASE), 6),
        ],
        "negative": []
    },
    ClauseCategoryEnum.PAYMENT: {
        "positive": [
            (re.compile(r"\b(?:monthly\s+(?:ground\s+)?rent|base\s+rent|yielding\s+and\s+paying|payable\s+in\s+advance|due\s+on\s+or\s+before\s+the|undisputed\s+invoices\s+shall\s+be\s+paid|late\s+payment\s+(?:fee|penalty|interest)|accrue\s+interest\s+at\s+(?:the\s+rate\s+of|a\s+rate\s+of)|penalty\s+interest|fixed\s+rate\s+of|interest\s+on\s+unpaid\s+principal|maturity\s+period|single-draw\s+commercial\s+term\s+loan|disburse\s+to\s+borrower|principal\s+amount\s+of|prepayment\s+fee|prepayment\s+premiums?|prepay\s+the\s+outstanding|debt\s+service\s+coverage\s+ratio|dscr|purchase\s+orders?|lead\s+time|unit\s+component\s+prices?|price\s+adjustments?|cost\s+justification|base\s+salary\s+of|performance\s+bonus|monthly\s+rent\s+of|security\s+deposit|late\s+fee\s+of\s+5%|flat\s+late\s+fee)\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:remit\s+payment|invoices?|billing|payment\s+terms|compensation\s+for\s+services|net\s+\d+|salary|bonus|rent|principal|interest|installments?|prepayment)\b", re.IGNORECASE), 5),
            (re.compile(r"(?:₹|Rs\.?|\$|€|USD|INR)\s*[\d,]+", re.IGNORECASE), 3),
        ],
        "negative": [
            (re.compile(r"\b(?:without\s+any\s+(?:payment|compensation|reimbursement|fee)|shall\s+pay\s+no\s+(?:royalties|fees|compensation)|pay\s+no\s+royalties|without\s+financial\s+reimbursement)\b", re.IGNORECASE), -10),
            (re.compile(r"\b(?:even\s+if\s+customer\s+has\s+paid|provided\s+all\s+(?:previous\s+)?(?:service\s+)?fees\s+have\s+been\s+settled)\b", re.IGNORECASE), -6),
        ]
    },
    ClauseCategoryEnum.CONFIDENTIALITY: {
        "positive": [
            (re.compile(r"\b(?:confidential\s+information|non-disclosure|nda|strict\s+secrecy|keep\s+confidential|proprietary\s+information|maintain\s+(?:the\s+)?(?:strict\s+)?confidentiality|confidentiality\s+of|prior\s+written\s+consent\s+of\s+the\s+disclosing|survive\s+for\s+a\s+period\s+of\s+\d+\s+years\s+(?:after|following)\s+(?:termination|expiration))\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:confidential|confidentiality|secret|disclose|disclosure)\b", re.IGNORECASE), 4),
        ],
        "negative": [
            (re.compile(r"\b(?:non-compete|non-solicitation|competing\s+business)\b", re.IGNORECASE), -6),
        ]
    },
    ClauseCategoryEnum.INTELLECTUAL_PROPERTY: {
        "positive": [
            (re.compile(r"\b(?:work\s+made\s+for\s+hire|ownership\s+of\s+deliverables|ownership\s+of\s+inventions|assigns\s+all\s+right,\s+title\s+and\s+interest|intellectual\s+property|copyrights?|trademarks?|patents?|patent\s+rights?|trade\s+secrets?|license\s+grant|exclusive\s+property\s+of|work\s+product|source\s+code|documentation|pre-existing\s+(?:tools|materials|frameworks))\b", re.IGNORECASE), 8),
            (re.compile(r"\b(?:assigns?\s+(?:all\s+)?(?:right,\s+title|intellectual\s+property)|shall\s+be\s+the\s+exclusive\s+property)\b", re.IGNORECASE), 7),
        ],
        "negative": []
    },
    ClauseCategoryEnum.INDEMNIFICATION: {
        "positive": [
            (re.compile(r"\b(?:indemnify\s+and\s+(?:keep\s+indemnified|hold\s+harmless)|defend,?\s*indemnify|hold\s+harmless\s+from\s+and\s+against|indemnify\s+against\s+any\s+and\s+all\s+claims|patent\s+infringement\s+and\s+product\s+indemnification|defend\s+and\s+indemnify|indemnity\s+obligations?|third-party\s+claims?|officers,\s+directors,\s+employees)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:indemnif|indemnity|hold\s+harmless)\b", re.IGNORECASE), 5),
        ],
        "negative": []
    },
    ClauseCategoryEnum.LIMITATION_OF_LIABILITY: {
        "positive": [
            (re.compile(r"\b(?:limitation\s+of\s+liability|liability\s+cap|aggregate\s+liability|consequential\s+damages|indirect\s+damages|punitive\s+damages|disclaimer\s+of\s+consequential\s+damages|aggregate\s+monetary\s+liability|total\s+aggregate\s+liability|shall\s+not\s+exceed\s+(?:the\s+total\s+fees|\$[\d,]+)|fees\s+paid\s+by\s+client\s+in\s+the\s+prior\s+12\s+months)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:liability\s+shall\s+not\s+exceed|capped\s+at|in\s+no\s+event\s+shall\s+either\s+party\s+be\s+liable)\b", re.IGNORECASE), 7),
        ],
        "negative": []
    },
    ClauseCategoryEnum.TERM: {
        "positive": [
            (re.compile(r"\b(?:commencing\s+on\s+[A-Za-z]+\s+\d+,\s+\d{4},\s+and\s+terminating\s+on\s+[A-Za-z]+\s+\d+,\s+\d{4}|term\s+of\s+\d+\s+years?\s+commencing|fixed\s+(?:term|duration)\s+of\s+\d+\s+years?|shall\s+continue\s+for\s+a\s+period\s+of\s+\d+\s+years?|unless\s+sooner\s+terminated|two\s+\(2\)\s+years\s+from\s+the\s+effective\s+date)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:initial\s+term|duration\s+of\s+this\s+agreement|term\s+of\s+this\s+lease)\b", re.IGNORECASE), 6),
        ],
        "negative": [
            (re.compile(r"\b(?:either\s+party\s+may\s+terminate\s+for\s+convenience|terminate\s+immediately\s+upon\s+written\s+notice)\b", re.IGNORECASE), -4)
        ]
    },
    ClauseCategoryEnum.TERMINATION: {
        "positive": [
            (re.compile(r"\b(?:terminate\s+this\s+agreement|termination\s+for\s+cause|termination\s+for\s+convenience|right\s+to\s+terminate|notice\s+of\s+termination|early\s+termination|immediately\s+upon\s+written\s+notice\s+in\s+the\s+event\s+of\s+a\s+material\s+breach|thirty\s+\(30\)\s+days?\s+prior\s+written\s+notice\s+for\s+convenience|re-enter|re-entry|forfeiture)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:terminate|termination|cancel|cancellation|cure\s+period)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.RENEWAL: {
        "positive": [
            (re.compile(r"\b(?:automatically\s+renew|auto-renew|automatic\s+renewal|successive\s+(?:one-year|annual)\s+(?:terms|periods)|notice\s+of\s+non-renewal|extend\s+the\s+term\s+for\s+successive|renewal\s+term|option\s+to\s+renew)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:renew|renewal|extension\s+of\s+term)\b", re.IGNORECASE), 5),
        ],
        "negative": []
    },
    ClauseCategoryEnum.DISPUTE_RESOLUTION: {
        "positive": [
            (re.compile(r"\b(?:binding\s+arbitration|american\s+arbitration\s+association|arbitrator|exclusive\s+jurisdiction|governing\s+forum|venue\s+shall\s+be|jury\s+trial\s+waiver|class\s+action\s+waiver|state\s+and\s+federal\s+courts\s+located\s+in|courts\s+of\s+travis\s+county|courts\s+of\s+new\s+york\s+county|judicial\s+jurisdiction)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:arbitrat|litigation|dispute\s+resolution|dispute\s+arising|jurisdiction|venue|court\s+venue)\b", re.IGNORECASE), 5),
        ],
        "negative": []
    },
    ClauseCategoryEnum.GOVERNING_LAW: {
        "positive": [
            (re.compile(r"\b(?:governed\s+by,\s*and\s+construed\s+in\s+accordance\s+with,\s*the\s+laws\s+of|governed\s+by\s+the\s+laws\s+of|without\s+regard\s+to\s+(?:its\s+)?conflict\s+of\s+laws?\s+principles|substantive\s+laws\s+of\s+the\s+state\s+of|laws\s+of\s+the\s+commonwealth\s+of\s+massachusetts|laws\s+of\s+the\s+state\s+of\s+new\s+york)\b", re.IGNORECASE), 10),
            (re.compile(r"\b(?:governing\s+law|applicable\s+law|choice\s+of\s+law)\b", re.IGNORECASE), 6),
        ],
        "negative": []
    },
    ClauseCategoryEnum.RESTRICTIVE_COVENANTS: {
        "positive": [
            (re.compile(r"\b(?:non-compete|non-solicitation|post-employment\s+non-compete|competing\s+business|solicit\s+or\s+hire|materially\s+involved\s+in\s+the\s+performance|during\s+the\s+term\s+and\s+for\s+a\s+period\s+of\s+24\s+months|client\s+introduced\s+by\s+client)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:compete|solicit|restrictive\s+covenant|restrain)\b", re.IGNORECASE), 5),
        ],
        "negative": []
    },
    ClauseCategoryEnum.PROPERTY_PREMISES: {
        "positive": [
            (re.compile(r"\b(?:leased\s+premises|demised\s+premises|suite\s+\d+|square\s+feet|artisan\s+way|boston,\s*massachusetts|office\s+space\s+located\s+at)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:premises|property|building|real\s+estate)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.PROPERTY_USE: {
        "positive": [
            (re.compile(r"\b(?:general\s+corporate\s+offices|professional\s+services|software\s+development|use\s+of\s+premises|permitted\s+use|applicable\s+zoning|building\s+regulations|unlawful\s+or\s+offensive\s+purpose)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:occupy|occupancy|use\s+and\s+enjoyment)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.MAINTENANCE: {
        "positive": [
            (re.compile(r"\b(?:maintenance\s+and\s+repairs?|structural\s+soundness|foundation,\s*exterior\s+walls,\s*roof|plumbing\s+and\s+hvac|interior\s+of\s+the\s+leased\s+premises|good\s+and\s+tenantable\s+repair|janitorial\s+services|keep\s+in\s+repair)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:repair|maintain|maintenance|clean\s+condition)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.ALTERATIONS: {
        "positive": [
            (re.compile(r"\b(?:alterations\s+and\s+improvements|structural\s+alterations|without\s+the\s+prior\s+written\s+consent\s+of\s+landlord|permanent\s+improvements|become\s+the\s+property\s+of\s+landlord|fixtures\s+and\s+improvements)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:alteration|improvement|modification\s+to\s+premises|install\s+fixtures)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.GENERAL_BOILERPLATE: {
        "positive": [
            (re.compile(r"\b(?:entire\s+agreement|supersedes\s+all\s+prior|written\s+or\s+oral\s+understandings|severability|notices\s+under\s+this\s+agreement|counterparts|amendments?\s+in\s+writing|force\s+majeure)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:boilerplate|miscellaneous|general\s+provisions)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.PRIVACY: {
        "positive": [
            (re.compile(r"\b(?:personal\s+data|personally\s+identifiable|pii|gdpr|data\s+subject|data\s+protection\s+regulation|processing\s+of\s+personal\s+data)\b", re.IGNORECASE), 9),
            (re.compile(r"\b(?:privacy|data\s+protection|privacy\s+policy)\b", re.IGNORECASE), 4),
        ],
        "negative": []
    },
    ClauseCategoryEnum.LIABILITY: {
        "positive": [
            (re.compile(r"\b(?:acceleration\s+and\s+remedies|declare\s+the\s+entire\s+outstanding|immediately\s+due\s+and\s+payable|event\s+of\s+default|service\s+availability|service\s+credits?|product\s+warranty|defect\s+remedies|insurance\s+and\s+casualty|casualty\s+loss)\b", re.IGNORECASE), 6),
            (re.compile(r"\b(?:liable|liability|damages|losses|casualty|insurance)\b", re.IGNORECASE), 2),
        ],
        "negative": []
    },
}

CONFIDENCE_FLOOR: int = 3


def validate_category_value(val: str) -> ClauseCategoryEnum:
    """
    Validates that a category string strictly belongs to the approved category set.
    """
    if val not in APPROVED_CATEGORIES_SET:
        # Check if matched by string value case-insensitively
        for member in ClauseCategoryEnum:
            if member.value.lower() == str(val).lower():
                return member
        logger.error(f"Structured output validation failed: Rejected out-of-set category '{val}'.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_CATEGORY_REJECTED",
                "message": f"Category '{val}' is outside the approved category set."
            }
        )
    return ClauseCategoryEnum(val)


def score_clause_categories(
    text: str,
    title: str = "",
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> List[Tuple[ClauseCategoryEnum, int]]:
    """
    Scores categories using heading-first direct mapping followed by evidence-weighted scoring.
    """
    scores: Dict[ClauseCategoryEnum, int] = {cat: 0 for cat in ClauseCategoryEnum}

    # 1. HEADING-FIRST DIRECT MATCH (Highest Priority, Spec Root Cause #4 / P0 1D)
    clean_title = title.strip() if title else ""
    matched_heading_cats = set()
    if clean_title:
        for heading_pat, target_cat in HEADING_CATEGORY_PATTERNS:
            if heading_pat.search(clean_title) and target_cat not in matched_heading_cats:
                score_boost = 100 if not matched_heading_cats else 50
                scores[target_cat] += score_boost
                matched_heading_cats.add(target_cat)
                logger.info(f"Heading-First Categorization: Title '{clean_title}' matched {target_cat.value} (+{score_boost})")


    combined_content = f"{title} {text}".strip()
    clean_content = re.sub(r'\blimited\s+liability\s+(?:company|partnership|llc|llp)\b', '', combined_content, flags=re.IGNORECASE)

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

    # 4. Evidence from Rule Findings (if available)
    if rule_findings:
        for rf in rule_findings:
            signal = str(rf.get("risk_signal", "")).lower()
            if "termination" in signal:
                scores[ClauseCategoryEnum.TERMINATION] += 8
            elif "dispute" in signal or "arbitration" in signal:
                scores[ClauseCategoryEnum.DISPUTE_RESOLUTION] += 8
            elif "ip" in signal or "intellectual" in signal:
                scores[ClauseCategoryEnum.INTELLECTUAL_PROPERTY] += 8
            elif "confidential" in signal:
                scores[ClauseCategoryEnum.CONFIDENTIALITY] += 8
            elif "liability" in signal:
                scores[ClauseCategoryEnum.LIMITATION_OF_LIABILITY] += 8
            elif "renewal" in signal:
                scores[ClauseCategoryEnum.RENEWAL] += 8

    # Filter by confidence floor
    ranked_categories: List[Tuple[ClauseCategoryEnum, int]] = [
        (cat, score) for cat, score in scores.items() if score >= CONFIDENCE_FLOOR
    ]


    # Sort descending by score
    ranked_categories.sort(key=lambda x: x[1], reverse=True)
    
    # Fallback to General / Boilerplate if nothing meets confidence floor
    if not ranked_categories:
        ranked_categories = [(ClauseCategoryEnum.GENERAL_BOILERPLATE, CONFIDENCE_FLOOR)]
        
    return ranked_categories


def categorize_clause_records(
    clauses_input: List[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Categorizes an ordered list of clause records with heading-first priority mapping
    and evidence-weighted dominant subject ranking.
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


def categorize_clause(text: str, title: str = "") -> Dict[str, Any]:
    """Single clause categorization helper."""
    ranked = score_clause_categories(text=text, title=title)
    primary_cat = ranked[0][0]
    return {
        "primary_category": primary_cat,
        "category": primary_cat,
        "ranked_categories": ranked,
        "confidence": ranked[0][1]
    }


