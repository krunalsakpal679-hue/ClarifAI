"""
Unit Tests for Workstream 3 (W3): Expanded Category Taxonomy & Heading-First Categorization
"""

import pytest
from app.models.clause_categorization import ClauseCategoryEnum
from app.services.clause_categorization_service import (
    score_clause_categories,
    categorize_clause
)


def test_w3_heading_first_all_categories():
    test_headings = [
        ("SERVICES", ClauseCategoryEnum.SCOPE_OF_SERVICES),
        ("FEES AND PAYMENT", ClauseCategoryEnum.PAYMENT),
        ("CONFIDENTIALITY COVENANT", ClauseCategoryEnum.CONFIDENTIALITY),
        ("WORK PRODUCT OWNERSHIP", ClauseCategoryEnum.INTELLECTUAL_PROPERTY),
        ("INDEMNITY OBLIGATIONS", ClauseCategoryEnum.INDEMNIFICATION),
        ("LIMITATION OF LIABILITY", ClauseCategoryEnum.LIMITATION_OF_LIABILITY),
        ("TERM", ClauseCategoryEnum.TERM),
        ("TERMINATION FOR CONVENIENCE AND SUSPENSION", ClauseCategoryEnum.TERMINATION),
        ("AUTOMATIC RENEWAL", ClauseCategoryEnum.RENEWAL),
        ("DISPUTE RESOLUTION", ClauseCategoryEnum.DISPUTE_RESOLUTION),
        ("GOVERNING LAW", ClauseCategoryEnum.GOVERNING_LAW),
        ("RESTRICTIVE COVENANTS", ClauseCategoryEnum.RESTRICTIVE_COVENANTS),
        ("LEASED PREMISES", ClauseCategoryEnum.PROPERTY_PREMISES),
        ("USE OF PREMISES", ClauseCategoryEnum.PROPERTY_USE),
        ("MAINTENANCE AND REPAIRS", ClauseCategoryEnum.MAINTENANCE),
        ("ALTERATIONS AND IMPROVEMENTS", ClauseCategoryEnum.ALTERATIONS),
        ("PRODUCT WARRANTY AND REMEDIES", ClauseCategoryEnum.WARRANTY),
        ("INSURANCE AND CASUALTY", ClauseCategoryEnum.INSURANCE),
        ("FORCE MAJEURE", ClauseCategoryEnum.FORCE_MAJEURE),
        ("ASSIGNMENT AND DELEGATION", ClauseCategoryEnum.ASSIGNMENT),
        ("NOTICES", ClauseCategoryEnum.NOTICES),
        ("ENTIRE AGREEMENT", ClauseCategoryEnum.GENERAL_BOILERPLATE),
        ("DATA PRIVACY", ClauseCategoryEnum.PRIVACY),
    ]

    for heading, expected_enum in test_headings:
        res = categorize_clause(text="Standard operational text.", title=heading)
        assert res["primary_category"] == expected_enum, f"Heading '{heading}' failed to categorize as {expected_enum.value} (got {res['primary_category'].value})"


def test_w3_multi_topic_heading():
    title = "GOVERNING JURISDICTION AND BINDING ARBITRATION"
    text = "This Agreement shall be governed by Delaware law and controversies submitted to AAA binding arbitration."
    ranked = score_clause_categories(text=text, title=title)
    ranked_enums = [cat for cat, _ in ranked]
    assert ClauseCategoryEnum.GOVERNING_LAW in ranked_enums
    assert ClauseCategoryEnum.DISPUTE_RESOLUTION in ranked_enums
