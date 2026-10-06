"""
Run full pipeline sweep across unseen contracts and Contract E.
Captures raw counts for tabular presentation.
"""

import os
import sys
import json
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath("backend/django-api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from services.ai_client.client import RealAIClient

DOCS_DIR = os.path.abspath("evaluation_dataset/documents")

# Selected contracts: Contract E (uploaded PDF) + 3 unseen contracts (not held_out_1)
contracts_to_test = [
    {
        "name": "Contract E (Shuttle Professional Services)",
        "path": os.path.join(DOCS_DIR, "SampleContract-Shuttle.pdf"),
        "doc_id": "test_contract_e"
    },
    {
        "name": "Unseen Contract 1 (Employment Agreement)",
        "path": os.path.join(DOCS_DIR, "new_doc_1_employment_agreement.pdf"),
        "doc_id": "test_unseen_1"
    },
    {
        "name": "Unseen Contract 2 (Commercial Loan Agreement)",
        "path": os.path.join(DOCS_DIR, "new_doc_2_commercial_loan_agreement.pdf"),
        "doc_id": "test_unseen_2"
    },
    {
        "name": "Unseen Contract 3 (SaaS Terms of Service)",
        "path": os.path.join(DOCS_DIR, "new_doc_3_saas_terms_of_service.pdf"),
        "doc_id": "test_unseen_3"
    },
    {
        "name": "Unseen Contract 4 (Supplier Agreement)",
        "path": os.path.join(DOCS_DIR, "new_doc_4_lettered_supplier_agreement.pdf"),
        "doc_id": "test_unseen_4"
    }
]

banned_templates = [
    "plain-english explanation unavailable",
    "operative obligations governed under",
    "clause evaluated under category",
    "plain-english explanation exceeded echo threshold",
    "needs review: plain-english explanation"
]

client = RealAIClient()
results = []

for c_meta in contracts_to_test:
    name = c_meta["name"]
    p = c_meta["path"]
    doc_id = c_meta["doc_id"]
    print(f"\nProcessing: {name} ({os.path.basename(p)})...")
    
    if not os.path.exists(p):
        print(f"File not found: {p}")
        continue

    try:
        res = client.process_document(
            document_id=doc_id,
            file_reference=p,
            user_id="test_runner"
        )
    except Exception as e:
        print(f"Error processing {name}: {e}")
        continue

    summary = res.get("summary", {})
    clauses = res.get("clauses", [])

    total_clauses = len(clauses)
    high_count = sum(1 for cl in clauses if str(cl.get("severity", "")).lower() == "high")
    mod_count = sum(1 for cl in clauses if str(cl.get("severity", "")).lower() in ("moderate", "medium"))
    low_count = sum(1 for cl in clauses if str(cl.get("severity", "")).lower() == "low")
    safe_count = sum(1 for cl in clauses if str(cl.get("severity", "")).lower() == "safe")

    empty_count = sum(1 for cl in clauses if len(cl.get("original_text", "").strip()) < 20)
    
    banned_found = 0
    categories_set = set()
    for cl in clauses:
        plain = (cl.get("plain_language") or cl.get("explanation") or "").lower()
        if any(b in plain for b in banned_templates):
            banned_found += 1
        cat = cl.get("category")
        if cat:
            categories_set.add(cat)

    llm_modes = sum(1 for cl in clauses if str(cl.get("mode", "")).lower() == "llm")
    limited_modes = sum(1 for cl in clauses if str(cl.get("mode", "")).lower() != "llm")

    res_record = {
        "name": name,
        "filename": os.path.basename(p),
        "total_clauses": total_clauses,
        "high": high_count,
        "moderate": mod_count,
        "low": low_count,
        "safe": safe_count,
        "empty_count": empty_count,
        "banned_count": banned_found,
        "categories_count": len(categories_set),
        "categories": sorted(list(categories_set)),
        "llm_modes": llm_modes,
        "limited_modes": limited_modes,
        "purpose": summary.get("purpose_text") or summary.get("purpose", "")[:80]
    }
    results.append(res_record)
    print(f"  -> Clauses: {total_clauses} | High: {high_count} | Mod: {mod_count} | Low: {low_count} | Safe: {safe_count} | Safe > 0: {safe_count > 0} | Banned: {banned_found}")

print("\n" + "=" * 90)
print("FINAL RESULTS TABLE")
print("=" * 90)
print(f"{'Contract Name':<42} | {'Total':<5} | {'High':<4} | {'Mod':<4} | {'Low':<4} | {'Safe':<4} | {'Empty':<5} | {'Banned':<6}")
print("-" * 90)
for r in results:
    print(f"{r['name']:<42} | {r['total_clauses']:<5} | {r['high']:<4} | {r['moderate']:<4} | {r['low']:<4} | {r['safe']:<4} | {r['empty_count']:<5} | {r['banned_count']:<6}")
print("=" * 90)

# Save JSON results for easy inspection
with open("sweep_unseen_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("Saved details to sweep_unseen_results.json")
