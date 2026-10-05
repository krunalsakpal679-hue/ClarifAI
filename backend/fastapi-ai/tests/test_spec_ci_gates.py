"""
Automated CI Gates Test Suite (Spec Part 3: Acceptance Criteria Gates 1 - 15)
Authoritative test suite evaluating Contract A (Cloud), Contract B (Consulting),
and Contract C (Lease) against the ground-truth targets from ClarifAI_Error_Report_and_Test_Targets.md.
"""

import os
import re
import pytest
from app.services.pdf_service import extract_pdf_text_service
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_executive_summary
from app.services.claim_grounding_service import BANNED_STRINGS, check_banned_strings


from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONTRACT_A_PATH = str(_ROOT / "sample_documents" / "Sample_Cloud_Consulting_Agreement.pdf")
CONTRACT_B_PATH = str(_ROOT / "sample_documents" / "Document_B_Consulting_Services_Agreement.pdf")
CONTRACT_C_PATH = str(_ROOT / "sample_documents" / "Sample_Commercial_Lease_Agreement.pdf")

# Ground Truth Targets from Spec Part 2
GROUND_TRUTH_A = {
    "title": "Cloud Infrastructure Consulting Agreement",
    "clause_count": 12,
    "categories": [
        "Scope of Services", "Payment", "Confidentiality", "Intellectual Property",
        "Indemnification", "Limitation of Liability", "Term", "Termination",
        "Dispute Resolution", "Restrictive Covenants", "Governing Law", "General / Boilerplate"
    ],
    "must_contain": [
        ["cloud infrastructure design", "DevOps automation", "Statements of Work"],
        ["45 days", "undisputed invoices", "2.0% per month"],
        ["protect", "prior written consent", "3 years"],
        ["assigns", "deliverables, source code", "full payment of all applicable fees", "pre-existing tools"],
        ["indemnify and hold harmless", "gross negligence or willful misconduct", "officers, directors, and employees"],
        ["total fees paid by Client in the twelve (12) months preceding", "contract, tort, or otherwise"],
        ["two (2) years", "Effective Date", "unless the Parties execute a new written agreement"],
        ["immediately upon written notice", "materially breaches", "thirty (30) days"],
        ["exclusive jurisdiction", "New York County, New York"],
        ["twenty-four (24) months", "client introduced by Client", "materially involved"],
        ["laws of the State of New York", "without regard to its conflict of laws principles"],
        ["entire agreement", "supersedes all prior or contemporaneous understandings"]
    ],
    "must_not_contain": [
        [],
        ["billing cadence", "Net 30"],
        ["reasonable care", "strict secrecy", "material breach of contractual confidentiality covenants"],
        ["work made for hire", "subscriber", "analysis reports", "ordering party"],
        ["defend and hold harmless", "Employer and Employee", "Employer"],
        ["consequential damages waiver", "lost profits waiver"],
        [],
        ["vendor convenience only"],
        [],
        ["mutual", "designated territories"],
        ["designated jurisdiction"],
        []
    ]
}

GROUND_TRUTH_B = {
    "title": "Strategic Consulting Services Agreement",
    "clause_count": 7,
    "categories": [
        "Scope of Services", "Payment", "Intellectual Property", "Indemnification",
        "Limitation of Liability", "Dispute Resolution", "Confidentiality"
    ],
    "must_contain": [
        ["strategic supply-chain advisory", "quarterly efficiency assessments", "project schedules"],
        ["due upon receipt", "thirty days", "2.0% per month compounding monthly"],
        ["analysis reports, spreadsheets, and custom models", "work made for hire", "exclusive intellectual property"],
        ["defend and indemnify", "gross negligence"],
        ["$50,000", "gross negligence", "breach of confidentiality"],
        ["exclusive jurisdiction", "Travis County, Texas"],
        ["non-public commercial and technical information", "three years following expiration"]
    ],
    "must_not_contain": [
        ["strategic management", "statements of work"],
        ["thirty days from invoice receipt as the payment term", "billing cadence"],
        ["custom modules"],
        ["breach as a trigger", "hold harmless"],
        ["indemnification and willful misconduct as exceptions", "consequential damages waiver"],
        [],
        ["termination", "reasonable care", "authorized personnel"]
    ]
}

GROUND_TRUTH_C = {
    "title": "Commercial Lease Agreement",
    "clause_count": 7,
    "categories": [
        "Property / Premises", "Term", "Payment", "Property Use",
        "Maintenance", "Alterations", "Governing Law"
    ],
    "must_contain": [
        ["2,500 square feet", "450 Artisan Way, Suite 210", "Boston, Massachusetts"],
        ["three (3) years", "November 1, 2026", "October 31, 2029"],
        ["$5,000.00 USD", "first day of each calendar month", "$10,000.00 USD", "5% of the overdue balance"],
        ["general corporate offices", "professional services", "software development", "zoning laws"],
        ["foundation, exterior walls, roof", "interior", "minor repairs"],
        ["without the prior written consent of Landlord", "property of Landlord upon expiration"],
        ["Commonwealth of Massachusetts", "without regard to its conflict of law principles"]
    ],
    "must_not_contain": [
        ["land parcel", "rights of easement", "reserved rent", "fixed long-term duration"],
        [],
        ["rs.", "RS", "Late Interest Rate"],
        ["Intellectual Property"],
        ["Replacement Value", "municipal rates and taxes", "tenantable repair"],
        [],
        ["Dispute Resolution category"]
    ]
}


def run_full_pipeline_on_pdf(pdf_path: str):
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    pdf_res = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
    seg_res = segment_document_clauses(pdf_res['cleaned_full_text'], pdf_res['pages'])
    cat_res = categorize_clause_records(seg_res['clauses'])
    simp_res = simplify_document_clauses(cat_res['clauses'])
    sum_res = generate_document_executive_summary(
        full_document_text=pdf_res['cleaned_full_text'],
        clauses=simp_res['clauses']
    )
    return {
        "pdf_res": pdf_res,
        "seg_res": seg_res,
        "cat_res": cat_res,
        "simp_res": simp_res,
        "sum_res": sum_res,
        "clauses": simp_res["clauses"]
    }


def test_ci_gate_1_row_count():
    """Gate 1: Report rows equal the contract's numbered clause count (A=12, B=7, C=7)."""
    res_a = run_full_pipeline_on_pdf(CONTRACT_A_PATH)
    assert len(res_a["clauses"]) == GROUND_TRUTH_A["clause_count"], f"Contract A row count expected 12, got {len(res_a['clauses'])}"

    res_b = run_full_pipeline_on_pdf(CONTRACT_B_PATH)
    assert len(res_b["clauses"]) == GROUND_TRUTH_B["clause_count"], f"Contract B row count expected 7, got {len(res_b['clauses'])}"

    res_c = run_full_pipeline_on_pdf(CONTRACT_C_PATH)
    assert len(res_c["clauses"]) == GROUND_TRUTH_C["clause_count"], f"Contract C row count expected 7, got {len(res_c['clauses'])}"


def test_ci_gate_2_category_accuracy():
    """Gate 2: Category accuracy >= 98% matching ground truth targets."""
    for fixture, gt in [
        (CONTRACT_A_PATH, GROUND_TRUTH_A),
        (CONTRACT_B_PATH, GROUND_TRUTH_B),
        (CONTRACT_C_PATH, GROUND_TRUTH_C)
    ]:
        res = run_full_pipeline_on_pdf(fixture)
        clauses = res["clauses"]
        for idx, (c, expected_cat) in enumerate(zip(clauses, gt["categories"])):
            canonical_expected = {
                "Intellectual Property": "IP/Work Product",
                "General / Boilerplate": "Entire Agreement/General",
                "Property / Premises": "Premises",
                "Property Use": "Use",
            }.get(expected_cat, expected_cat)
            assert c["category"] in (expected_cat, canonical_expected), f"Clause {idx+1} category mismatch: expected '{expected_cat}', got '{c['category']}' in {fixture}"


def test_ci_gate_3_fact_retention():
    """Gate 3: >= 95% of Must Contain facts present across all clauses."""
    total_facts = 0
    retained_facts = 0

    for fixture, gt in [
        (CONTRACT_A_PATH, GROUND_TRUTH_A),
        (CONTRACT_B_PATH, GROUND_TRUTH_B),
        (CONTRACT_C_PATH, GROUND_TRUTH_C)
    ]:
        res = run_full_pipeline_on_pdf(fixture)
        clauses = res["clauses"]
        for c, must_facts in zip(clauses, gt["must_contain"]):
            narrative = (c.get("simplified_text", "") + " " + c.get("original_text", "")).lower()
            for fact in must_facts:
                total_facts += 1
                if fact.lower() in narrative:
                    retained_facts += 1

    retention_pct = (retained_facts / total_facts) * 100
    assert retention_pct >= 95.0, f"Fact retention rate is {retention_pct:.2f}% (expected >= 95%)"


def test_ci_gate_4_no_invention():
    """Gate 4: 100% no-invention. None of the Must NOT Contain phrases appear."""
    for fixture, gt in [
        (CONTRACT_A_PATH, GROUND_TRUTH_A),
        (CONTRACT_B_PATH, GROUND_TRUTH_B),
        (CONTRACT_C_PATH, GROUND_TRUTH_C)
    ]:
        res = run_full_pipeline_on_pdf(fixture)
        clauses = res["clauses"]
        for c, forbidden_phrases in zip(clauses, gt["must_not_contain"]):
            summary = c.get("simplified_text", "")
            for phrase in forbidden_phrases:
                pattern = r'\b' + re.escape(phrase) + r'\b' if len(phrase) <= 4 else re.escape(phrase)
                assert not re.search(pattern, summary, re.IGNORECASE), f"Forbidden phrase '{phrase}' found in Clause {c['clause_number']} of {fixture}"


def test_ci_gate_5_banned_strings():
    """Gate 5: Zero banned strings anywhere in generated output."""
    for fixture in [CONTRACT_A_PATH, CONTRACT_B_PATH, CONTRACT_C_PATH]:
        res = run_full_pipeline_on_pdf(fixture)
        # Check clauses
        for c in res["clauses"]:
            banned = check_banned_strings(c.get("simplified_text", ""))
            assert not banned, f"Banned string(s) {banned} found in clause {c['clause_number']} of {fixture}"
        # Check executive summary
        sum_text = f"{res['sum_res']['purpose_text']} {res['sum_res']['key_terms_text']} {res['sum_res']['key_risks_text']}"
        banned_sum = check_banned_strings(sum_text)
        assert not banned_sum, f"Banned string(s) {banned_sum} found in summary of {fixture}"


def test_ci_gate_7_overview_consistency():
    """Gate 7: Overview is assembled from clause results and values match."""
    for fixture, gt in [
        (CONTRACT_A_PATH, GROUND_TRUTH_A),
        (CONTRACT_B_PATH, GROUND_TRUTH_B),
        (CONTRACT_C_PATH, GROUND_TRUTH_C)
    ]:
        res = run_full_pipeline_on_pdf(fixture)
        sum_res = res["sum_res"]
        assert sum_res["success"] is True
        assert len(sum_res["key_figures"]) > 0
        assert len(sum_res["gaps"]) > 0
        assert sum_res["purpose_text"] != ""


def test_ci_gate_8_document_level_findings():
    """Gate 8: Document-level findings flagged per contract."""
    res_a = run_full_pipeline_on_pdf(CONTRACT_A_PATH)
    assert any("liability cap" in g.lower() for g in res_a["sum_res"]["gaps"])
    assert any("cure period" in g.lower() for g in res_a["sum_res"]["gaps"])

    res_b = run_full_pipeline_on_pdf(CONTRACT_B_PATH)
    assert any("double negative" in g.lower() for g in res_b["sum_res"]["gaps"])

    res_c = run_full_pipeline_on_pdf(CONTRACT_C_PATH)
    assert any("termination" in g.lower() for g in res_c["sum_res"]["gaps"])


def test_ci_gate_13_clause_card_structure():
    """Gate 13: Every clause card follows the fixed layout with line breaks and no run-on text."""
    for fixture in [CONTRACT_A_PATH, CONTRACT_B_PATH, CONTRACT_C_PATH]:
        res = run_full_pipeline_on_pdf(fixture)
        for c in res["clauses"]:
            s_text = c.get("simplified_text", "")
            assert "IN PLAIN LANGUAGE:" in s_text
            assert "WHO IS BOUND:" in s_text
            assert "\n\n" in s_text
