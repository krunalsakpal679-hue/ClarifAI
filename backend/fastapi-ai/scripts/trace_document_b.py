"""
Trace pipeline stages for Document_B_Consulting_Services_Agreement.pdf
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

pdf_path = Path("c:/ClarifAI- AIPipeline/sample_documents/Document_B_Consulting_Services_Agreement.pdf")
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

print("=" * 80)
print("STAGE 1: EXTRACT")
ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
raw_text = ext["full_text"]
print(f"Extracted length: {len(raw_text)}")

print("\n" + "=" * 80)
print("STAGE 2: CLEAN")
cleaned = clean_legal_text(raw_text)["cleaned_text"]
print(f"Cleaned length: {len(cleaned)}")

print("\n" + "=" * 80)
print("STAGE 3: SEGMENTATION")
seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
segmented = seg_res["clauses"]
print(f"Total segmented clauses: {len(segmented)}")
for c in segmented:
    print(f"  Pos: {c.get('position')}, ID: {c.get('clause_id')}, Title: '{c.get('title')}', Text: {c.get('text', '')[:60]}...")

print("\n" + "=" * 80)
print("STAGE 4: RULE ENGINE")
rules_res = evaluate_rules(clauses=segmented, text=cleaned)
findings = rules_res.get("findings", [])
print(f"Total rule findings: {len(findings)}")
for f in findings:
    print(f"  Finding for clause: {f.get('clause_id')} ({f.get('clause_position')}): {f.get('rule_id')} - {f.get('risk_signal')}")

print("\n" + "=" * 80)
print("STAGE 5: CATEGORIZATION")
cat_res = categorize_clause_records(segmented, rule_findings=findings)
categorized = cat_res["clauses"]
print(f"Total categorized clauses: {len(categorized)}")
for c in categorized:
    print(f"  Pos: {c.get('position')}, ID: {c.get('clause_id')}, Categories: {c.get('categories')}, Text: {c.get('text', '')[:60]}...")

print("\n" + "=" * 80)
print("STAGE 6: RISK CLASSIFICATION")
risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
classified = risk_res["clauses"]
print(f"Total classified clauses: {len(classified)}")
for c in classified:
    print(f"  Pos: {c.get('position')}, ID: {c.get('clause_id')}, Severity: {c.get('severity')}, RiskSource: {c.get('risk_source')}, Text: {c.get('text', '')[:60]}...")

print("\n" + "=" * 80)
print("STAGE 7: SIMPLIFICATION")
simp_res = simplify_document_clauses(classified, rule_findings=findings)
simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])
print(f"Total simplified clauses: {len(simplified)}")
for c in simplified:
    print(f"  Pos: {c.get('position')}, ID: {c.get('clause_id')}, Text: {c.get('original_text', c.get('text', ''))[:60]}...")
    print(f"    What means: {c.get('structured_explanation', {}).get('what_this_clause_means')}")
    print(f"    Why flagged: {c.get('why_flagged')}")

print("\n" + "=" * 80)
print("STAGE 8: SUMMARIZATION")
sum_res = generate_document_summary(classified, rule_findings=findings)
print("Purpose:", sum_res.get("purpose_text"))
print("Key Risks:", sum_res.get("key_risks_text"))
print("Key Terms:", sum_res.get("key_terms_text"))
print("Obligations:", sum_res.get("obligations_text"))
