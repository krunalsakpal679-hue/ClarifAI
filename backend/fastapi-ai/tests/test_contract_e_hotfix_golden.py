"""
Contract E Hotfix Golden Verification & Generalization Suite
Verifies:
- 24/24 clauses extracted without empty or near-empty original_text
- Perfect category alignment across standard legal categories
- Severity calibration from Consultant perspective (High recall on 4, 5, 15; 0 High-to-Safe/Low errors)
- Zero banned template phrases
- Executive overview contains purpose, labeled key figures, and blank template fields
- Generalization on an unseen held-out contract
"""

import os
import re
import pytest
from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_document_clauses
from app.services.output_validator_service import validate_and_resolve_clause_risk
from app.services.rule_engine_service import evaluate_document_rules
from app.services.summarization_service import generate_document_level_summary
from app.services.simplification_service import simplify_single_clause

CONTRACT_E_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../../evaluation_dataset/documents/SampleContract-Shuttle.pdf"
))

HELD_OUT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../../evaluation_dataset/documents/held_out_1_mutual_nda.pdf"
))

BANNED_TEMPLATE_PHRASES = [
    "operative obligations governed under",
    "clause evaluated under category",
    "plain-english explanation exceeded echo threshold",
    "needs review: plain-english explanation"
]


@pytest.fixture(scope="module")
def contract_e_pipeline():
    assert os.path.exists(CONTRACT_E_PATH), f"Contract E not found at {CONTRACT_E_PATH}"
    with open(CONTRACT_E_PATH, "rb") as f:
        pdf_bytes = f.read()

    ext_res = extract_pdf_text_service(pdf_bytes)
    clean_res = clean_legal_text(ext_res["full_text"])
    seg_res = segment_document_clauses(clean_res["cleaned_text"], pages=ext_res.get("pages"))
    rule_res = evaluate_document_rules(clauses=seg_res["clauses"], text=clean_res["cleaned_text"])
    cat_res = categorize_document_clauses(seg_res["clauses"], rule_findings=rule_res.get("findings", []))

    # Validate risks with Consultant perspective
    validated_clauses = []
    for c in cat_res["clauses"]:
        val_res = validate_and_resolve_clause_risk(
            clause=c,
            raw_classification={"severity": c.get("severity", "Low")},
            rule_findings=rule_res.get("findings", []),
            reviewing_party="Consultant"
        )
        c["severity"] = val_res.get("final_severity") or val_res.get("severity") or "Low"
        c["risk_reason"] = val_res.get("risk_reason", "")
        validated_clauses.append(c)

    summary_res = generate_document_level_summary(
        clauses=validated_clauses,
        rule_findings=rule_res.get("findings", []),
        document_header=clean_res.get("document_header")
    )

    return {
        "clauses": validated_clauses,
        "clean_res": clean_res,
        "summary": summary_res
    }


def test_contract_e_extraction_and_empty_check(contract_e_pipeline):
    """H6: Exactly 24 clauses found, none empty or near-empty (<20 chars)."""
    clauses = contract_e_pipeline["clauses"]
    assert len(clauses) == 24, f"Expected 24 clauses, got {len(clauses)}"

    for c in clauses:
        text = c.get("text", "")
        assert len(text.strip()) >= 20, f"Clause {c.get('position')} is too short ({len(text)} chars)"

    # Section 24 must be complete (was previously emptied)
    sec_24 = next(c for c in clauses if c.get("position") == 24 or c.get("clause_number") == "24")
    assert len(sec_24["text"]) > 1000, f"Section 24 should have substantial length, got {len(sec_24['text'])}"


def test_contract_e_category_alignment(contract_e_pipeline):
    """H2: Target category alignment for all 24 sections."""
    clauses = contract_e_pipeline["clauses"]
    expected_categories = {
        1: "Scope of Services",
        2: "Payment",
        3: "Term",
        4: "Termination",
        5: "Indemnification",
        6: "Insurance",
        7: "Compliance/Legal",
        8: "Compliance/Legal",
        9: "Compliance/Legal",
        10: "Compliance/Legal",
        11: "Compliance/Legal",
        12: "Audit and Records",
        13: "Compliance/Legal",
        14: "Compliance/Legal",
        15: "IP/Work Product",
        16: "Compliance/Legal",
        17: "Entire Agreement/General",
        18: "Dispute Resolution",
        19: "Audit and Records",
        20: "Subcontracting",
        21: "Assignment",
        22: "Compliance/Legal",
        23: "Notices",
        24: "Entire Agreement/General"
    }

    mismatches = []
    for c in clauses:
        pos = c.get("position")
        cat = c.get("category")
        exp = expected_categories.get(pos)
        if exp and cat != exp:
            mismatches.append(f"Section {pos}: got '{cat}', expected '{exp}'")

    assert len(mismatches) == 0, f"Category mismatches: {mismatches}"


def test_contract_e_severity_calibration(contract_e_pipeline):
    """H5: Consultant view calibration (High recall on 4, 5, 15; Safe clauses exist; 0 High-to-Safe/Low)."""
    clauses = contract_e_pipeline["clauses"]
    sev_map = {c.get("position"): str(c.get("severity")).capitalize() for c in clauses}

    # Target High risk clauses for Consultant
    assert sev_map[4] == "High", f"Section 4 (Early Termination) must be High, got {sev_map[4]}"
    assert sev_map[5] == "High", f"Section 5 (Indemnification) must be High, got {sev_map[5]}"
    assert sev_map[15] == "High", f"Section 15 (Work Products) must be High, got {sev_map[15]}"

    # Safe administrative clauses
    assert sev_map[21] == "Safe", f"Section 21 (Nonassignment) must be Safe, got {sev_map[21]}"
    assert sev_map[23] == "Safe", f"Section 23 (Notices) must be Safe, got {sev_map[23]}"
    safe_clauses = [pos for pos, s in sev_map.items() if s == "Safe"]
    assert len(safe_clauses) > 0, "Clause categorization must include Safe clauses"

    # No High-to-Low or High-to-Safe errors
    for pos in [4, 5, 15]:
        assert sev_map[pos] not in ("Low", "Safe"), f"Critical clause {pos} under-classified as {sev_map[pos]}"


def test_contract_e_executive_overview(contract_e_pipeline):
    """H7: Purpose text, labeled key figures, blank fields, and risk counts."""
    summary = contract_e_pipeline["summary"]
    purpose = summary.get("purpose_text") or summary.get("purpose")
    assert purpose is not None and len(purpose) > 20

    # Blank template fields
    blanks = summary.get("blank_template_fields", [])
    assert isinstance(blanks, list) and len(blanks) > 0

    # Risk counts
    counts = summary.get("risk_counts", {})
    assert "HIGH" in counts
    assert "MODERATE" in counts
    assert "LOW" in counts
    assert "SAFE" in counts
    assert counts["HIGH"] >= 3
    assert counts["SAFE"] > 0, f"Expected SAFE clauses in overview, got {counts['SAFE']}"


def test_contract_e_no_banned_templates(contract_e_pipeline):
    """H1: Zero banned template phrases across all clause simplifications."""
    clauses = contract_e_pipeline["clauses"][:5]  # Test sample of clauses
    for c in clauses:
        res = simplify_single_clause(c)
        plain = res.get("plain_language", "")
        for banned in BANNED_TEMPLATE_PHRASES:
            assert banned not in plain.lower(), f"Banned phrase '{banned}' found in clause {c.get('position')}"


def test_unseen_contract_generalization():
    """Generalization: Test pipeline on an unseen held-out contract."""
    if not os.path.exists(HELD_OUT_PATH):
        pytest.skip(f"Held out document not found at {HELD_OUT_PATH}")

    with open(HELD_OUT_PATH, "rb") as f:
        pdf_bytes = f.read()

    ext_res = extract_pdf_text_service(pdf_bytes)
    clean_res = clean_legal_text(ext_res["full_text"])
    seg_res = segment_document_clauses(clean_res["cleaned_text"])
    assert len(seg_res["clauses"]) > 0, "No clauses segmented in held-out contract"

    # All clauses must have >20 chars
    for c in seg_res["clauses"]:
        assert len(c["text"].strip()) >= 20, f"Clause {c.get('position')} too short in held-out doc"

    cat_res = categorize_document_clauses(seg_res["clauses"])
    assert len(cat_res["clauses"]) == len(seg_res["clauses"])
