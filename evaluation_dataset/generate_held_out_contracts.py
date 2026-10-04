"""
Held-out Unseen Benchmark Dataset Generator & Evaluation Harness
Constructs 5 completely unseen, distinct legal contract archetypes with
strictly pre-defined ground truth annotations.
"""

import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = Path("evaluation_dataset/documents")
GT_DIR = Path("evaluation_dataset/ground_truth")

DOCS_DIR.mkdir(parents=True, exist_ok=True)
GT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Held-out Contracts Specifications and Ground Truth
HELD_OUT_DATA = [
    {
        "doc_id": "held_out_1_mutual_nda",
        "title": "MUTUAL NONDISCLOSURE AGREEMENT",
        "party_a": "Apex Dynamics Corp. (Disclosing Party)",
        "party_b": "Zenith AI Labs LLC (Receiving Party)",
        "reviewing_party": "Zenith AI Labs LLC",
        "clauses": [
            {
                "position": 1,
                "title": "1. SCOPE OF CONFIDENTIAL INFORMATION",
                "text": "1. SCOPE OF CONFIDENTIAL INFORMATION. Confidential Information encompasses all non-public technical and financial data disclosed by either party, provided it is marked confidential or reasonably understood as confidential.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 2,
                "title": "2. EXCLUSIONS FROM CONFIDENTIALITY",
                "text": "2. EXCLUSIONS FROM CONFIDENTIALITY. Confidential Information does not include information that is publicly known, already in the recipient's rightful possession without restriction, or independently developed without reference to the Disclosing Party's data.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Receiving Party",
                "gt_numbers": [],
                "gt_exceptions": ["publicly known", "rightful possession", "independently developed"]
            },
            {
                "position": 3,
                "title": "3. STANDARD OF CARE",
                "text": "3. STANDARD OF CARE. Each party shall protect the other's Confidential Information with the same degree of care it uses for its own confidential assets, but not less than reasonable care.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 4,
                "title": "4. COMPELLED DISCLOSURE",
                "text": "4. COMPELLED DISCLOSURE. If Receiving Party is required by valid court order or subpoena to disclose Confidential Information, it shall provide prompt written notice to Disclosing Party to enable protective orders.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Receiving Party",
                "gt_numbers": [],
                "gt_exceptions": ["court order", "subpoena"]
            },
            {
                "position": 5,
                "title": "5. TERM AND SURVIVAL",
                "text": "5. TERM AND SURVIVAL. This Agreement remains in effect for two (2) years, and nondisclosure obligations survive for three (3) years following termination, except trade secrets which survive indefinitely.",
                "gt_category": "Term",
                "gt_severity": "Medium",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["two (2) years", "three (3) years"],
                "gt_exceptions": ["trade secrets which survive indefinitely"]
            },
            {
                "position": 6,
                "title": "6. REMEDIES AND INJUNCTIVE RELIEF",
                "text": "6. REMEDIES AND INJUNCTIVE RELIEF. Unauthorized disclosure causes irreparable harm for which monetary damages are inadequate, entitling Disclosing Party to seek immediate injunctive relief without posting bond.",
                "gt_category": "Remedies",
                "gt_severity": "High",
                "gt_party_bound": "Receiving Party",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 7,
                "title": "7. GOVERNING LAW AND VENUE",
                "text": "7. GOVERNING LAW AND VENUE. This Agreement is governed by Delaware law, and all disputes must be brought exclusively in the state or federal courts located in New Castle County, Delaware.",
                "gt_category": "Governing Law",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": [],
                "gt_exceptions": []
            }
        ]
    },
    {
        "doc_id": "held_out_2_saas_service_level_agreement",
        "title": "ENTERPRISE SAAS AND SERVICE LEVEL AGREEMENT",
        "party_a": "NovaScale Cloud Systems Inc. (Provider)",
        "party_b": "Horizon Media Group LLC (Customer)",
        "reviewing_party": "Horizon Media Group LLC",
        "clauses": [
            {
                "position": 1,
                "title": "1. UPTIME COMMITMENT AND AVAILABILITY",
                "text": "1. UPTIME COMMITMENT AND AVAILABILITY. Provider warrants that the SaaS Platform shall achieve ninety-nine point nine percent (99.9%) system availability during each calendar month, excluding scheduled maintenance windows.",
                "gt_category": "Service Level Agreement (SLA)",
                "gt_severity": "Low",
                "gt_party_bound": "Provider",
                "gt_numbers": ["ninety-nine point nine percent (99.9%)"],
                "gt_exceptions": ["scheduled maintenance windows"]
            },
            {
                "position": 2,
                "title": "2. SCHEDULED MAINTENANCE NOTIFICATION",
                "text": "2. SCHEDULED MAINTENANCE NOTIFICATION. Provider shall provide at least seventy-two (72) hours advance electronic notice for all scheduled downtime, which shall occur only between 00:00 and 04:00 UTC on weekends.",
                "gt_category": "Service Level Agreement (SLA)",
                "gt_severity": "Low",
                "gt_party_bound": "Provider",
                "gt_numbers": ["seventy-two (72) hours"],
                "gt_exceptions": []
            },
            {
                "position": 3,
                "title": "3. SERVICE LEVEL CREDITS",
                "text": "3. SERVICE LEVEL CREDITS. If monthly uptime falls below ninety-nine percent (99.0%), Customer is entitled to a fifteen percent (15%) service credit applied against the subsequent monthly billing invoice.",
                "gt_category": "Payment",
                "gt_severity": "Medium",
                "gt_party_bound": "Provider",
                "gt_numbers": ["ninety-nine percent (99.0%)", "fifteen percent (15%)"],
                "gt_exceptions": []
            },
            {
                "position": 4,
                "title": "4. DATA PROTECTION AND SECURITY AUDITS",
                "text": "4. DATA PROTECTION AND SECURITY AUDITS. Provider shall maintain SOC 2 Type II compliance and encrypt all Customer data in transit and at rest using AES-256 encryption.",
                "gt_category": "Privacy",
                "gt_severity": "Low",
                "gt_party_bound": "Provider",
                "gt_numbers": ["AES-256"],
                "gt_exceptions": []
            },
            {
                "position": 5,
                "title": "5. UNILATERAL CUSTOMER INDEMNIFICATION",
                "text": "5. UNILATERAL CUSTOMER INDEMNIFICATION. Customer shall defend, indemnify, and hold harmless Provider from all third-party claims, liabilities, and legal fees arising from Customer's transmitted content.",
                "gt_category": "Indemnification",
                "gt_severity": "High",
                "gt_party_bound": "Customer only",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 6,
                "title": "6. AGGREGATE MONETARY LIABILITY CAP",
                "text": "6. AGGREGATE MONETARY LIABILITY CAP. Provider's total aggregate liability under this agreement is strictly capped at the total subscription fees paid by Customer during the prior twelve (12) months.",
                "gt_category": "Liability",
                "gt_severity": "High",
                "gt_party_bound": "Provider",
                "gt_numbers": ["twelve (12) months"],
                "gt_exceptions": []
            },
            {
                "position": 7,
                "title": "7. TERMINATION FOR CAUSE",
                "text": "7. TERMINATION FOR CAUSE. Either party may terminate immediately upon written notice if the other party commits a material breach and fails to cure within thirty (30) days of written demand.",
                "gt_category": "Termination",
                "gt_severity": "Medium",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["thirty (30) days"],
                "gt_exceptions": []
            }
        ]
    },
    {
        "doc_id": "held_out_3_equipment_lease_agreement",
        "title": "COMMERCIAL EQUIPMENT LEASE AGREEMENT",
        "party_a": "Precision Machinery Leasing LLC (Lessor)",
        "party_b": "Atlas Manufacturing Corp. (Lessee)",
        "reviewing_party": "Atlas Manufacturing Corp.",
        "clauses": [
            {
                "position": 1,
                "title": "1. LEASE TERM AND COMMENCEMENT",
                "text": "1. LEASE TERM AND COMMENCEMENT. Lessor leases to Lessee the industrial machinery listed in Exhibit A for an initial term of thirty-six (36) months commencing October 1, 2026.",
                "gt_category": "Term",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["thirty-six (36) months"],
                "gt_exceptions": []
            },
            {
                "position": 2,
                "title": "2. MONTHLY RENT AND SECURITY DEPOSIT",
                "text": "2. MONTHLY RENT AND SECURITY DEPOSIT. Lessee shall remit monthly rent of $5,400.00 on the first business day of each month, along with an upfront security deposit of $10,800.00.",
                "gt_category": "Payment",
                "gt_severity": "Medium",
                "gt_party_bound": "Lessee",
                "gt_numbers": ["$5,400.00", "$10,800.00"],
                "gt_exceptions": []
            },
            {
                "position": 3,
                "title": "3. MAINTENANCE AND REPAIR COVENANTS",
                "text": "3. MAINTENANCE AND REPAIR COVENANTS. Lessee assumes sole responsibility for all routine maintenance, preventative servicing, and repairs required to maintain the machinery in certified operating condition.",
                "gt_category": "Maintenance",
                "gt_severity": "Medium",
                "gt_party_bound": "Lessee",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 4,
                "title": "4. MANDATORY INSURANCE COVERAGE",
                "text": "4. MANDATORY INSURANCE COVERAGE. Lessee shall maintain commercial general liability insurance of not less than $2,000,000.00 per occurrence naming Lessor as an additional insured party.",
                "gt_category": "Insurance",
                "gt_severity": "Medium",
                "gt_party_bound": "Lessee",
                "gt_numbers": ["$2,000,000.00"],
                "gt_exceptions": []
            },
            {
                "position": 5,
                "title": "5. LESSOR INSPECTION RIGHTS",
                "text": "5. LESSOR INSPECTION RIGHTS. Lessor and its authorized agents may enter Lessee's premises during standard operating hours upon forty-eight (48) hours advance written notice to inspect the leased equipment.",
                "gt_category": "Audit / Inspection",
                "gt_severity": "Low",
                "gt_party_bound": "Lessee",
                "gt_numbers": ["forty-eight (48) hours"],
                "gt_exceptions": []
            },
            {
                "position": 6,
                "title": "6. UNRESTRICTED DEFAULT AND REPOSSESSION",
                "text": "6. UNRESTRICTED DEFAULT AND REPOSSESSION. Upon Lessee's failure to pay rent within ten (10) days of the due date, Lessor may repossess the equipment immediately without judicial process.",
                "gt_category": "Default / Remedies",
                "gt_severity": "Critical",
                "gt_party_bound": "Lessee",
                "gt_numbers": ["ten (10) days"],
                "gt_exceptions": []
            },
            {
                "position": 7,
                "title": "7. PROHIBITION OF ASSIGNMENT OR SUBLEASE",
                "text": "7. PROHIBITION OF ASSIGNMENT OR SUBLEASE. Lessee shall not assign, sublease, or pledge the equipment without Lessor's prior written consent, which Lessor may withhold at its sole discretion.",
                "gt_category": "Assignment",
                "gt_severity": "High",
                "gt_party_bound": "Lessee",
                "gt_numbers": [],
                "gt_exceptions": ["with Lessor's prior written consent"]
            }
        ]
    },
    {
        "doc_id": "held_out_4_executive_employment_agreement",
        "title": "EXECUTIVE EMPLOYMENT AND RESTRICTIVE COVENANTS",
        "party_a": "Solstice BioTech Corp. (Company)",
        "party_b": "Dr. Elena Vance (Executive)",
        "reviewing_party": "Dr. Elena Vance",
        "clauses": [
            {
                "position": 1,
                "title": "1. POSITION AND COMPENSATION",
                "text": "1. POSITION AND COMPENSATION. Company employs Executive as Chief Scientific Officer with an annual base salary of $275,000.00, payable in semi-monthly installments, plus eligibility for a performance bonus of up to 35%.",
                "gt_category": "Payment",
                "gt_severity": "Low",
                "gt_party_bound": "Company",
                "gt_numbers": ["$275,000.00", "35%"],
                "gt_exceptions": []
            },
            {
                "position": 2,
                "title": "2. NON-COMPETE RESTRICTION",
                "text": "2. NON-COMPETE RESTRICTION. For eighteen (18) months following termination, Executive shall not directly or indirectly engage with any competing biotechnology business within a one hundred (100) mile radius.",
                "gt_category": "Non-Compete",
                "gt_severity": "Critical",
                "gt_party_bound": "Executive only",
                "gt_numbers": ["eighteen (18) months", "one hundred (100) mile"],
                "gt_exceptions": []
            },
            {
                "position": 3,
                "title": "3. NON-SOLICITATION OF EMPLOYEES AND CLIENTS",
                "text": "3. NON-SOLICITATION OF EMPLOYEES AND CLIENTS. Executive covenants not to solicit or recruit any employee, contractor, or commercial customer of Company for twenty-four (24) months post-employment.",
                "gt_category": "Non-Solicitation",
                "gt_severity": "High",
                "gt_party_bound": "Executive only",
                "gt_numbers": ["twenty-four (24) months"],
                "gt_exceptions": []
            },
            {
                "position": 4,
                "title": "4. INTELLECTUAL PROPERTY ASSIGNMENT",
                "text": "4. INTELLECTUAL PROPERTY ASSIGNMENT. All discoveries, inventions, patents, and software conceived by Executive during employment vest entirely and irrevocably in Company as work made for hire.",
                "gt_category": "Intellectual Property",
                "gt_severity": "Medium",
                "gt_party_bound": "Executive only",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 5,
                "title": "5. TERMINATION WITHOUT CAUSE AND SEVERANCE",
                "text": "5. TERMINATION WITHOUT CAUSE AND SEVERANCE. If Company terminates Executive without cause, Company shall provide sixty (60) days advance notice and pay six (6) months base salary as severance.",
                "gt_category": "Termination",
                "gt_severity": "Low",
                "gt_party_bound": "Company",
                "gt_numbers": ["sixty (60) days", "six (6) months"],
                "gt_exceptions": []
            },
            {
                "position": 6,
                "title": "6. TERMINATION FOR CAUSE",
                "text": "6. TERMINATION FOR CAUSE. Company may terminate immediately for cause upon fraud, felony conviction, or gross insubordination, forfeiting all unvested equity and severance entitlements.",
                "gt_category": "Termination",
                "gt_severity": "High",
                "gt_party_bound": "Company",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 7,
                "title": "7. MANDATORY ARBITRATION",
                "text": "7. MANDATORY ARBITRATION. Any employment dispute shall be settled by binding arbitration in Seattle, Washington under American Arbitration Association (AAA) employment rules.",
                "gt_category": "Dispute Resolution",
                "gt_severity": "Medium",
                "gt_party_bound": "Both parties",
                "gt_numbers": [],
                "gt_exceptions": []
            }
        ]
    },
    {
        "doc_id": "held_out_5_independent_contractor_agreement",
        "title": "INDEPENDENT CONTRACTOR CONSULTING AGREEMENT",
        "party_a": "Aether Dynamics LLC (Client)",
        "party_b": "Kestrel Security Advisory Inc. (Contractor)",
        "reviewing_party": "Kestrel Security Advisory Inc.",
        "clauses": [
            {
                "position": 1,
                "title": "1. CONSULTING SERVICES AND DELIVERABLES",
                "text": "1. CONSULTING SERVICES AND DELIVERABLES. Contractor shall deliver cybersecurity penetration testing and architecture review services in accordance with Schedule A milestones.",
                "gt_category": "Scope / Deliverables",
                "gt_severity": "Low",
                "gt_party_bound": "Contractor",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 2,
                "title": "2. COMPENSATION AND EXPENSES",
                "text": "2. COMPENSATION AND EXPENSES. Client shall remit a fixed fee of $18,500.00 within forty-five (45) days of receipt of undisputed milestone completion invoices.",
                "gt_category": "Payment",
                "gt_severity": "Low",
                "gt_party_bound": "Client",
                "gt_numbers": ["$18,500.00", "forty-five (45) days"],
                "gt_exceptions": []
            },
            {
                "position": 3,
                "title": "3. INDEPENDENT CONTRACTOR STATUS",
                "text": "3. INDEPENDENT CONTRACTOR STATUS. Contractor acts as an independent contractor, assuming sole liability for all state, federal, and local income and payroll taxes.",
                "gt_category": "General / Boilerplate",
                "gt_severity": "Low",
                "gt_party_bound": "Contractor",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 4,
                "title": "4. CONFIDENTIALITY AND NONDISCLOSURE",
                "text": "4. CONFIDENTIALITY AND NONDISCLOSURE. Contractor agrees to hold all client architectural designs and vulnerability assessments in confidence for five (5) years following project completion.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Contractor only",
                "gt_numbers": ["five (5) years"],
                "gt_exceptions": []
            },
            {
                "position": 5,
                "title": "5. UNILATERAL CONTRACTOR INDEMNIFICATION",
                "text": "5. UNILATERAL CONTRACTOR INDEMNIFICATION. Contractor shall defend and indemnify Client against all claims, liabilities, losses, and damages arising out of Contractor's performance or negligence.",
                "gt_category": "Indemnification",
                "gt_severity": "Critical",
                "gt_party_bound": "Contractor only",
                "gt_numbers": [],
                "gt_exceptions": []
            },
            {
                "position": 6,
                "title": "6. TERMINATION FOR CONVENIENCE",
                "text": "6. TERMINATION FOR CONVENIENCE. Client may terminate this agreement at any time without cause upon fourteen (14) days prior written notice, paying only for completed deliverables.",
                "gt_category": "Termination",
                "gt_severity": "Medium",
                "gt_party_bound": "Client only",
                "gt_numbers": ["fourteen (14) days"],
                "gt_exceptions": []
            },
            {
                "position": 7,
                "title": "7. GOVERNING LAW AND SEVERABILITY",
                "text": "7. GOVERNING LAW AND SEVERABILITY. This Agreement shall be governed by California law. If any provision is deemed unenforceable, remaining terms remain in full force.",
                "gt_category": "Governing Law",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": [],
                "gt_exceptions": []
            }
        ]
    }
]

def generate_pdf(doc_spec):
    pdf_path = DOCS_DIR / f"{doc_spec['doc_id']}.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=15
    )
    parties_style = ParagraphStyle(
        'PartiesStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=10
    )

    story = []
    story.append(Paragraph(doc_spec["title"], title_style))
    story.append(Spacer(1, 10))
    preamble = f"This Agreement is entered into by and between {doc_spec['party_a']} and {doc_spec['party_b']}."
    story.append(Paragraph(preamble, parties_style))
    story.append(Spacer(1, 10))

    for cl in doc_spec["clauses"]:
        story.append(Paragraph(cl["text"], body_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"Generated PDF: {pdf_path}")

def generate_gt(doc_spec):
    gt_path = GT_DIR / f"{doc_spec['doc_id']}_ground_truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(doc_spec, f, indent=2)
    print(f"Generated Ground Truth: {gt_path}")

def main():
    for doc in HELD_OUT_DATA:
        generate_pdf(doc)
        generate_gt(doc)
    print("All 5 held-out contracts and ground truth files generated successfully.")

if __name__ == "__main__":
    main()
