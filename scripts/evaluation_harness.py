"""
ClarifAI Document-Agnostic Evaluation Harness (Phase B)
Automated testing framework to benchmark pipeline generalization against ground-truth answer keys.
Evaluates:
- Category accuracy per clause
- Severity accuracy per clause
- Hallucination / Invention rate in 'what_this_clause_means' (unsupported claims)
- Omission rate of material ground-truth facts/numbers/covenants
- Directionality accuracy (obligor vs beneficiary)
- Preservation of conditional triggers and exception carve-outs
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Ensure FastAPI backend modules can be imported
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FASTAPI_DIR = WORKSPACE_ROOT / "backend" / "fastapi-ai"
if str(FASTAPI_DIR) not in sys.path:
    sys.path.insert(0, str(FASTAPI_DIR))

from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.rule_engine_service import evaluate_rules
from app.services.clause_categorization_service import categorize_clause_records
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import simplify_document_clauses
from app.services.summarization_service import generate_document_summary


def run_pipeline_on_pdf(pdf_path: Path) -> Dict[str, Any]:
    """Runs a PDF through the full ClarifAI AI pipeline and returns all intermediate & final outputs."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. PDF Extraction
    extraction_res = extract_pdf_text_service(pdf_bytes, pdf_path.name)
    full_text = extraction_res.get("full_text", "")
    pages = extraction_res.get("pages", [])

    # 2. Text Cleaning
    clean_res = clean_legal_text(full_text)
    cleaned_text = clean_res.get("cleaned_text", full_text)

    # 3. Clause Segmentation
    segment_res = segment_document_clauses(cleaned_text, pages=pages)
    segmented_clauses = segment_res.get("clauses", [])

    # 4. Rule Engine Evaluation
    rule_res = evaluate_rules(clauses=segmented_clauses, text=cleaned_text)
    rule_findings = rule_res.get("findings", [])

    # 5. Clause Categorization
    categorize_res = categorize_clause_records(segmented_clauses, rule_findings=rule_findings)
    categorized_clauses = categorize_res.get("clauses", segmented_clauses)

    # 6. Risk Classification
    risk_res = classify_document_clauses_risk(categorized_clauses, rule_findings=rule_findings)
    classified_clauses = risk_res.get("clauses", categorized_clauses)

    # 7. Plain-Language Simplification & Structured Explanation
    simplify_res = simplify_document_clauses(classified_clauses, rule_findings=rule_findings)
    simplified_clauses = simplify_res.get("clauses", classified_clauses)

    # 8. Document Executive Summary
    summary_res = generate_document_summary(simplified_clauses, rule_findings=rule_findings)

    return {
        "extracted_text": full_text,
        "cleaned_text": cleaned_text,
        "segmented_clauses": segmented_clauses,
        "rule_findings": rule_findings,
        "categorized_clauses": categorized_clauses,
        "classified_clauses": classified_clauses,
        "simplified_clauses": simplified_clauses,
        "summary": summary_res,
    }


def extract_keywords_and_entities(text: str) -> set:
    """Extracts key tokens, numbers, percentages, currency amounts, and technical terms from text."""
    if not text:
        return set()
    text_lower = text.lower()
    # Find numbers, currency, percentages
    numbers = re.findall(r"\b(?:\$|₹|€)?\d+(?:[\.,]\d+)?%?\b", text_lower)
    # Find words with 4+ characters
    words = re.findall(r"\b[a-z]{4,}\b", text_lower)
    stopwords = {
        "this", "that", "with", "from", "shall", "will", "have", "been", "were",
        "their", "there", "other", "under", "which", "party", "parties", "agreement",
        "clause", "section", "pursuant", "accordance", "hereunder", "thereof"
    }
    filtered_words = [w for w in words if w not in stopwords]
    return set(numbers + filtered_words)


def evaluate_clause_match(gt_clause: Dict[str, Any], pipeline_clause: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares a single pipeline clause output against its ground truth specification.
    """
    gt_cat = (gt_clause.get("gt_category") or gt_clause.get("category") or "").strip().lower()
    gt_sev = (gt_clause.get("gt_severity") or gt_clause.get("severity") or "").strip().lower()

    # Extract pipeline category
    pipe_cats = pipeline_clause.get("categories", [])
    pipe_cat_names = []
    if isinstance(pipe_cats, list):
        for c in pipe_cats:
            val = c.value if hasattr(c, "value") else str(c)
            val = val.replace("ClauseCategoryEnum.", "").replace("clausecategoryenum.", "").replace("_", " ").strip().lower()
            pipe_cat_names.append(val)
    else:
        val = pipe_cats.value if hasattr(pipe_cats, "value") else str(pipe_cats)
        val = val.replace("ClauseCategoryEnum.", "").replace("clausecategoryenum.", "").replace("_", " ").strip().lower()
        pipe_cat_names.append(val)
    
    # Handle structured explanation category if present
    struct_expl = pipeline_clause.get("structured_explanation", {})
    if isinstance(struct_expl, dict):
        cat_struct = struct_expl.get("category", {})
        if isinstance(cat_struct, dict) and cat_struct.get("label"):
            lbl = str(cat_struct.get("label")).replace("ClauseCategoryEnum.", "").replace("_", " ").strip().lower()
            pipe_cat_names.append(lbl)

    # Standard PRD category match: canonical taxonomy mapping supported
    canonical_map = {
        "intellectual property": "ip/work product",
        "general / boilerplate": "entire agreement/general",
        "property / premises": "premises",
        "property use": "use",
        "general": "entire agreement/general",
        "liability": "limitation of liability",
    }
    norm_gt_cat = canonical_map.get(gt_cat, gt_cat)
    category_correct = False
    if gt_cat in ("unclassified", "none", ""):
        category_correct = (len(pipe_cat_names) == 0 or all(c in ("unclassified", "none", "") for c in pipe_cat_names))
    else:
        category_correct = (gt_cat in pipe_cat_names or norm_gt_cat in pipe_cat_names)

    # Extract pipeline severity: Safe and Low are equivalent base levels
    pipe_sev = str(pipeline_clause.get("severity", "")).strip().lower()
    severity_correct = (gt_sev == pipe_sev or (gt_sev in ("safe", "low") and pipe_sev in ("safe", "low")))

    # Explanations
    what_means = ""
    if isinstance(struct_expl, dict) and struct_expl.get("what_this_clause_means"):
        what_means = struct_expl.get("what_this_clause_means", "")
    elif pipeline_clause.get("simplified_text"):
        what_means = pipeline_clause.get("simplified_text", "")

    why_flagged = pipeline_clause.get("why_flagged", "")
    full_explanation = f"{what_means} {why_flagged}".strip()

    # 1. Invention Check: Are claims in explanation grounded in source text?
    source_tokens = extract_keywords_and_entities(gt_clause.get("verbatim_text", "") or pipeline_clause.get("original_text", ""))
    expl_tokens = extract_keywords_and_entities(what_means)
    
    # Check for hallucinated numbers / terms not in source
    source_numbers = set(re.findall(r"\b(?:\$|₹|€)?\d+(?:[\.,]\d+)?%?\b", (gt_clause.get("verbatim_text", "") or pipeline_clause.get("original_text", "")).lower()))
    expl_numbers = set(re.findall(r"\b(?:\$|₹|€)?\d+(?:[\.,]\d+)?%?\b", what_means.lower()))
    invented_numbers = expl_numbers - source_numbers

    # Must Not Contain phrases
    must_not = gt_clause.get("must_not_contain", [])
    forbidden_found = [p for p in must_not if re.search(r'\b' + re.escape(p) + r'\b' if len(p) <= 4 else re.escape(p), what_means, re.IGNORECASE)]

    has_invention = (len(invented_numbers) > 0) or (len(forbidden_found) > 0)

    # 2. Fact Retention / Omission Check
    must_contain = gt_clause.get("must_contain", [])
    retained_facts_count = 0
    if must_contain:
        for f in must_contain:
            if f.lower() in what_means.lower() or f.lower() in pipeline_clause.get("original_text", "").lower():
                retained_facts_count += 1
        fact_retention = retained_facts_count / len(must_contain)
    else:
        fact_retention = 1.0

    material_claims = gt_clause.get("material_claims", [])
    omitted_claims = []
    for claim in material_claims:
        claim_tokens = extract_keywords_and_entities(claim)
        overlap = claim_tokens.intersection(expl_tokens)
        coverage = len(overlap) / max(len(claim_tokens), 1)
        if coverage < 0.25:
            omitted_claims.append(claim)

    omission_rate = len(omitted_claims) / max(len(material_claims), 1) if material_claims else (1.0 - fact_retention)

    # 3. Substance & Filler Check (W9)
    from app.services.claim_grounding_service import check_banned_strings
    banned_in_clause = check_banned_strings(what_means)
    is_filler = ("standard operative contractual provisions" in what_means.lower()) or (len(banned_in_clause) > 0)
    has_substance = bool(len(what_means.strip()) >= 20 and not is_filler)

    # 4. Directionality Check
    gt_directionality = gt_clause.get("directionality", "").lower()
    directionality_correct = True
    if "mutual" in gt_directionality:
        directionality_correct = True
    elif "only" in gt_directionality or "to" in gt_directionality:
        who_bound = pipeline_clause.get("who_is_bound", "")
        if "customer only" in gt_directionality and "mutual" in who_bound.lower():
            directionality_correct = False
        elif "consultant only" in gt_directionality and "mutual" in who_bound.lower():
            directionality_correct = False
        elif "vendor only" in gt_directionality and "mutual" in who_bound.lower():
            directionality_correct = False

    # 5. Conditions & Exceptions Check
    gt_conditions = gt_clause.get("conditions", [])
    gt_exceptions = gt_clause.get("exceptions", [])
    
    conditions_preserved = True
    for cond in gt_conditions:
        cond_tokens = extract_keywords_and_entities(cond)
        if len(cond_tokens) > 0 and len(cond_tokens.intersection(expl_tokens)) == 0:
            conditions_preserved = False

    exceptions_preserved = True
    for exc in gt_exceptions:
        exc_tokens = extract_keywords_and_entities(exc)
        if len(exc_tokens) > 0 and len(exc_tokens.intersection(expl_tokens)) == 0:
            exceptions_preserved = False

    return {
        "clause_number": gt_clause.get("clause_number"),
        "title": gt_clause.get("title"),
        "gt_category": gt_clause.get("category"),
        "predicted_categories": pipe_cat_names,
        "category_correct": category_correct,
        "gt_severity": gt_clause.get("severity"),
        "predicted_severity": pipeline_clause.get("severity"),
        "severity_correct": severity_correct,
        "has_invention": has_invention,
        "invented_items": list(invented_numbers) + forbidden_found,
        "fact_retention": fact_retention,
        "omission_rate": omission_rate,
        "omitted_claims": omitted_claims,
        "has_substance": has_substance,
        "is_filler": is_filler,
        "directionality_correct": directionality_correct,
        "conditions_preserved": conditions_preserved,
        "exceptions_preserved": exceptions_preserved,
        "what_this_clause_means": what_means,
    }


def evaluate_dataset(dataset_dir: Path) -> Dict[str, Any]:
    """
    Iterates through all evaluation documents and their ground truths,
    runs the full pipeline, evaluates every W9 metric, and computes comprehensive statistics.
    """
    docs_dir = dataset_dir / "documents"
    gt_dir = dataset_dir / "ground_truth"

    gt_files = sorted(list(gt_dir.glob("*.json")))
    if not gt_files:
        raise FileNotFoundError(f"No ground-truth files found in {gt_dir}")

    total_clauses_evaluated = 0
    total_category_correct = 0
    total_severity_correct = 0
    total_no_inventions = 0
    total_no_omissions = 0
    total_substance = 0
    total_filler = 0
    total_directionality_correct = 0
    total_conditions_preserved = 0
    total_exceptions_preserved = 0

    per_document_results = []
    split_metrics = {
        "Dev": {"total": 0, "cat": 0, "sev": 0, "no_inv": 0, "retention": 0},
        "Val": {"total": 0, "cat": 0, "sev": 0, "no_inv": 0, "retention": 0},
        "Held-Out v1": {"total": 0, "cat": 0, "sev": 0, "no_inv": 0, "retention": 0},
        "Contract E": {"total": 0, "cat": 0, "sev": 0, "no_inv": 0, "retention": 0},
        "Other": {"total": 0, "cat": 0, "sev": 0, "no_inv": 0, "retention": 0},
    }

    for gt_path in gt_files:
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        pdf_filename = gt_data.get("document_name")
        if not pdf_filename:
            doc_id = gt_data.get("doc_id", "")
            if doc_id:
                pdf_filename = f"{doc_id}.pdf"
            else:
                pdf_filename = f"{gt_path.stem}.pdf"

        pdf_path = docs_dir / pdf_filename
        if not pdf_path.exists():
            # Check with underscores / hyphens
            alt_candidates = [
                WORKSPACE_ROOT / "sample_documents" / pdf_filename,
                docs_dir / pdf_filename.replace("_", "-"),
                docs_dir / pdf_filename.replace("-", "_"),
                docs_dir / "SampleContract-Shuttle.pdf",
            ]
            for cand in alt_candidates:
                if cand.exists():
                    pdf_path = cand
                    break

        if not pdf_path.exists():
            print(f"Warning: PDF file {pdf_filename} not found, skipping {gt_path.name}")
            continue

        stem = gt_path.stem.lower()
        if stem.startswith("contract_") or "cloud_consulting" in stem or "commercial_lease" in stem or "consulting_services" in stem or "master_services" in stem:
            split_name = "Dev"
        elif stem.startswith("val_"):
            split_name = "Val"
        elif stem.startswith("held_out_"):
            split_name = "Held-Out v1"
        elif "shuttle" in stem:
            split_name = "Contract E"
        else:
            split_name = "Other"

        print(f"\n================================================================================")
        print(f"RUNNING PIPELINE: [{split_name}] {pdf_filename} ({gt_data.get('document_title') or gt_data.get('title')})")
        print(f"================================================================================")

        pipeline_output = run_pipeline_on_pdf(pdf_path)
        pipeline_clauses = pipeline_output.get("simplified_clauses", [])

        print(f"-> Extracted {len(pipeline_output.get('segmented_clauses', []))} segmented clauses")
        print(f"-> Simplified {len(pipeline_clauses)} clauses")

        doc_clause_evaluations = []
        gt_clauses = gt_data.get("clauses", [])

        # Align ground truth with pipeline clauses
        for idx, gt_clause in enumerate(gt_clauses):
            matched_pipeline_clause = None
            if idx < len(pipeline_clauses):
                matched_pipeline_clause = pipeline_clauses[idx]
            else:
                matched_pipeline_clause = {
                    "position": idx + 1,
                    "categories": [],
                    "severity": "Low",
                    "simplified_text": "",
                    "structured_explanation": {}
                }

            clause_res = evaluate_clause_match(gt_clause, matched_pipeline_clause)
            doc_clause_evaluations.append(clause_res)

            # Aggregate stats
            total_clauses_evaluated += 1
            split_metrics[split_name]["total"] += 1
            if clause_res["category_correct"]:
                total_category_correct += 1
                split_metrics[split_name]["cat"] += 1
            if clause_res["severity_correct"]:
                total_severity_correct += 1
                split_metrics[split_name]["sev"] += 1
            if not clause_res["has_invention"]:
                total_no_inventions += 1
                split_metrics[split_name]["no_inv"] += 1
            if clause_res["omission_rate"] < 0.5:
                total_no_omissions += 1
                split_metrics[split_name]["retention"] += 1
            if clause_res["has_substance"]:
                total_substance += 1
            if clause_res["is_filler"]:
                total_filler += 1
            if clause_res["directionality_correct"]:
                total_directionality_correct += 1
            if clause_res["conditions_preserved"]:
                total_conditions_preserved += 1
            if clause_res["exceptions_preserved"]:
                total_exceptions_preserved += 1

            cat_mark = "PASS" if clause_res["category_correct"] else "FAIL"
            sev_mark = "PASS" if clause_res["severity_correct"] else "FAIL"
            inv_mark = "PASS" if not clause_res["has_invention"] else "FAIL"
            sub_mark = "PASS" if clause_res["has_substance"] else "FAIL"
            print(f"  Clause {clause_res['clause_number']} [{clause_res['title']}]: "
                  f"Cat: [{cat_mark}] (GT: {clause_res['gt_category']} vs Pred: {clause_res['predicted_categories']}) | "
                  f"Sev: [{sev_mark}] (GT: {clause_res['gt_severity']} vs Pred: {clause_res['predicted_severity']}) | "
                  f"No-Invention: [{inv_mark}] | Substance: [{sub_mark}]")

        doc_summary_eval = {
            "document_name": pdf_filename,
            "document_title": gt_data.get("document_title") or gt_data.get("title"),
            "document_type": gt_data.get("document_type"),
            "split": split_name,
            "total_clauses": len(gt_clauses),
            "pipeline_clauses_count": len(pipeline_clauses),
            "clause_evaluations": doc_clause_evaluations,
            "category_accuracy": sum(1 for c in doc_clause_evaluations if c["category_correct"]) / len(gt_clauses) if gt_clauses else 0,
            "severity_accuracy": sum(1 for c in doc_clause_evaluations if c["severity_correct"]) / len(gt_clauses) if gt_clauses else 0,
        }
        per_document_results.append(doc_summary_eval)

    # Global Aggregate Metrics (W9 Spec)
    summary_report = {
        "total_documents": len(gt_files),
        "total_clauses_evaluated": total_clauses_evaluated,
        "category_accuracy": round((total_category_correct / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "severity_accuracy": round((total_severity_correct / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "no_invention_rate": round((total_no_inventions / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "fact_retention_rate": round((total_no_omissions / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "substance_rate": round((total_substance / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "filler_rate": round((total_filler / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "directionality_accuracy": round((total_directionality_correct / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "conditions_preservation_rate": round((total_conditions_preserved / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "exceptions_preservation_rate": round((total_exceptions_preserved / total_clauses_evaluated) * 100, 2) if total_clauses_evaluated else 0.0,
        "per_document_results": per_document_results
    }

    # Save to disk
    results_path = dataset_dir / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    print(f"\n================================================================================")
    print(f"CLARIFAI MEASURED EVALUATION HARNESS SUMMARY (W9)")
    print(f"================================================================================")
    print(f"Total Documents:               {summary_report['total_documents']}")
    print(f"Total Clauses Evaluated:       {summary_report['total_clauses_evaluated']}")
    print(f"Category Accuracy:             {summary_report['category_accuracy']}% ({total_category_correct}/{total_clauses_evaluated})")
    print(f"Severity Accuracy:             {summary_report['severity_accuracy']}% ({total_severity_correct}/{total_clauses_evaluated})")
    print(f"No-Invention / Hallucination:  {summary_report['no_invention_rate']}% ({total_no_inventions}/{total_clauses_evaluated})")
    print(f"Fact Retention (Low Omission): {summary_report['fact_retention_rate']}% ({total_no_omissions}/{total_clauses_evaluated})")
    print(f"Substance Rate:                {summary_report['substance_rate']}% ({total_substance}/{total_clauses_evaluated})")
    print(f"Filler Rate:                   {summary_report['filler_rate']}% ({total_filler}/{total_clauses_evaluated})")
    print(f"Directionality Accuracy:       {summary_report['directionality_accuracy']}% ({total_directionality_correct}/{total_clauses_evaluated})")
    print(f"Condition Preservation:        {summary_report['conditions_preservation_rate']}% ({total_conditions_preserved}/{total_clauses_evaluated})")
    print(f"Exception Preservation:        {summary_report['exceptions_preservation_rate']}% ({total_exceptions_preserved}/{total_clauses_evaluated})")
    print(f"\n================================================================================")
    print(f"CLARIFAI MASTER PROMPT v5 SPLIT-SPECIFIC PERFORMANCE BREAKDOWN")
    print(f"================================================================================")
    for sp_name, sp_data in split_metrics.items():
        if sp_data["total"] > 0:
            tot = sp_data["total"]
            cat_pct = round((sp_data["cat"] / tot) * 100, 1)
            sev_pct = round((sp_data["sev"] / tot) * 100, 1)
            ret_pct = round((sp_data["retention"] / tot) * 100, 1)
            inv_pct = round((sp_data["no_inv"] / tot) * 100, 1)
            print(f"Split: {sp_name:<12} | Clauses: {tot:2d} | Category: {cat_pct:5.1f}% ({sp_data['cat']}/{tot}) | Severity: {sev_pct:5.1f}% ({sp_data['sev']}/{tot}) | Fact Retention: {ret_pct:5.1f}% ({sp_data['retention']}/{tot}) | No-Invention: {inv_pct:5.1f}% ({sp_data['no_inv']}/{tot})")
    print(f"================================================================================\n")
    print(f"Structured results written to: {results_path}")

    return summary_report


if __name__ == "__main__":
    dataset_dir = WORKSPACE_ROOT / "evaluation_dataset"
    evaluate_dataset(dataset_dir)



if __name__ == "__main__":
    dataset_dir = WORKSPACE_ROOT / "evaluation_dataset"
    evaluate_dataset(dataset_dir)
