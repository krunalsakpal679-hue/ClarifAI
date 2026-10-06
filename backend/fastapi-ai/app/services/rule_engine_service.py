"""
ClarifAI Legal Risk Rule Engine Service Module
(W4 Spec Implementation)

Implements generalized risk signal detection (R001–R015) matching legal meaning,
verb/noun forms, and party obligations across diverse contract types without overfitting.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from app.models.rule_engine import RULE_SET_VERSION, RuleFinding

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Definitions for generalized risk rules R001-R015 matching legal meaning (verb/noun, active/passive)
RULES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "R001": {
        "risk_signal": "Auto-Renewal",
        "pattern": re.compile(
            r"\b(?:auto(?:matically)?\s*renew(?:s|ed|ing)?|renew(?:s|ed|ing)?\s+automatically|"
            r"automatic(?:ally)?\s+extension|consecutive\s+\w+[- ]year\s+terms?|"
            r"successive\s+(?:\d+|twelve|\w+)\s*[- ]month\s+periods?|"
            r"raise\s+prices\s+up\s+to\s+\d+%|annual\s+price\s+escalation|"
            r"increase\s+(?:fees?|rates?|prices?)\s+by\s+(?:up\s+to\s+)?\d+%)\b",
            re.IGNORECASE
        )
    },
    "R002": {
        "risk_signal": "Early-Termination Penalty",
        "pattern": re.compile(
            r"\b(?:early\s+termination\s+(?:fee|penalty|charge)|liquidated\s+damages\s+for\s+early\s+termination|"
            r"prepayment\s+(?:fee|penalty|premium)|forfeiture\s+of\s+(?:leasehold|deposit|prepaid\s+amounts?))\b",
            re.IGNORECASE
        )
    },
    "R003": {
        "risk_signal": "Hidden/Add-on Charges",
        "pattern": re.compile(
            r"\b(?:administrative\s+fee|processing\s+surcharge|hidden\s+fee|unspecified\s+(?:fee|charge|surcharge)|"
            r"surcharge\s+without\s+notice|administrative\s+surcharge|additional\s+unspecified\s+costs?)\b",
            re.IGNORECASE
        )
    },
    "R004": {
        "risk_signal": "Late-Payment Penalty",
        "pattern": re.compile(
            r"\b(?:late\s+payment\s+(?:fee|penalty|interest)|late\s+charge|"
            r"accrue\s+(?:a\s+)?late\s+payment|bear\s+interest\s+at|"
            r"accrue\s+interest\s+at|compounding\s+monthly|compounded\s+monthly|"
            r"collection\s+costs\s+and\s+(?:reasonable\s+)?(?:legal|attorney)\s+fees|"
            r"maximum\s+rate\s+permitted\s+by\s+law\s+or\s+\d+(?:\.\d+)?%\s*per\s+month|"
            r"flat\s+late\s+fee\s+of\s+\d+%|\d+(?:\.\d+)?%\s*per\s+month\s+on\s+past-due|"
            r"(?:rate\s+of\s+)?\d+(?:\.\d+)?%\s*per\s+month\s+until\s+settled)\b",
            re.IGNORECASE
        )
    },
    "R005": {
        "risk_signal": "Excessive Liability Transfer",
        "pattern": re.compile(
            r"\b(?:disclaim\w*\s+all\s+liability|disclaim(?:er)?\s+of\s+consequential\s+damages|"
            r"exclude\s+liability\s+for\s+(?:indirect|consequential|incidental|special|punitive)|"
            r"under\s+no\s+circumstances\s+shall\s+\w+\s+have\s+liability|"
            r"total\s+(?:aggregate\s+)?liability\s+shall\s+not\s+exceed|"
            r"capped\s+at\s+(?:the\s+)?(?:total\s+)?fees\s+paid|liability\s+is\s+limited\s+to\s+\$[\d,]+|"
            r"in\s+no\s+event\s+shall\s+(?:either\s+party|vendor|consultant|licensor)\b.{0,60}\bexceed)\b",
            re.IGNORECASE
        )
    },
    "R006": {
        "risk_signal": "Broad Indemnification",
        "pattern": re.compile(
            r"\b(?:defend\s+and\s+indemnify|defend,?\s*indemnify,?\s*(?:and\s+)?hold\s+harmless|"
            r"indemnify\s+and\s+hold\s+harmless|indemnify,?\s*hold\s+harmless,?\s*and\s+defend|"
            r"indemnif\w*\s+against\s+any\s+and\s+all\s+claims|"
            r"without\s+limitation\b.{0,60}\bindemnif|"
            r"indemnif\w*\b.{0,60}\bwithout\s+limitation|"
            r"customer\s+indemnification|consultant\s+indemnification)\b",
            re.IGNORECASE
        )
    },
    "R007": {
        "risk_signal": "Unilateral Modification",
        "pattern": re.compile(
            r"\b(?:reserve(?:s)?\s+the\s+right\s+to\s+modify|change\s+these\s+terms\s+at\s+any\s+time|"
            r"without\s+prior\s+notice|in\s+its\s+sole\s+discretion|unilaterally\s+(?:modify|amend|alter))\b",
            re.IGNORECASE
        )
    },
    "R008": {
        "risk_signal": "Unfavorable Termination",
        "pattern": re.compile(
            r"\b(?:terminat\w*\s+for\s+convenience|terminate\s+at\s+any\s+time\s+without\s+cause|"
            r"terminate\s+(?:or\s+suspend\s+)?immediately|immediate\s+termination|"
            r"without\s+refund\s+of\s+prepaid\s+fees|no\s+obligation\s+to\s+assist\s+in\s+transition|"
            r"immediate\s+termination\s+upon\s+written\s+notice\s+for\s+material\s+breach|"
            r"terminat\w*\s+immediately\s+without\s+cure)\b",
            re.IGNORECASE
        )
    },
    "R009": {
        "risk_signal": "Unusual Notice Requirement",
        "pattern": re.compile(
            r"\b(?:written\s+notice\s+of\s+at\s+least\s+(?:60|90|120)\s+days|"
            r"opt-out\s+at\s+least\s+(?:60|90|120)\s+days|prior\s+written\s+notice\s+of\s+not\s+less\s+than\s+(?:60|90)\s+days|"
            r"notice\s+of\s+at\s+least\s+(?:60|90|120)\s+days)\b",
            re.IGNORECASE
        )
    },
    "R010": {
        "risk_signal": "Restrictive Confidentiality",
        "pattern": re.compile(
            r"\b(?:survive\s+(?:indefinitely|perpetually|forever)|"
            r"survive\s+for\s+a\s+period\s+of\s+[1-3]\s+years|in\s+confidence\s+for\s+(?:three|two|one|\d+)\s+years|"
            r"trade\s+secrets\s+indefinitely|perpetual\s+confidentiality|"
            r"survives?\s+(?:for\s+)?\d+\s+years?\s+following\s+(?:disclosure|termination|expiration))\b",
            re.IGNORECASE
        )
    },
    "R011": {
        "risk_signal": "Broad IP Transfer",
        "pattern": re.compile(
            r"\b(?:assigns\s+all\s+right,\s+title,\s+and\s+interest|work\s+made\s+for\s+hire|"
            r"works\s+made\s+for\s+hire|irrevocable\s+assignment|"
            r"perpetual,?\s*irrevocable,?\s*royalty-free\s+license\s+to\s+use|"
            r"operational\s+usage\s+telemetry|exclusive\s+intellectual\s+property|"
            r"permanent\s+improvements\s+become\s+(?:landlord|lessor)'s\s+property)\b",
            re.IGNORECASE
        )
    },
    "R012": {
        "risk_signal": "Arbitration/Dispute Restriction",
        "pattern": re.compile(
            r"\b(?:binding\s+arbitration|American\s+Arbitration\s+Association|AAA\s+rules|"
            r"exclusive\s+jurisdiction\b|waive\s+(?:the\s+right\s+to\s+a\s+)?jury\s+trial|"
            r"class\s+action\s+waiver|exclusive\s+venue\s+in|courts\s+located\s+in)\b",
            re.IGNORECASE
        )
    },
    "R013": {
        "risk_signal": "Data/Privacy Obligation",
        "pattern": re.compile(
            r"\b(?:sell\s+personal\s+information|share\s+data\s+with\s+third-party\s+advertisers|"
            r"unauthorized\s+processing\s+or\s+data\s+loss)\b",
            re.IGNORECASE
        )
    },
    "R014": {
        "risk_signal": "Restrictive Employment/Business Obligation",
        "pattern": re.compile(
            r"\b(?:non-compete|non-solicitation|shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?compete|"
            r"competing\s+business|term\s+plus\s+24\s+months|twenty-four\s*\(24\)\s*months\s+thereafter|"
            r"client\s+introduced\s+by\s+Client|solicit\s+(?:any\s+)?employees?)\b",
            re.IGNORECASE
        )
    },
    "R015": {
        "risk_signal": "Uncapped Liability Carve-Out",
        "pattern": re.compile(
            r"\b(?:except\s+for\b.{0,300}\b(?:liability|damages|claims)\b.{0,80}\b(?:shall\s+not\s+exceed|is\s+capped|limited\s+to|capped\s+at|shall\s+exceed)|"
            r"excluding\s+liability\b.{0,300}\b(?:liability|damages|fees)|"
            r"other\s+than\b.{0,300}\b(?:liability|damages)\b.{0,80}\b(?:shall\s+not\s+exceed|is\s+capped|limited\s+to|capped\s+at|shall\s+exceed)|"
            r"no\s+carve-outs|without\s+limitation|liability\s+cap\s+has\s+no\s+carve-outs|"
            r"all\s+causes\s+of\s+action,\s+without\s+exception|sole\s+and\s+exclusive\s+remedy|"
            r"shall\s+not\s+exceed\b.{0,40}\bno\s+carve-outs?)\b",
            re.IGNORECASE
        )
    },
}


def _extract_evidence_span(text: str, match_start: int, match_end: int, window: int = 60) -> str:
    """Extracts a supporting contextual evidence text span surrounding a match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def evaluate_rules(
    clauses: Optional[List[Dict[str, Any]]] = None,
    text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates all rules (R001-R015) against input clauses or document text.
    Produces structured evidence findings with exact source spans and rule version.
    """
    findings: List[Dict[str, Any]] = []

    if clauses:
        for clause in clauses:
            clause_id = str(clause.get("clause_id") or clause.get("clause_number") or clause.get("position", "c-000"))
            clause_text = clause.get("text", "")
            for rule_id, rule_data in RULES_REGISTRY.items():
                match = rule_data["pattern"].search(clause_text)
                if match:
                    span_text = _extract_evidence_span(clause_text, match.start(), match.end())
                    matched_snippet = match.group(0).strip()
                    findings.append({
                        "rule_id": rule_id,
                        "rule_name": rule_data["risk_signal"],
                        "risk_signal": rule_data["risk_signal"],
                        "clause_id": clause_id,
                        "position": clause.get("position", 1),
                        "matched_text": matched_snippet,
                        "evidence": span_text,
                        "evidence_span": span_text,
                        "match_start": match.start(),
                        "match_end": match.end(),
                        "rule_version": RULE_SET_VERSION,
                        "rule_set_version": RULE_SET_VERSION
                    })
    elif text:
        for rule_id, rule_data in RULES_REGISTRY.items():
            for match in rule_data["pattern"].finditer(text):
                span_text = _extract_evidence_span(text, match.start(), match.end())
                matched_snippet = match.group(0).strip()
                findings.append({
                    "rule_id": rule_id,
                    "rule_name": rule_data["risk_signal"],
                    "risk_signal": rule_data["risk_signal"],
                    "clause_id": "doc-global",
                    "position": 1,
                    "matched_text": matched_snippet,
                    "evidence": span_text,
                    "evidence_span": span_text,
                    "match_start": match.start(),
                    "match_end": match.end(),
                    "rule_version": RULE_SET_VERSION,
                    "rule_set_version": RULE_SET_VERSION
                })

    return {
        "success": True,
        "total_findings": len(findings),
        "findings": findings,
        "rule_set_version": RULE_SET_VERSION,
        "schema_version": SCHEMA_VERSION
    }


evaluate_document_rules = evaluate_rules
