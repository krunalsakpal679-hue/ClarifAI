"""
Runner for Contracts A, B, C, and D through the real ClarifAI pipeline (with Groq ON).
Outputs side-by-side comparison of actual contract text vs generated analysis per clause.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add fastapi-ai to sys.path
sys.path.insert(0, str(Path("backend/fastapi-ai").resolve()))

from app.core.config import settings
from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.risk_service import classify_document_clauses_risk, load_legal_bert_model
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_summary

CONTRACT_FILES = [
    {
        "id": "Contract A",
        "file": "contract_a_cloud_consulting.pdf",
        "title": "Cloud Infrastructure Consulting Agreement",
        "party_a": "Cascade Robotics Inc. (Client)",
        "party_b": "Vantage Point Cloud Solutions LLC (Consultant)",
        "reviewing_party": "Cascade Robotics Inc."
    },
    {
        "id": "Contract B",
        "file": "contract_b_consulting_services.pdf",
        "title": "Strategic Consulting Services Agreement",
        "party_a": "Vanguard Manufacturing Group (Client)",
        "party_b": "Vantage Advisory Partners LLC (Consultant)",
        "reviewing_party": "Vanguard Manufacturing Group"
    },
    {
        "id": "Contract C",
        "file": "contract_c_commercial_lease.pdf",
        "title": "Commercial Lease Agreement",
        "party_a": "Vanguard Commercial Properties LLC (Landlord)",
        "party_b": "Quantum Analytics Inc. (Tenant)",
        "reviewing_party": "Quantum Analytics Inc."
    },
    {
        "id": "Contract D",
        "file": "contract_d_master_services_agreement.pdf",
        "title": "Master Services Agreement, Enterprise Cloud Services",
        "party_a": "CloudScale Technologies, Inc. (Vendor)",
        "party_b": "Enterprise Solutions Global Ltd. (Customer)",
        "reviewing_party": "Enterprise Solutions Global Ltd."
    }
]

def process_contracts():
    print("=" * 80)
    print("ClarifAI Step 2: Live Pipeline Execution for Contracts A, B, C, D (Groq ON)")
    print("=" * 80)

    # Startup checkpoint verification
    load_legal_bert_model()

    results_all = {}

    for c_info in CONTRACT_FILES:
        pdf_path = Path("evaluation_dataset/documents") / c_info["file"]
        if not pdf_path.exists():
            print(f"Error: {pdf_path} not found!")
            continue

        print(f"\nProcessing {c_info['id']}: {c_info['title']} ({c_info['file']})...")
        pdf_bytes = pdf_path.read_bytes()
        doc_hash = hashlib.sha256(pdf_bytes).hexdigest()

        extracted = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
        cleaned = clean_legal_text(extracted["full_text"])
        segmented = segment_document_clauses(cleaned["cleaned_text"])
        categorized = categorize_clause_records(segmented["clauses"])
        classified = classify_document_clauses_risk(categorized["clauses"], reviewing_party=c_info["reviewing_party"])
        simplified = simplify_document_clauses(classified["clauses"])
        summary = generate_document_summary(clauses=simplified["clauses"], full_document_text=cleaned["cleaned_text"])

        clauses_out = simplified["clauses"]
        print(f"-> Total Segments: {len(clauses_out)}, Executive Purpose: {summary.get('purpose_text')[:60]}...")

        contract_report = {
            "contract_id": c_info["id"],
            "title": c_info["title"],
            "sha256": doc_hash,
            "reviewing_party": c_info["reviewing_party"],
            "summary": summary,
            "clauses": []
        }

        for cl in clauses_out:
            c_num = cl.get("clause_number") or cl.get("position")
            c_title = cl.get("title", "Untitled")
            orig_text = cl.get("original_text") or cl.get("text", "")
            cat = cl.get("category", "General")
            sev = cl.get("severity", "Low")
            explanation = cl.get("simplified_text") or cl.get("structured_explanation", {}).get("what_this_clause_means", "")
            why_sev = cl.get("why_flagged") or cl.get("structured_explanation", {}).get("risk", {}).get("reason", "")
            key_details = cl.get("key_details", [])

            contract_report["clauses"].append({
                "clause_number": str(c_num),
                "title": c_title,
                "category": cat,
                "severity": sev,
                "original_text": orig_text.strip(),
                "generated_explanation": explanation.strip(),
                "severity_reason": why_sev.strip(),
                "key_details": key_details
            })

        results_all[c_info["id"]] = contract_report

    out_json = Path("evaluation_dataset/contracts_a_to_d_real_output.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results_all, f, indent=2)

    print(f"\nSaved complete outputs to {out_json}")
    return results_all

if __name__ == "__main__":
    process_contracts()
