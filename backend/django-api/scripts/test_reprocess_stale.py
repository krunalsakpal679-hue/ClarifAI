"""
Helper script to populate 3 stale documents in test DB and verify reprocess_stale_documents management command.
"""
import os
import sys
import django
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "c:/ClarifAI- AIPipeline/backend/django-api")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentStatus, Clause, ClauseStatus, DocumentSummary
from django.core.management import call_command

User = get_user_model()
user, _ = User.objects.get_or_create(email="testuser@example.com")

# Define 3 historical test documents processed before Phase 1 with old defaults (e.g. severity="safe", category="General", structured_explanation=None)
test_docs_data = [
    {
        "filename": "historical_msa_contract.pdf",
        "file_ref": "c:/ClarifAI- AIPipeline/sample_documents/Sample_Master_Services_Agreement.pdf",
        "clauses": [
            ("2. PAYMENT AND FEES Customer shall remit payment within thirty (30) days.", "safe", "Payment"),
            ("5. INDEMNIFICATION Vendor agrees to defend, indemnify, and hold harmless Customer against all third-party claims.", "safe", "General"),
            ("6. LIMITATION OF LIABILITY In no event shall aggregate liability exceed $1,000.", "safe", "General"),
        ]
    },
    {
        "filename": "historical_consulting_agreement.pdf",
        "file_ref": "c:/ClarifAI- AIPipeline/sample_documents/Document_B_Consulting_Services_Agreement.pdf",
        "clauses": [
            ("4. INDEMNITY OBLIGATIONS Consultant agrees to defend and indemnify Client against all claims.", "safe", "General"),
            ("5. AGGREGATE LIABILITY CAP Total liability of consultant shall in no event exceed fees paid.", "safe", "General"),
            ("7. CONFIDENTIALITY COVENANT Each party shall hold all non-public technical data in confidence.", "safe", "General"),
        ]
    },
    {
        "filename": "historical_nda_agreement.pdf",
        "file_ref": "c:/ClarifAI- AIPipeline/sample_documents/Sample_Non_Disclosure_Agreement.pdf",
        "clauses": [
            ("2. DEFINITION OF CONFIDENTIAL INFORMATION Proprietary and confidential trade secrets.", "safe", "General"),
            ("4. OBLIGATIONS & STANDARD OF CARE The Recipient agrees to protect Confidential Information.", "safe", "General"),
            ("5. NON-CIRCUMVENTION Recipient agrees not to circumvent or bypass Discloser.", "safe", "General"),
        ]
    }
]

past_timestamp = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)

created_docs = []
for doc_info in test_docs_data:
    doc, created = Document.objects.get_or_create(
        original_filename=doc_info["filename"],
        defaults={
            "user": user,
            "file_reference": doc_info["file_ref"],
            "status": DocumentStatus.COMPLETE,
        }
    )
    # Set historical uploaded_at
    Document.objects.filter(id=doc.id).update(uploaded_at=past_timestamp)
    doc.refresh_from_db()

    # Create old stale clauses (with old "safe" fallback, "General" category, and no structured_explanation)
    doc.clauses.all().delete()
    for idx, (c_text, old_sev, old_cat) in enumerate(doc_info["clauses"], start=1):
        Clause.objects.create(
            document=doc,
            position=idx,
            original_text=c_text,
            simplified_text=c_text,
            explanation="Old legacy explanation",
            structured_explanation=None,
            severity=old_sev,
            category=old_cat,
            risk_source=None,
            status=ClauseStatus.COMPLETE
        )
    created_docs.append(doc)

print("=" * 80)
print("PART 3: STALE DATA CLEANUP VERIFICATION (3 HISTORICAL DOCUMENTS)")
print("=" * 80)

print("\n--- BEFORE REPROCESSING (LEGACY / STALE STATE) ---")
for doc in created_docs:
    print(f"\nDocument: {doc.original_filename} (ID: {doc.id}) | Uploaded: {doc.uploaded_at.isoformat()}")
    for c in doc.clauses.order_by('position'):
        print(f"  Clause {c.position}: Category='{c.category}', Severity='{c.severity}', RiskSource={c.risk_source}, StructuredExplanation={c.structured_explanation}")

# Run dry run command
print("\n--- RUNNING MANAGEMENT COMMAND (DRY RUN) ---")
call_command("reprocess_stale_documents", dry_run=True)

# Run execute command inline
print("\n--- RUNNING MANAGEMENT COMMAND (EXECUTE INLINE) ---")
call_command("reprocess_stale_documents", execute=True, inline=True)

print("\n--- AFTER REPROCESSING (AUDITED / PERSISTED STATE) ---")
for doc in created_docs:
    doc.refresh_from_db()
    print(f"\nDocument: {doc.original_filename} (ID: {doc.id}) | Status: {doc.status}")
    for c in doc.clauses.order_by('position'):
        has_struct = bool(c.structured_explanation)
        struct_summary = "Populated (what_this_clause_means + risk + category evidence)" if has_struct else "None"
        print(f"  Clause {c.position}: Category='{c.category}', Severity='{c.severity}', RiskSource='{c.risk_source}', StructuredExplanation={struct_summary}")
