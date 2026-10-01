import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

# 1. Login
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "audit_user@clarifai.io", "password": "Password123!"}
)
print("Login Status:", login_resp.status_code)
if login_resp.status_code != 200:
    print("Login failed:", login_resp.text)
    exit(1)

auth_data = login_resp.json()
tokens = auth_data.get("tokens", {}) or auth_data
access_token = tokens.get("access")
headers = {"Authorization": f"Bearer {access_token}"}

# 2. Upload Document B
pdf_path = Path("sample_documents/golden_lease_deed.pdf")
with open(pdf_path, "rb") as f:
    files = {"file": ("golden_lease_deed.pdf", f, "application/pdf")}
    upload_resp = requests.post(f"{BASE_URL}/documents/", headers=headers, files=files)

print("Upload Status:", upload_resp.status_code)
print("Upload Response:", upload_resp.json())
doc_id = upload_resp.json().get("document_id") or upload_resp.json().get("id")
print("Document ID:", doc_id)

# 3. Poll for processing completion
print("\nWaiting for document processing...")
for attempt in range(60):
    time.sleep(2)
    doc_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/", headers=headers)
    data = doc_resp.json()
    status = data.get("status")
    print(f"Polling [{attempt+1}]: Status = {status}")
    if status in ["complete", "completed", "failed"]:
        break

print("\nFinal Document Processing Status:", data.get("status"))

# 4. Fetch Summary & Clauses
summary_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/summary/", headers=headers)
sum_data = summary_resp.json()
print("\n=== EXECUTIVE SUMMARY ===")
print("Purpose:    ", sum_data.get("purpose") or sum_data.get("purpose_text"))
print("Key Risks:  ", sum_data.get("key_risks") or sum_data.get("key_risks_text"))
print("Key Terms:  ", sum_data.get("key_terms") or sum_data.get("key_terms_text"))
print("Obligations:", sum_data.get("obligations") or sum_data.get("obligations_text"))

clauses_resp = requests.get(f"{BASE_URL}/documents/{doc_id}/clauses/", headers=headers)
clauses_data = clauses_resp.json()
clauses = clauses_data.get("results") or clauses_data.get("clauses") or clauses_data
print(f"\n=== PROCESSED CLAUSES ({len(clauses)}) ===")
for c in clauses:
    print(f"\n--- Clause {c.get('position')}: {c.get('title')} ---")
    print("Category:  ", c.get("category"))
    print("Severity:  ", c.get("severity"))
    print("Risk Source:", c.get("risk_source"))
    print("Simplified:", c.get("simplified_text"))
    print("Structured Explanation:", json.dumps(c.get("structured_explanation"), indent=2))
