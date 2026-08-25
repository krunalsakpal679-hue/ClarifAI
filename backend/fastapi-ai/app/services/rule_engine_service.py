"""
ClarifAI Legal Risk Rule Engine Service Module
Implements all 14 approved rules (R001–R014) per Chapter 16.7.
Produces structured evidence findings without assigning any final severity value per Chapter 16.10.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from app.models.rule_engine import RULE_SET_VERSION, RuleFinding

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Definitions for exactly 14 approved rules R001-R014 (Chapter 16.7)
RULES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "R001": {
        "risk_signal": "Auto-Renewal",
        "pattern": re.compile(r"\b(?:auto(?:matically)?\s*renew(?:s|ed|ing)?|renew(?:s|ed|ing)?\s+automatically|automatic(?:ally)?\s+extension)\b", re.IGNORECASE)
    },
    "R002": {
        "risk_signal": "Early-Termination Penalty",
        "pattern": re.compile(r"\b(?:early\s+termination\s+(?:fee|penalty|charge)|early\s+cancellation\s+(?:fee|penalty)|liquidated\s+damages\s+for\s+early\s+termination)\b", re.IGNORECASE)
    },
    "R003": {
        "risk_signal": "Hidden/Add-on Charges",
        "pattern": re.compile(r"\b(?:hidden\s+fee|additional\s+charge|unspecified\s+fee|maintenance\s+surcharge|administrative\s+fee|processing\s+surcharge)\b", re.IGNORECASE)
    },
    "R004": {
        "risk_signal": "Late-Payment Penalty",
        "pattern": re.compile(r"\b(?:late\s+payment\s+(?:fee|penalty|interest)|interest\s+rate\s+of\s+[0-9]+(?:\.[0-9]+)?%\s*per\s+month|late\s+charge)\b", re.IGNORECASE)
    },
    "R005": {
        "risk_signal": "Excessive Liability Transfer",
        "pattern": re.compile(r"\b(?:disclaim(?:s|er)?\s+all\s+liability|no\s+liability\s+whatsoever|liability\s+whatsoever|entire\s+risk|user\s+assumes\s+all\s+risk|liability\s+exceeds?\s+\$0)\b", re.IGNORECASE)
    },
    "R006": {
        "risk_signal": "Broad Indemnification",
        "pattern": re.compile(r"\b(?:indemnify\s+and\s+hold\s+harmless|defend\s+and\s+indemnify|indemnify\s+against\s+any\s+and\s+all\s+claims)\b", re.IGNORECASE)
    },
    "R007": {
        "risk_signal": "Unilateral Modification",
        "pattern": re.compile(r"\b(?:reserve(?:s)?\s+the\s+right\s+to\s+modify|change\s+these\s+terms\s+at\s+any\s+time|without\s+prior\s+notice|in\s+its\s+sole\s+discretion)\b", re.IGNORECASE)
    },
    "R008": {
        "risk_signal": "Unfavorable Termination",
        "pattern": re.compile(r"\b(?:terminate\s+at\s+any\s+time\s+without\s+cause|immediate\s+termination\s+without\s+notice|terminate\s+for\s+convenience)\b", re.IGNORECASE)
    },
    "R009": {
        "risk_signal": "Unusual Notice Requirement",
        "pattern": re.compile(r"\b(?:written\s+notice\s+of\s+at\s+least\s+(?:60|90|120)\s+days|notice\s+period\s+exceeding\s+60\s+days)\b", re.IGNORECASE)
    },
    "R010": {
        "risk_signal": "Restrictive Confidentiality",
        "pattern": re.compile(r"\b(?:confidentiality\s+obligation\s+shall\s+survive\s+indefinitely|perpetual\s+confidentiality|strict\s+secrecy\s+forever)\b", re.IGNORECASE)
    },
    "R011": {
        "risk_signal": "Broad IP Transfer",
        "pattern": re.compile(r"\b(?:assigns\s+all\s+right,\s+title,\s+and\s+interest|work\s+made\s+for\s+hire|transfer\s+all\s+intellectual\s+property|irrevocable\s+assignment)\b", re.IGNORECASE)
    },
    "R012": {
        "risk_signal": "Arbitration/Dispute Restriction",
        "pattern": re.compile(r"\b(?:binding\s+arbitration|waive\s+(?:the\s+)?right\s+to\s+a\s+jury\s+trial|class\s+action\s+waiver|exclusive\s+jurisdiction\s+in)\b", re.IGNORECASE)
    },
    "R013": {
        "risk_signal": "Data/Privacy Obligation",
        "pattern": re.compile(r"\b(?:share\s+data\s+with\s+third-party\s+advertisers|sell\s+personal\s+information|process\s+unrestricted\s+data)\b", re.IGNORECASE)
    },
    "R014": {
        "risk_signal": "Restrictive Employment/Business Obligation",
        "pattern": re.compile(r"\b(?:non-compete|non-solicitation|shall\s+not\s+engage\s+in\s+competing\s+business|restrictive\s+covenant)\b", re.IGNORECASE)
    },
}


def _extract_evidence_span(text: str, match_start: int, match_end: int, window: int = 60) -> str:
    """
    Extracts a supporting contextual evidence text span surrounding a match.
    """
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
    Evaluates all 14 rules (R001-R014) against input clauses or text.
    Produces structured evidence findings without assigning any final severity value per Chapter 16.10.

    Args:
        clauses: List of clause dicts.
        text: Raw or cleaned document text.

    Returns:
        Dict containing findings list, total_findings, rule_set_version, and schema_version.
    """
    findings: List[Dict[str, Any]] = []

    # Build target evaluation items (clause blocks or full text)
    evaluation_items: List[Dict[str, Any]] = []
    if clauses:
        for idx, clause_item in enumerate(clauses, start=1):
            c_id = str(clause_item.get("clause_id") or clause_item.get("position") or idx)
            c_text = clause_item.get("text", "")
            evaluation_items.append({"clause_id": c_id, "text": c_text})
    elif text:
        evaluation_items.append({"clause_id": "1", "text": text})

    for item in evaluation_items:
        item_text = item["text"]
        c_id = item["clause_id"]

        if not item_text or not item_text.strip():
            continue

        for rule_id, rule_def in RULES_REGISTRY.items():
            pattern = rule_def["pattern"]
            risk_signal = rule_def["risk_signal"]

            for match in pattern.finditer(item_text):
                matched_span = match.group(0)
                evidence = _extract_evidence_span(item_text, match.start(), match.end())

                finding_dict = {
                    "rule_id": rule_id,
                    "risk_signal": risk_signal,
                    "matched_text": matched_span,
                    "clause_id": c_id,
                    "evidence": evidence,
                    "rule_version": RULE_SET_VERSION,
                    "match_status": "MATCH"
                }
                findings.append(finding_dict)

    logger.info(f"Rule Engine Execution Complete: {len(findings)} rule findings generated across {len(RULES_REGISTRY)} rules.")

    return {
        "success": True,
        "total_findings": len(findings),
        "findings": findings,
        "rule_set_version": RULE_SET_VERSION,
        "schema_version": SCHEMA_VERSION
    }
