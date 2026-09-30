"""
ClarifAI Master Audit Part 3: Generalization Check Across All 5 Repository Sample Documents
1. Sample_Master_Services_Agreement.pdf
2. Document_B_Consulting_Services_Agreement.pdf
3. Document_A_SaaS_Service_Agreement.pdf
4. Sample_Non_Disclosure_Agreement.pdf
5. golden_lease_deed.pdf
"""

import sys
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
from app.services.summarization_service import generate_document_summary

DOCUMENTS = [
    ("Sample Master Services Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/Sample_Master_Services_Agreement.pdf")),
    ("Document B Consulting Services Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/Document_B_Consulting_Services_Agreement.pdf")),
    ("Document A SaaS Service Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/Document_A_SaaS_Service_Agreement.pdf")),
    ("Sample Non-Disclosure Agreement", Path("c:/ClarifAI- AIPipeline/sample_documents/Sample_Non_Disclosure_Agreement.pdf")),
    ("Golden Lease Deed", Path("c:/ClarifAI- AIPipeline/sample_documents/golden_lease_deed.pdf")),
]

def run_generalization_audit():
    for doc_name, doc_path in DOCUMENTS:
        print("\n" + "=" * 90)
        print(f"DOCUMENT AUDIT: {doc_name}")
        print(f"Path: {doc_path}")
        print("=" * 90)
        
        if not doc_path.exists():
            print(f"ERROR: Document not found at {doc_path}")
            continue
            
        with open(doc_path, "rb") as f:
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
        
        sum_res = generate_document_summary(classified, rule_findings=findings)
        
        print(f"\nExecutive Summary:")
        print(f"  Purpose:     {sum_res.get('purpose_text')}")
        print(f"  Key Risks:   {sum_res.get('key_risks_text')}")
        print(f"  Key Terms:   {sum_res.get('key_terms_text')}")
        print(f"  Obligations: {sum_res.get('obligations_text')}")
        
        print(f"\nPer-Clause Audit Table ({len(simplified)} clauses):")
        print(f"{'Pos':<4} | {'Clause ID':<7} | {'Category':<20} | {'Severity':<9} | {'Evidence Substring?':<20} | {'Claim Grounding Status':<22}")
        print("-" * 90)
        
        for idx, sc in enumerate(simplified, start=1):
            pos = sc.get("position", idx)
            cid = sc.get("clause_id", f"c-{pos:03d}")
            orig = sc.get("original_text", "")
            
            exp_struct = sc.get("structured_explanation", {})
            cat = exp_struct.get("category", {}).get("label") or "Unclassified"
            sev = sc.get("severity") or exp_struct.get("risk", {}).get("severity") or "Safe"
            
            cat_ev = exp_struct.get("category", {}).get("evidence", "")
            risk_ev = exp_struct.get("risk", {}).get("evidence", "")
            
            # Substring checks
            cat_ev_valid = bool(cat_ev and cat_ev in orig) if cat_ev else True
            risk_ev_valid = bool(risk_ev and risk_ev in orig) if risk_ev else True
            ev_valid_str = "YES (Verbatim)" if (cat_ev_valid and risk_ev_valid) else "MISMATCH"
            
            # Narrative Grounding Checks
            what_means = exp_struct.get("what_this_clause_means", "")
            simp_text = sc.get("simplified_text", "")
            
            # Check for ungrounded payment condition
            has_invented_cond = ("conditioned upon full payment" in simp_text.lower() or "upon fee satisfaction" in simp_text.lower()) and ("payment" not in orig.lower())
            
            # Check for ungrounded remedies
            has_invented_injunct = ("immediate injunctive relief" in simp_text.lower()) and ("injunct" not in orig.lower())
            has_invented_attorney = ("reasonable attorney fees" in simp_text.lower()) and ("attorney" not in orig.lower())
            
            # Check for ungrounded substantive law
            has_conflated_law = ("substantive law" in what_means.lower()) and ("governing law" not in orig.lower() and "laws of" not in orig.lower())
            
            if has_invented_cond or has_invented_injunct or has_invented_attorney or has_conflated_law:
                grounding_status = "FAILED GROUNDING"
            else:
                grounding_status = "PASSED GROUNDING"
                
            print(f"{pos:<4} | {cid:<7} | {cat:<20} | {sev:<9} | {ev_valid_str:<20} | {grounding_status:<22}")

if __name__ == "__main__":
    run_generalization_audit()
