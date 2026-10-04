from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.risk_service import classify_document_clauses_risk

doc_text = """SOFTWARE CONSULTING AND LICENSE SERVICES
AGREEMENT

This Software Consulting and License Services Agreement (the "Agreement") is entered into as of November 3, 2026 (the "Effective Date"), by and between Northbridge Analytics Inc., a Delaware corporation ("Client"), and Summit Ridge Consulting LLC, a California limited liability company ("Consultant"), collectively referred to as the "Parties."

1. SERVICES
Consultant shall provide software architecture consulting, data pipeline development, and related technical advisory services (the "Services") as described in one or more Statements of Work executed by both Parties under this Agreement.

2. FEES AND PAYMENT
Client shall pay all undisputed invoices within thirty (30) days of the invoice date. In the event any invoice remains unpaid beyond the due date, Client shall be charged interest at the rate of 1.5% per month on the outstanding balance until paid in full.

3. CONFIDENTIALITY
Each Party agrees to protect the other Party's confidential and proprietary information using the same degree of care it uses to protect its own confidential information, and in no event less than reasonable care, and shall not disclose such information to any third party without the prior written consent of the disclosing Party, except as required by law.

4. INTELLECTUAL PROPERTY
Any code, algorithms, documentation, or other deliverables created by Consultant in the course of performing the Services hereunder shall be deemed a work made for hire under applicable copyright law, and Client shall own all right, title and interest in and to such deliverables upon payment in full.

5. INDEMNIFICATION
Consultant shall defend, indemnify, and hold harmless Client, its officers, directors, employees, and affiliates from and against any and all third-party claims, damages, liabilities, and expenses (including reasonable attorneys' fees) arising out of Consultant's gross negligence, willful misconduct, or infringement of a third party's intellectual property rights in connection with the Services.

6. LIMITATION OF LIABILITY
Except for liabilities arising from a breach of Section 5 (Indemnification) or Section 3 (Confidentiality) above, each Party's total liability under this Agreement shall not exceed the total fees paid by Client in the six (6) months preceding the event giving rise to the claim.

7. TERM AND RENEWAL
This Agreement shall commence on the Effective Date and continue for an initial term of one (1) year, and shall automatically renew for successive one-year periods unless either Party provides written notice of non-renewal at least ninety (90) days prior to the end of the then-current term.

8. TERMINATION
Either Party may terminate this Agreement for convenience upon forty-five (45) days' prior written notice to the other Party. Either Party may terminate immediately upon written notice if the other Party materially breaches this Agreement and fails to cure such breach within fifteen (15) days of receiving notice thereof.

9. DISPUTE RESOLUTION
The Parties agree that any dispute, controversy, or claim arising out of or relating to this Agreement shall be resolved exclusively through binding arbitration administered by the American Arbitration Association in accordance with its Commercial Arbitration Rules, and each Party hereby waives its right to a jury trial with respect to any such dispute.

10. NON-SOLICITATION
During the term of this Agreement and for a period of twelve (12) months thereafter, neither Party shall directly or indirectly solicit for employment or engage as a contractor any employee of the other Party who was materially involved in the performance of this Agreement, without the prior written consent of the other Party.

11. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of the State of California, without regard to its conflict of laws principles.

12. ENTIRE AGREEMENT
This Agreement, together with any Statements of Work executed hereunder, constitutes the entire agreement between the Parties with respect to its subject matter and supersedes all prior or contemporaneous understandings, whether written or oral.

IN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date first written above.

NORTHBRIDGE ANALYTICS INC. SUMMIT RIDGE CONSULTING LLC
"""

cl = clean_legal_text(doc_text)
print("Cleaned text rules:", cl["rules_applied"])
seg = segment_document_clauses(cl["cleaned_text"])
print(f"Segmented clauses count: {len(seg['clauses'])}")
cats = categorize_clause_records(seg["clauses"])
print(f"Categorized clauses count: {len(cats['clauses'])}")
rsk = classify_document_clauses_risk(cats["clauses"])
print(f"Risk classified clauses count: {len(rsk['clauses'])}")

for i, c in enumerate(rsk["clauses"]):
    print(f"[{i+1}] #{c.get('clause_number')}: {c.get('title')} | Cat: {c.get('category')} | Severity: {c.get('severity')}")
