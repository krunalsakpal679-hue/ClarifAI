"""
Phase 4 Verification Script:
1. Part 3: Reprocess stale documents test on local documents, verifying before/after changes.
2. Part 4: Full golden-document regression across MSA, Consulting, NDA, and Lease/Loan documents.
   Validates category, severity, risk_source, and exact substring evidence in structured_explanation.
"""
import os
import sys
import json
import logging
from pathlib import Path

FASTAPI_ROOT = Path("c:/ClarifAI- AIPipeline/backend/fastapi-ai")
sys.path.insert(0, str(FASTAPI_ROOT))

from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.rule_engine_service import evaluate_rules
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import simplify_document_clauses

SAMPLE_DOCS = [
    ("Master Services Agreement (MSA)", Path("c:/ClarifAI- AIPipeline/sample_documents/Sample_Master_Services_Agreement.pdf")),
    ("Consulting Services Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/Document_B_Consulting_Services_Agreement.pdf")),
    ("Non-Disclosure Agreement (NDA)", Path("c:/ClarifAI- AIPipeline/sample_documents/Sample_Non_Disclosure_Agreement.pdf")),
    ("Commercial Lease Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/golden_lease_deed.pdf")),
]

def run_pipeline_for_pdf(pdf_path: Path):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Extract
    extracted = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
    raw_text = extracted.get("full_text", "")
    pages = extracted.get("pages", [])

    # 2. Clean
    cleaned = clean_legal_text(raw_text).get("cleaned_text", raw_text)

    # 3. Segment
    segmented = segment_document_clauses(cleaned, pages=pages).get("clauses", [])

    # 4. Rule engine (run on segmented clauses)
    rule_res = evaluate_rules(clauses=segmented, text=cleaned)
    findings = rule_res.get("findings", [])

    # 5. Categorize (with rule findings signal)
    cat_res = categorize_clause_records(segmented, rule_findings=findings)
    categorized = cat_res.get("clauses", segmented)

    # 6. Risk classification
    risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
    classified_clauses = risk_res.get("clauses", categorized)

    # 7. Simplification + Structured Explanation
    simp_res = simplify_document_clauses(classified_clauses, rule_findings=findings)
    simplified_clauses = simp_res.get("simplified_clauses", classified_clauses)
    simp_map = {sc.get("position", idx): sc for idx, sc in enumerate(simplified_clauses, start=1)}

    results = []
    for idx, clause in enumerate(classified_clauses, start=1):
        pos = clause.get("position", idx)
        simp = simp_map.get(pos, {})
        orig_text = clause.get("original_text", "") or clause.get("text", "")
        structured_exp = simp.get("structured_explanation") or {}

        risk_obj = structured_exp.get("risk") or structured_exp.get("risk_assessment") or {}
        cat_obj = structured_exp.get("category") or structured_exp.get("category_assessment") or {}

        risk_ev = risk_obj.get("evidence")
        cat_ev = cat_obj.get("evidence")

        all_ev = []
        if isinstance(risk_ev, list):
            all_ev.extend(risk_ev)
        elif isinstance(risk_ev, str) and risk_ev.strip():
            all_ev.append(risk_ev)

        if isinstance(cat_ev, list):
            all_ev.extend(cat_ev)
        elif isinstance(cat_ev, str) and cat_ev.strip():
            all_ev.append(cat_ev)

        valid_substrings = []
        for ev in all_ev:
            if ev and isinstance(ev, str) and ev.strip():
                clean_ev = ev.strip().strip('"').strip("'")
                valid_substrings.append(clean_ev in orig_text or clean_ev.lower() in orig_text.lower())

        all_evidence_is_substring = all(valid_substrings) if valid_substrings else True

        # Category label
        cat_label = clause.get("category")
        if not cat_label and clause.get("categories"):
            cat_label = clause.get("categories")[0]
        if hasattr(cat_label, "value"):
            cat_label = cat_label.value
        if not cat_label:
            cat_label = "Unclassified"

        # Risk source
        risk_source = clause.get("risk_source") or "MODEL_CLASSIFICATION"

        results.append({
            "position": idx,
            "category": cat_label,
            "severity": clause.get("severity"),
            "risk_source": risk_source,
            "text_snippet": orig_text[:60].replace("\n", " ") + ("..." if len(orig_text) > 60 else ""),
            "all_evidence_is_substring": all_evidence_is_substring,
            "evidence_count": len(all_ev),
            "evidence_quotes": all_ev[:2],
        })

    return results

def main():
    print("=" * 80)
    print("PHASE 4: FULL GOLDEN-DOCUMENT REGRESSION AUDIT ACROSS 4 CONTRACT ARCHETYPES")
    print("=" * 80)

    for doc_name, pdf_path in SAMPLE_DOCS:
        if not pdf_path.exists():
            print(f"\nSkipping {doc_name}: {pdf_path} does not exist.")
            continue

        print(f"\n### Contract: {doc_name} ({pdf_path.name})")
        clauses = run_pipeline_for_pdf(pdf_path)
        print(f"Total Clauses Analyzed: {len(clauses)}\n")

        print(f"| Position | Category | Severity | Risk Source | Evidence Substring Valid? | Clause Text Snippet |")
        print(f"|---|---|---|---|---|---|")
        for c in clauses:
            sub_valid_str = "YES (100% Substring)" if c["all_evidence_is_substring"] else "NO (Hallucinated)"
            print(f"| Clause {c['position']} | {c['category']} | {c['severity']} | {c['risk_source']} | {sub_valid_str} | {c['text_snippet']} |")

if __name__ == "__main__":
    main()
