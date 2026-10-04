import sys
import json
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path("backend/fastapi-ai").resolve()))

from app.services.pdf_service import extract_pdf_text_service
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_executive_summary
from app.services.claim_grounding_service import check_banned_strings, BANNED_STRINGS

CONTRACT_A_PATH = "sample_documents/Sample_Cloud_Consulting_Agreement.pdf"
CONTRACT_B_PATH = "sample_documents/Document_B_Consulting_Services_Agreement.pdf"
CONTRACT_C_PATH = "sample_documents/Sample_Commercial_Lease_Agreement.pdf"

def process_pdf(pdf_path, doc_title):
    pdf_bytes = Path(pdf_path).read_bytes()
    pdf_extract = extract_pdf_text_service(pdf_bytes, Path(pdf_path).name)
    text = pdf_extract["full_text"]
    
    seg_res = segment_document_clauses(text)
    raw_clauses = seg_res["clauses"]
    
    cat_res = categorize_clause_records(raw_clauses)
    categorized_clauses = cat_res["clauses"]
    
    simp_res = simplify_document_clauses(categorized_clauses)
    processed_clauses = simp_res["clauses"]
    
    # Audit each clause
    for c in processed_clauses:
        c["banned_strings_found"] = check_banned_strings(c["simplified_text"])
        
    exec_summary = generate_document_executive_summary(
        full_document_text=text,
        clauses=processed_clauses,
        document_title=doc_title
    )
    
    return {
        "document_title": doc_title,
        "total_clauses": len(processed_clauses),
        "preamble": seg_res.get("preamble"),
        "signature_block": seg_res.get("signature_block"),
        "executive_overview": exec_summary,
        "clauses": processed_clauses
    }

if __name__ == "__main__":
    report_a = process_pdf(CONTRACT_A_PATH, "Cloud Infrastructure Consulting Agreement")
    report_b = process_pdf(CONTRACT_B_PATH, "Consulting Services Agreement")
    report_c = process_pdf(CONTRACT_C_PATH, "Commercial Lease Agreement")
    
    out_dict = {
        "Contract_A": report_a,
        "Contract_B": report_b,
        "Contract_C": report_c
    }
    
    output_path = Path("backend/fastapi-ai/tests/fixtures/generated_reports_dump.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out_dict, indent=2), encoding="utf-8")
    
    print(f"Contract A clauses: {report_a['total_clauses']}")
    print(f"Contract B clauses: {report_b['total_clauses']}")
    print(f"Contract C clauses: {report_c['total_clauses']}")
    print("Reports successfully generated and dumped.")
