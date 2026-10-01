import requests
import time
import json
import io
import re
from pathlib import Path
import pypdf

BASE_URL = "http://localhost:8000/api"

# 1. Login or Signup
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "audit_user@clarifai.io", "password": "Password123!"}
)
if login_resp.status_code != 200:
    signup_resp = requests.post(
        f"{BASE_URL}/auth/signup",
        json={"email": "audit_user@clarifai.io", "password": "Password123!", "full_name": "Audit User"}
    )
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "audit_user@clarifai.io", "password": "Password123!"}
    )

auth_data = login_resp.json()
tokens = auth_data.get("tokens", {}) or auth_data
access_token = tokens.get("access")
headers = {"Authorization": f"Bearer {access_token}"}

sample_docs = [
    "Document_A_SaaS_Service_Agreement.pdf",
    "Document_B_Consulting_Services_Agreement.pdf",
    "Sample_Master_Services_Agreement.pdf",
    "Sample_Non_Disclosure_Agreement.pdf",
    "golden_lease_deed.pdf"
]

results_summary = []

for filename in sample_docs:
    pdf_path = Path(f"sample_documents/{filename}")
    if not pdf_path.exists():
        print(f"Skipping missing file: {filename}")
        continue
    
    print(f"\n========================================================")
    print(f"PROCESSING LIVE: {filename}")
    print(f"========================================================")
    
    with open(pdf_path, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        upload_resp = requests.post(f"{BASE_URL}/documents/", headers=headers, files=files)
    
    if upload_resp.status_code not in [200, 201]:
        print(f"Upload failed for {filename}: {upload_resp.text}")
        continue
        
    doc_id = upload_resp.json().get("document_id") or upload_resp.json().get("id")
    print(f"Uploaded {filename} -> Doc ID: {doc_id}")
    
    # Poll for completion
    for attempt in range(60):
        time.sleep(2)
        doc_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/", headers=headers)
        status = doc_resp.json().get("status")
        if status in ["complete", "completed", "failed"]:
            break
            
    final_status = doc_resp.json().get("status")
    print(f"Processing Result for {filename}: {final_status}")
    
    # Fetch Clauses from API
    clauses_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/clauses/", headers=headers)
    clauses_data = clauses_resp.json()
    clauses = clauses_data.get("results") or clauses_data.get("clauses") or clauses_data
    
    # Generate & Download PDF report
    report_gen_resp = requests.post(f"{BASE_URL}/documents/{doc_id}/report/", headers=headers)
    report_down_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/report/download/", headers=headers)
    
    pdf_text = ""
    if report_down_resp.status_code == 200:
        pdf_reader = pypdf.PdfReader(io.BytesIO(report_down_resp.content))
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() or ""
        print(f"PDF Export Downloaded ({len(report_down_resp.content)} bytes, {len(pdf_reader.pages)} pages).")
    else:
        print(f"PDF Report Download status: {report_down_resp.status_code}")
        
    # Clause validations
    doc_clauses_info = []
    has_unknown = False
    has_general = False
    has_numeric_cat_evidence = False
    
    for c in clauses:
        pos = c.get("position")
        cat = c.get("category")
        sev = c.get("severity")
        simp = c.get("simplified_text") or ""
        struct = c.get("structured_explanation") or {}
        
        cat_ev = struct.get("category", {}).get("evidence") if isinstance(struct.get("category"), dict) else None
        risk_ev = struct.get("risk", {}).get("evidence") if isinstance(struct.get("risk"), dict) else None
        
        if sev == "UNKNOWN" or (isinstance(struct.get("risk"), dict) and struct.get("risk", {}).get("severity") == "UNKNOWN"):
            has_unknown = True
        if cat == "General" or (isinstance(struct.get("category"), dict) and struct.get("category", {}).get("label") == "General"):
            has_general = True
        if cat_ev and (cat_ev.isdigit() or re.match(r'^\W*\d+\W*$', cat_ev)):
            has_numeric_cat_evidence = True
            
        doc_clauses_info.append({
            "pos": pos,
            "category": cat,
            "severity": sev,
            "cat_evidence": cat_ev,
            "risk_evidence": risk_ev,
            "what_this_clause_means": struct.get("what_this_clause_means"),
            "warnings": struct.get("grounding_warnings", [])
        })
        
    results_summary.append({
        "filename": filename,
        "doc_id": doc_id,
        "status": final_status,
        "clause_count": len(clauses),
        "has_unknown": has_unknown,
        "has_general": has_general,
        "has_numeric_cat_evidence": has_numeric_cat_evidence,
        "clauses": doc_clauses_info,
        "pdf_text_sample": pdf_text[:1200]
    })

print("\n\n========================================================")
print("FINAL AUDIT SUMMARY ACROSS ALL 5 DOCUMENTS:")
print("========================================================")
for r in results_summary:
    print(f"\nDocument: {r['filename']} (ID: {r['doc_id']})")
    print(f"  Status: {r['status']}, Clauses: {r['clause_count']}")
    print(f"  Has 'UNKNOWN' Severity: {r['has_unknown']}")
    print(f"  Has 'General' Category: {r['has_general']}")
    print(f"  Has Numeric Cat Evidence (Bug A): {r['has_numeric_cat_evidence']}")
    for c in r["clauses"]:
        print(f"    Clause {c['pos']}: Category='{c['category']}', Severity='{c['severity']}'")
        print(f"      Cat Evidence: '{c['cat_evidence']}'")
        print(f"      What Means:   '{c['what_this_clause_means']}'")
        if c["warnings"]:
            print(f"      Warnings:     {c['warnings']}")

with open("scripts/audit_live_results.json", "w", encoding="utf-8") as out:
    json.dump(results_summary, out, indent=2)
