"""
Definitive Concurrent Multi-Document Isolation & Non-Contamination Regression Test Suite
Validates that running Sample_Master_Services_Agreement.pdf, new_doc_1_employment_agreement.pdf,
and new_doc_3_saas_terms_of_service.pdf SIMULTANEOUSLY in parallel threads exhibits:
1. Exact clause count integrity (9 clauses for MSA, not 10).
2. Zero cross-document party or role leakage (No Employer/Employee or Customer/Subscriber in MSA).
3. Zero contaminated clause text or structured explanation leakage.
4. Clean narrative syntax (no double commas, dangling conjunctions, or mid-sentence deletions).
"""

import concurrent.futures
import os
import re
from pathlib import Path
import fitz
import pytest

from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.rule_engine_service import evaluate_rules
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_summary


def process_pdf_pipeline(pdf_path: str):
    """Executes full microservice processing pipeline for a PDF document."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])

    seg_res = segment_document_clauses(text)
    clauses = seg_res["clauses"]

    cat_res = categorize_clause_records(clauses)
    categorized = cat_res["clauses"]

    rules_res = evaluate_rules(categorized)
    rule_findings = rules_res.get("findings", [])

    risk_res = classify_document_clauses_risk(categorized, rule_findings=rule_findings)
    risk_clauses = risk_res.get("clauses", categorized)

    simp_res = simplify_document_clauses(risk_clauses, rule_findings=rule_findings)
    simplified_clauses = simp_res.get("clauses", [])

    summary_res = generate_document_summary(text, simplified_clauses)

    return {
        "pdf_path": pdf_path,
        "text": text,
        "clause_count": len(simplified_clauses),
        "clauses": simplified_clauses,
        "summary": summary_res
    }


def test_concurrent_three_document_isolation():
    """Concurrently processes MSA, Employment Agreement, and SaaS ToS and asserts zero cross-contamination."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    msa_path = str(repo_root / "sample_documents" / "Sample_Master_Services_Agreement.pdf")
    emp_path = str(repo_root / "evaluation_dataset" / "documents" / "new_doc_1_employment_agreement.pdf")
    saas_path = str(repo_root / "evaluation_dataset" / "documents" / "new_doc_3_saas_terms_of_service.pdf")

    assert os.path.exists(msa_path), f"Missing {msa_path}"
    assert os.path.exists(emp_path), f"Missing {emp_path}"
    assert os.path.exists(saas_path), f"Missing {saas_path}"

    paths = [msa_path, emp_path, saas_path]

    # Execute all 3 documents simultaneously using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_pdf_pipeline, p): p for p in paths}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            results[p] = future.result()

    msa_res = results[msa_path]
    emp_res = results[emp_path]
    saas_res = results[saas_path]

    # 1. MSA Clause Count Integrity
    assert msa_res["clause_count"] == 9, f"MSA should have exactly 9 clauses, found {msa_res['clause_count']}"

    # 2. MSA Isolation Check: Zero Employment or SaaS terms
    msa_all_text = " ".join([
        f"{c.get('title', '')} {c.get('text', '')} {c.get('plain_english_summary', '')} {c.get('key_obligations', '')} {c.get('identified_parties', '')} {c.get('consequences_of_breach', '')} {' '.join(c.get('details', []))}"
        for c in msa_res["clauses"]
    ]) + " " + msa_res["summary"].get("executive_summary", "") + " " + msa_res["summary"].get("title", "")

    assert "Employer and Employee" not in msa_all_text, "MSA contains 'Employer and Employee' contaminated parties"
    assert "Customer/Subscriber" not in msa_all_text, "MSA contains 'Customer/Subscriber' contaminated parties"
    assert "employment position" not in msa_all_text.lower(), "MSA contains 'employment position' contaminated text"
    assert "job responsibilities" not in msa_all_text.lower(), "MSA contains 'job responsibilities' contaminated text"
    assert "reporting structure" not in msa_all_text.lower(), "MSA contains 'reporting structure' contaminated text"
    assert "Tlined In" not in msa_res["summary"].get("title", ""), "MSA executive summary title contains garbled text"

    # 3. Employment Agreement Isolation Check: Zero Commercial Vendor or SaaS terms
    emp_all_text = " ".join([
        f"{c.get('title', '')} {c.get('text', '')} {c.get('plain_english_summary', '')} {c.get('key_obligations', '')} {c.get('identified_parties', '')}"
        for c in emp_res["clauses"]
    ])
    assert "Customer/Subscriber" not in emp_all_text, "Employment Agreement contains 'Customer/Subscriber'"
    assert "Master Services Agreement" not in emp_all_text, "Employment Agreement contains MSA title"

    # 4. SaaS ToS Isolation Check: Zero Employment terms
    saas_all_text = " ".join([
        f"{c.get('title', '')} {c.get('text', '')} {c.get('plain_english_summary', '')} {c.get('key_obligations', '')} {c.get('identified_parties', '')}"
        for c in saas_res["clauses"]
    ])
    assert "Employer and Employee" not in saas_all_text, "SaaS ToS contains 'Employer and Employee'"
    assert "Chief Technology Officer" not in saas_all_text, "SaaS ToS contains Employment position text"

    # 5. Narrative Syntax Integrity on all documents (no double commas or dangling conjunctions)
    for doc_name, doc_data in [("MSA", msa_res), ("EMP", emp_res), ("SAAS", saas_res)]:
        for c in doc_data["clauses"]:
            for field in ["plain_english_summary", "key_obligations", "consequences_of_breach"] + c.get("details", []):
                val = c.get(field, "") if isinstance(field, str) and field in c else str(field)
                assert ", ," not in val, f"Found double comma in {doc_name} clause {c.get('position')}: '{val}'"
                assert not re.search(r'\b(?:and|or|with|to)\s+\.', val), f"Found dangling conjunction in {doc_name} clause {c.get('position')}: '{val}'"
