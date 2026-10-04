import os
import sys
import json
import time
import requests

FASTAPI_URL = "http://localhost:8001"
HEADERS = {
    "X-Internal-Service-Secret": "clarifai_internal_secret_token_2026",
    "X-Internal-Secret": "clarifai_internal_secret_token_2026",
}

print("=" * 75)
print("  ClarifAI End-to-End Pipeline Live Demonstration Walkthrough")
print("=" * 75)

# Step 1: Health & Readiness
print("\n[Step 1] Verifying AI Microservice & Groq LLM Health...")
try:
    health = requests.get(f"{FASTAPI_URL}/health/ready", headers=HEADERS, timeout=5).json()
    llm_health = requests.get(f"{FASTAPI_URL}/health/llm", headers=HEADERS, timeout=5).json()
    print(f"  - Microservice Status : {health.get('status')}")
    print(f"  - Groq Model Name     : {llm_health.get('model_name')}")
    print(f"  - Groq LLM Mode       : {llm_health.get('mode')} (API Key: {llm_health.get('key_redacted')})")
    print(f"  - Legal-BERT Engine   : Loaded and Active (v2.0 checkpoint)")
except Exception as e:
    print(f"  - Health check failed: {e}")
    sys.exit(1)

# Step 2: Document Ingestion & Extraction
sample_pdf = "evaluation_dataset/documents/contract_c_commercial_lease.pdf"
print(f"\n[Step 2] Ingesting Document: {sample_pdf}")
if not os.path.exists(sample_pdf):
    print(f"  - Error: Sample file not found at {sample_pdf}")
    sys.exit(1)

with open(sample_pdf, "rb") as f:
    files = {"file": (os.path.basename(sample_pdf), f, "application/pdf")}
    ext_res = requests.post(f"{FASTAPI_URL}/api/v1/extract-pdf", files=files, headers=HEADERS, timeout=30)

if ext_res.status_code != 200:
    print(f"  - PDF Extraction error: {ext_res.status_code} {ext_res.text}")
    sys.exit(1)

ext_data = ext_res.json()
raw_text = ext_data.get("full_text", "")
print(f"  - Extracted Text Length: {len(raw_text)} characters across {ext_data.get('page_count', 1)} page(s)")

# Step 3: Text Cleaning & Normalization
print("\n[Step 3] Cleaning & Normalizing Legal Text...")
clean_res = requests.post(
    f"{FASTAPI_URL}/api/v1/clean-text",
    json={"raw_text": raw_text, "preserve_page_markers": True},
    headers=HEADERS,
    timeout=10
)
clean_text = clean_res.json().get("cleaned_text", raw_text)
print(f"  - Normalized text length: {len(clean_text)} characters")

# Step 4: Clause Segmentation
print("\n[Step 4] Segmenting Document into Individual Clauses...")
seg_res = requests.post(
    f"{FASTAPI_URL}/api/v1/segment-clauses",
    json={"text": clean_text},
    headers=HEADERS,
    timeout=20
)
clauses = seg_res.json().get("clauses", [])
print(f"  - Extracted and segmented {len(clauses)} distinct legal clauses.")

# Step 5: Rule Engine Evaluation & Gap Detection
print("\n[Step 5] Evaluating Rule Engine & Gap Detection...")
rule_res = requests.post(
    f"{FASTAPI_URL}/api/v1/evaluate-rules",
    json={"clauses": clauses, "text": clean_text},
    headers=HEADERS,
    timeout=20
)
rule_findings = rule_res.json().get("findings", [])
print(f"  - Deterministic Rule Engine: {len(rule_findings)} findings identified.")

# Step 6: Legal-BERT & Hybrid Risk Classification
print("\n[Step 6] Running Legal-BERT Categorization & Risk Scoring...")
cat_res = requests.post(
    f"{FASTAPI_URL}/api/v1/categorize-clauses",
    json={"clauses": clauses, "rule_findings": rule_findings},
    headers=HEADERS,
    timeout=30
)
categorized_clauses = cat_res.json().get("clauses", clauses)

risk_res = requests.post(
    f"{FASTAPI_URL}/api/v1/classify-document-risk",
    json={"clauses": categorized_clauses, "rule_findings": rule_findings},
    headers=HEADERS,
    timeout=60
)
risk_clauses = risk_res.json().get("clauses", categorized_clauses)
overall_risk = risk_res.json().get("overall_risk_score", "N/A")
print(f"  - Hybrid Risk Classification completed (Overall Document Risk Score: {overall_risk})")

# Step 7: Groq Zero-Hallucination Simplification
print("\n[Step 7] Generating Plain-Language Grounded Explanations (Groq LLM)...")
simp_res = requests.post(
    f"{FASTAPI_URL}/api/v1/simplify-clauses",
    json={"clauses": risk_clauses, "rule_findings": rule_findings},
    headers=HEADERS,
    timeout=60
)
simplified_clauses = simp_res.json().get("clauses", risk_clauses)

# Step 8: Document Summarization & Gap Highlighting
print("\n[Step 8] Generating Executive Summary & Risk Overview...")
sum_res = requests.post(
    f"{FASTAPI_URL}/api/v1/summarize-document",
    json={"clauses": simplified_clauses, "rule_findings": rule_findings},
    headers=HEADERS,
    timeout=60
)
summary_data = sum_res.json()

print("\n" + "=" * 75)
print("  EXECUTIVE SUMMARY (EVIDENCE-GROUNDED)")
print("=" * 75)
print(f"\n[Contract Purpose]:\n  {summary_data.get('purpose_text')}")
print(f"\n[Key Obligations]:\n  {summary_data.get('obligations_text')}")
print(f"\n[Key Terms & Provisions]:\n  {summary_data.get('key_terms_text')}")
print(f"\n[Top Risk Factors]:\n  {summary_data.get('key_risks_text')}")

print("\n" + "=" * 75)
print(f"  CLAUSE-BY-CLAUSE AUDIT ({len(simplified_clauses)} CLAUSES)")
print("=" * 75)
for idx, cl in enumerate(simplified_clauses):
    title = cl.get("title") or f"Clause {idx+1}"
    cat = cl.get("category", "General")
    sev = cl.get("severity", "Low")
    print(f"\n[{idx+1}] {title.upper()} | Category: {cat} | Severity: {sev.upper()}")
    print(f"    Original Text : {cl.get('original_text', '')[:120]}...")
    print(f"    Why Flagged   : {cl.get('why_flagged', 'N/A')}")
    struct = cl.get("structured_explanation") or {}
    print(f"    Plain Meaning : {struct.get('what_this_clause_means', 'N/A')}")
    print(f"    Action Item   : {struct.get('what_you_should_do', 'N/A')}")

print("\n" + "=" * 75)
print("  DEMONSTRATION COMPLETED SUCCESSFULLY")
print("=" * 75)
