"""
Verification script for ClarifAI Hotfix on Contract E (SampleContract-Shuttle.pdf)
"""

import os
import sys
import json

# Reconfigure stdout to utf-8 for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django environment
sys.path.insert(0, os.path.abspath("backend/django-api"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from services.ai_client.client import RealAIClient

pdf_path = os.path.abspath("evaluation_dataset/documents/SampleContract-Shuttle.pdf")
print(f"Loading Contract E from: {pdf_path}")

client = RealAIClient()
res = client.process_document(
    document_id="contract_e_test",
    file_reference=pdf_path,
    user_id="test_user"
)

summary = res.get("summary", {})
clauses = res.get("clauses", [])

print("\n" + "=" * 80)
print(f"TOTAL CLAUSES EXTRACTED: {len(clauses)}")
print("=" * 80)

print("\n--- EXECUTIVE OVERVIEW ---")
print("Purpose Text:", summary.get("purpose_text") or summary.get("purpose"))
print("Blank template fields:", summary.get("blank_template_fields"))
print("Risk counts:", summary.get("risk_counts"))
print("Key figures:", json.dumps(summary.get("key_figures", []), indent=2))
print("Top risks:", json.dumps(summary.get("top_risks", []), indent=2))

print("\n--- CLAUSE DETAILS ---")
banned_templates = [
    "operative obligations governed under",
    "clause evaluated under category",
    "plain-english explanation exceeded echo threshold",
    "needs review: plain-english explanation"
]

llm_count = 0
limited_count = 0
empty_count = 0
banned_found = 0

high_clauses = []
mod_clauses = []
low_clauses = []
safe_clauses = []

for c in clauses:
    pos = c.get("position")
    title = c.get("title")
    cat = c.get("category")
    sev = (c.get("severity") or "").capitalize()
    plain = c.get("plain_language") or c.get("explanation") or ""
    mode = c.get("mode", "unknown")
    text = c.get("original_text", "")
    text_len = len(text)

    if mode.lower() == "llm":
        llm_count += 1
    else:
        limited_count += 1

    if text_len < 20:
        empty_count += 1

    if sev == "High":
        high_clauses.append((pos, title))
    elif sev == "Moderate":
        mod_clauses.append((pos, title))
    elif sev == "Safe":
        safe_clauses.append((pos, title))
    elif sev == "Low":
        low_clauses.append((pos, title))

    has_banned = any(b in plain.lower() for b in banned_templates)
    if has_banned:
        banned_found += 1

    print(f"\n[{pos}] {title}")
    print(f"  Category: {cat} | Severity: {sev} | Mode: {mode} | TextLen: {text_len}")
    print(f"  Explanation: {plain[:140]}...")
    if c.get("key_details"):
        print(f"  Details: {c.get('key_details')[:3]}")

print("\n" + "=" * 80)
print("HOTFIX VALIDATION SUMMARY:")
print(f"Total clauses: {len(clauses)} (Expected: 24)")
print(f"LLM mode: {llm_count}/24")
print(f"Limited mode: {limited_count}/24")
print(f"Empty text (<20 chars): {empty_count} (Expected: 0)")
print(f"Banned template phrases found: {banned_found} (Expected: 0)")
print(f"High risk clauses ({len(high_clauses)}): {[f'Section {p}' for p, _ in high_clauses]}")
print(f"Moderate risk clauses ({len(mod_clauses)}): {[f'Section {p}' for p, _ in mod_clauses]}")
print(f"Low risk clauses ({len(low_clauses)}): {[f'Section {p}' for p, _ in low_clauses]}")
print(f"Safe clauses ({len(safe_clauses)}): {[f'Section {p}' for p, _ in safe_clauses]}")
print("=" * 80)
