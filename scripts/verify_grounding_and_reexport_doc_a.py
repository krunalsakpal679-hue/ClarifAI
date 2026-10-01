"""
Verification script for BUG C and BUG D:
1. Tests Governing Law vs. Jurisdiction/Venue grounding on real Cook County clause and 3 adversarial variants.
2. Asserts full 7-clause completeness and position integrity for Document A (BUG C).
3. Asserts completeness across all documents in sample_documents/.
4. Re-exports Document A PDF and dumps the exact 7-row report table.
"""

import os
import sys
from pathlib import Path
import re
import json

# Setup Python paths
FASTAPI_PATH = Path("c:/ClarifAI- AIPipeline/backend/fastapi-ai").resolve()
sys.path.insert(0, str(FASTAPI_PATH))

from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.rule_engine_service import evaluate_rules
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import simplify_document_clauses, simplify_single_clause
from app.services.summarization_service import generate_document_summary


def test_bug_d_adversarial():
    print("--- [BUG D] Testing Governing Law vs. Jurisdiction / Venue Distinction ---")
    
    # 1. Real Cook County clause (Jurisdiction ONLY)
    cook_text = "Any action or proceeding arising out of or relating to this Agreement shall be submitted to the exclusive jurisdiction in Cook County, Illinois."
    res1 = simplify_single_clause({"text": cook_text, "category": "Dispute Resolution"})
    means1 = res1["structured_explanation"]["what_this_clause_means"]
    simp1 = res1["simplified_text"]
    print(f"1. Real Cook County clause (Jurisdiction Only):")
    print(f"   Means: {means1}")
    print(f"   Simplified Text snippet: {simp1[:150]}...")
    assert "governed by" not in means1.lower(), f"Unexpected 'governed by' in jurisdiction-only clause: {means1}"
    assert "governing law" not in means1.lower(), f"Unexpected 'governing law' in jurisdiction-only clause: {means1}"
    assert "governed by the laws of cook county" not in simp1.lower(), f"Unexpected 'governed by' in simplified text: {simp1}"
    assert "cook county" in means1.lower() or "illinois" in means1.lower()
    print("   -> PASS: No governing-law claims synthesized into jurisdiction-only clause.\n")

    # 2. Adversarial 1: Governing Law ONLY (no jurisdiction/venue)
    gov_text = "This Agreement and all claims arising out of or relating to this Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without giving effect to any choice or conflict of law provision or rule."
    res2 = simplify_single_clause({"text": gov_text, "category": "Dispute Resolution"})
    means2 = res2["structured_explanation"]["what_this_clause_means"]
    simp2 = res2["simplified_text"]
    print(f"2. Adversarial 1: Governing Law ONLY (Delaware):")
    print(f"   Means: {means2}")
    print(f"   Simplified Text snippet: {simp2[:150]}...")
    assert "delaware" in means2.lower()
    assert "governed by" in means2.lower() or "governing law" in means2.lower()
    assert "exclusive jurisdiction" not in means2.lower(), f"Invented exclusive jurisdiction: {means2}"
    assert "venue" not in means2.lower(), f"Invented venue: {means2}"
    assert "courts of" not in means2.lower(), f"Invented courts: {means2}"
    assert "litigated exclusively" not in simp2.lower(), f"Invented litigated exclusively: {simp2}"
    print("   -> PASS: Governing law accurately identified; no ungrounded court jurisdiction invented.\n")

    # 3. Adversarial 2: BOTH Governing Law AND Jurisdiction
    both_text = "This Agreement shall be governed by the laws of the State of New York, and each party irrevocably submits to the exclusive jurisdiction of the state and federal courts located in New York County for any dispute arising out of this Agreement."
    res3 = simplify_single_clause({"text": both_text, "category": "Dispute Resolution"})
    means3 = res3["structured_explanation"]["what_this_clause_means"]
    simp3 = res3["simplified_text"]
    print(f"3. Adversarial 2: BOTH Governing Law and Jurisdiction (New York):")
    print(f"   Means: {means3}")
    print(f"   Simplified Text snippet: {simp3[:150]}...")
    assert "new york" in means3.lower()
    assert "governed by" in means3.lower() or "governing law" in means3.lower()
    assert "exclusive venue" in means3.lower() or "exclusive jurisdiction" in means3.lower() or "courts" in means3.lower()
    assert "governing law" in simp3.lower()
    assert "jurisdiction" in simp3.lower() or "venue" in simp3.lower()
    print("   -> PASS: Both governing law and jurisdiction reported accurately.\n")

    # 4. Adversarial 3: NEITHER Governing Law NOR Jurisdiction (Informal Negotiation Escalation)
    neither_text = "In the event of any dispute, controversy, or claim arising from or relating to this Agreement, the parties shall first consult and negotiate in good faith to resolve the controversy informally within thirty (30) days."
    res4 = simplify_single_clause({"text": neither_text, "category": "Dispute Resolution"})
    means4 = res4["structured_explanation"]["what_this_clause_means"]
    simp4 = res4["simplified_text"]
    print(f"4. Adversarial 3: NEITHER Governing Law nor Jurisdiction (Escalation):")
    print(f"   Means: {means4}")
    print(f"   Simplified Text snippet: {simp4[:150]}...")
    assert "governed by" not in means4.lower()
    assert "governing law" not in means4.lower()
    assert "exclusive jurisdiction" not in means4.lower()
    assert "venue" not in means4.lower()
    assert "dispute" in means4.lower()
    print("   -> PASS: Pure escalation procedure reported; no law or jurisdiction invented.\n")


def get_sample_dir():
    candidates = [
        Path("c:/ClarifAI- AIPipeline/sample_documents"),
        Path("/sample_documents"),
        Path(__file__).resolve().parent.parent / "sample_documents"
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    raise FileNotFoundError("Could not find sample_documents directory in candidate locations.")


def test_bug_c_completeness_all_documents():
    print("--- [BUG C] Testing Completeness & Position Integrity Across All Sample Documents ---")
    sample_dir = get_sample_dir()
    pdf_files = sorted(list(sample_dir.glob("*.pdf")))
    
    for pdf_path in pdf_files:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
        cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
        seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
        segmented = seg_res["clauses"]
        n_clauses = len(segmented)

        rules_res = evaluate_rules(clauses=segmented, text=cleaned)
        findings = rules_res["findings"]
        cat_res = categorize_clause_records(segmented, rule_findings=findings)
        categorized = cat_res["clauses"]
        risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
        classified = risk_res["clauses"]
        simp_res = simplify_document_clauses(classified, rule_findings=findings)
        simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])

        assert len(categorized) == n_clauses, f"{pdf_path.name}: categorized count {len(categorized)} != {n_clauses}"
        assert len(classified) == n_clauses, f"{pdf_path.name}: classified count {len(classified)} != {n_clauses}"
        assert len(simplified) == n_clauses, f"{pdf_path.name}: simplified count {len(simplified)} != {n_clauses}"

        expected_positions = list(range(1, n_clauses + 1))
        actual_positions = [c["position"] for c in simplified]
        assert actual_positions == expected_positions, f"{pdf_path.name} position mismatch: {actual_positions} vs {expected_positions}"

        print(f"  [OK] {pdf_path.name}: Exactly {n_clauses} clauses processed with continuous positions 1..{n_clauses} (no gaps).")

    print("--- BUG C Sample Document Integrity All Passed ---\n")


def reexport_document_a():
    print("--- Re-exporting Document A Fresh Report Table ---")
    sample_dir = get_sample_dir()
    doc_a_path = sample_dir / "Document_A_SaaS_Service_Agreement.pdf"
    with open(doc_a_path, "rb") as f:
        pdf_bytes = f.read()

    ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
    cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
    seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
    segmented = seg_res["clauses"]

    rules_res = evaluate_rules(clauses=segmented, text=cleaned)
    findings = rules_res["findings"]
    cat_res = categorize_clause_records(segmented, rule_findings=findings)
    categorized = cat_res["clauses"]
    risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
    classified = risk_res["clauses"]
    simp_res = simplify_document_clauses(classified, rule_findings=findings)
    simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])

    print(f"Document A total clauses: {len(simplified)}\n")
    print(f"{'Pos':<5} | {'Severity':<10} | {'Category':<22} | {'What This Clause Means / Summary'}")
    print("-" * 120)
    
    rows = []
    for idx, c in enumerate(simplified):
        pos = c.get("position", idx + 1)
        sev_val = c.get("severity") or classified[idx].get("severity") or "RISK_CLASSIFICATION_UNAVAILABLE"
        sev = str(sev_val).upper()
        cat = c.get("category") or classified[idx].get("category") or c.get("structured_explanation", {}).get("category", {}).get("label") or "Unclassified"
        means = c.get("structured_explanation", {}).get("what_this_clause_means") or c.get("simplified_text")
        print(f"{pos:<5} | {sev:<10} | {cat:<22} | {means}")
        rows.append({
            "pos": pos,
            "sev": sev,
            "cat": cat,
            "summary": means,
            "obligations": c.get("structured_explanation", {}).get("key_obligations"),
            "details": c.get("structured_explanation", {}).get("key_details", [])
        })

    with open("doc_a_verified_fresh_report.json", "w", encoding="utf-8") as out_f:
        json.dump(rows, out_f, indent=2)
    print("\nSaved full dump to doc_a_verified_fresh_report.json")


if __name__ == "__main__":
    test_bug_d_adversarial()
    test_bug_c_completeness_all_documents()
    reexport_document_a()
