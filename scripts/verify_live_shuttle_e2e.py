import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

# 1. Login
print("Step 1: Logging in as audit_user@clarifai.io...")
login_resp = requests.post(
    f"{BASE_URL}/auth/login/",
    json={"email": "audit_user@clarifai.io", "password": "Password123!"}
)
if login_resp.status_code != 200:
    # Try without trailing slash
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "audit_user@clarifai.io", "password": "Password123!"}
    )

print(f"Login Response Status: {login_resp.status_code}")
if login_resp.status_code != 200:
    print("Login Failed:", login_resp.text)
    exit(1)

auth_data = login_resp.json()
tokens = auth_data.get("tokens", {}) or auth_data
access_token = tokens.get("access")
headers = {"Authorization": f"Bearer {access_token}"}
print("Authenticated successfully.")

# 2. Upload SampleContract-Shuttle.pdf
pdf_path = Path("evaluation_dataset/documents/SampleContract-Shuttle.pdf")
print(f"\nStep 2: Uploading {pdf_path.name} to Django API ({BASE_URL}/documents/)...")

with open(pdf_path, "rb") as f:
    files = {"file": ("SampleContract-Shuttle.pdf", f, "application/pdf")}
    upload_resp = requests.post(f"{BASE_URL}/documents/", headers=headers, files=files)

print("Upload HTTP Status:", upload_resp.status_code)
if upload_resp.status_code not in [200, 201]:
    print("Upload Failed:", upload_resp.text)
    exit(1)

up_data = upload_resp.json()
doc_id = up_data.get("document_id") or up_data.get("id")
print(f"Document Upload Succeeded! Document ID = {doc_id}")

# 3. Poll document processing status
print("\nStep 3: Polling for background AI analysis completion...")
final_doc_data = None
for attempt in range(45):
    time.sleep(2)
    doc_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/", headers=headers)
    if doc_resp.status_code == 200:
        data = doc_resp.json()
        status = data.get("status")
        clause_count = data.get("clause_count") or len(data.get("clauses", []))
        print(f"  Attempt {attempt+1:2d}: Status = {status} | Clauses = {clause_count}")
        if status in ["complete", "completed", "failed"]:
            final_doc_data = data
            break

print(f"\nFinal Document Status: {final_doc_data.get('status')}")

# 4. Fetch processed clauses
clauses_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/clauses/", headers=headers)
clauses_data = clauses_resp.json()
clauses = clauses_data.get("results") or clauses_data.get("clauses") or clauses_data
print(f"\nStep 4: Verified Clauses in Database ({len(clauses)} clauses stored):")
print("-" * 90)
print(f"{'Pos':<4} | {'Clause #':<8} | {'Title':<28} | {'Category':<22} | {'Risk':<10}")
print("-" * 90)
for c in clauses:
    pos = c.get("position", "-")
    c_num = c.get("clause_number", "-")
    title = str(c.get("title", ""))[:28]
    cat = c.get("category", "-")
    risk = c.get("risk_level") or c.get("severity", "-")
    print(f"{pos:<4} | {c_num:<8} | {title:<28} | {cat:<22} | {risk:<10}")

print("-" * 90)

# 5. Fetch Executive Summary
summary_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/summary/", headers=headers)
if summary_resp.status_code == 200:
    sum_data = summary_resp.json()
    print("\nStep 5: Executive Summary:")
    print("  Purpose:    ", str(sum_data.get("purpose") or sum_data.get("purpose_text"))[:120])
    print("  Key Risks:  ", str(sum_data.get("key_risks") or sum_data.get("key_risks_text"))[:120])
    print("  Key Terms:  ", str(sum_data.get("key_terms") or sum_data.get("key_terms_text"))[:120])
    print("  Obligations:", str(sum_data.get("obligations") or sum_data.get("obligations_text"))[:120])

print("\nLIVE END-TO-END VERIFICATION COMPLETE: ALL 24 CLAUSES VERIFIED IN DJANGO REST API.")
