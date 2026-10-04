"""
Validation Benchmark Dataset Generator (10 New Diverse Contract Archetypes)
Constructs 10 distinct, unseen validation contracts with pre-defined ground truth annotations:
1. Mutual NDA
2. Enterprise SaaS Subscription
3. Commercial Office Lease
4. Executive Employment
5. Independent Contractor
6. Commercial Term Loan
7. Manufacturing Supply
8. Proprietary Software License
9. Value-Added Reseller (VAR)
10. Master Technical Services
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

VALIDATION_DATA = [
    {
        "doc_id": "val_1_mutual_nda",
        "title": "MUTUAL PROPRIETARY INFORMATION AND NONDISCLOSURE AGREEMENT",
        "party_a": "Crestline Biotech Inc. (Disclosing Party)",
        "party_b": "Aegis Therapeutics LLC (Receiving Party)",
        "reviewing_party": "Aegis Therapeutics LLC",
        "clauses": [
            {
                "position": 1,
                "title": "1. DEFINITION OF PROPRIETARY INFORMATION",
                "text": "1. DEFINITION OF PROPRIETARY INFORMATION. Proprietary Information includes all technical, clinical, and commercial data disclosed by either party, marked confidential or reasonably understood as proprietary.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": []
            },
            {
                "position": 2,
                "title": "2. DUTY OF CARE AND USE LIMITATIONS",
                "text": "2. DUTY OF CARE AND USE LIMITATIONS. Receiving Party agrees to protect Proprietary Information with reasonable care and use it solely for evaluating the proposed commercial transaction.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Receiving Party",
                "gt_numbers": []
            },
            {
                "position": 3,
                "title": "3. TERM AND SURVIVAL OBLIGATIONS",
                "text": "3. TERM AND SURVIVAL OBLIGATIONS. This Agreement shall remain in effect for two (2) years, and nondisclosure covenants shall survive for five (5) years after expiration.",
                "gt_category": "Term",
                "gt_severity": "Moderate",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["two (2) years", "five (5) years"]
            },
            {
                "position": 4,
                "title": "4. GOVERNING LAW AND VENUE",
                "text": "4. GOVERNING LAW AND VENUE. This Agreement is governed by Delaware law, and all claims shall be resolved in state courts located in New Castle County, Delaware.",
                "gt_category": "Governing Law",
                "gt_severity": "Safe",
                "gt_party_bound": "Both parties",
                "gt_numbers": []
            }
        ]
    },
    {
        "doc_id": "val_2_enterprise_saas",
        "title": "ENTERPRISE CLOUD SAAS SUBSCRIPTION AGREEMENT",
        "party_a": "StratusCloud Technologies Inc. (Provider)",
        "party_b": "Pacific Rim Logistics Corp. (Customer)",
        "reviewing_party": "Pacific Rim Logistics Corp.",
        "clauses": [
            {
                "position": 1,
                "title": "1. SUBSCRIPTION FEES AND BILLING",
                "text": "1. SUBSCRIPTION FEES AND BILLING. Customer shall pay monthly subscription fees of $8,500.00 within thirty (30) days of invoice date. Overdue amounts incur interest at 1.5% per month.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Customer",
                "gt_numbers": ["$8,500.00", "thirty (30) days", "1.5%"]
            },
            {
                "position": 2,
                "title": "2. UNILATERAL CUSTOMER INDEMNIFICATION",
                "text": "2. UNILATERAL CUSTOMER INDEMNIFICATION. Customer shall defend, indemnify, and hold harmless Provider against all third-party claims, liabilities, and legal expenses arising from Customer data.",
                "gt_category": "Indemnification",
                "gt_severity": "High",
                "gt_party_bound": "Customer only",
                "gt_numbers": []
            },
            {
                "position": 3,
                "title": "3. AGGREGATE LIABILITY CAP",
                "text": "3. AGGREGATE LIABILITY CAP. Total liability of Provider shall not exceed the total fees paid by Customer in the six (6) months prior to the incident.",
                "gt_category": "Limitation of Liability",
                "gt_severity": "High",
                "gt_party_bound": "Provider",
                "gt_numbers": ["six (6) months"]
            },
            {
                "position": 4,
                "title": "4. TERMINATION FOR CONVENIENCE",
                "text": "4. TERMINATION FOR CONVENIENCE. Provider may terminate this agreement at will upon thirty (30) days notice without refund of prepaid subscription fees.",
                "gt_category": "Termination",
                "gt_severity": "High",
                "gt_party_bound": "Provider only",
                "gt_numbers": ["thirty (30) days"]
            }
        ]
    },
    {
        "doc_id": "val_3_commercial_lease",
        "title": "COMMERCIAL REAL ESTATE LEASE AGREEMENT",
        "party_a": "Harborview Realty Partners LLC (Landlord)",
        "party_b": "NextGen Software Labs Inc. (Tenant)",
        "reviewing_party": "NextGen Software Labs Inc.",
        "clauses": [
            {
                "position": 1,
                "title": "1. LEASED PREMISES AND USE",
                "text": "1. LEASED PREMISES AND USE. Landlord leases 4,000 square feet of commercial office space at 200 Harbor Boulevard, Suite 500, Seattle, WA for general software engineering use.",
                "gt_category": "Premises",
                "gt_severity": "Safe",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["4,000 square feet"]
            },
            {
                "position": 2,
                "title": "2. BASE RENT AND SECURITY DEPOSIT",
                "text": "2. BASE RENT AND SECURITY DEPOSIT. Tenant shall pay monthly rent of $9,200.00 USD on the 1st of each month and deposit an initial security deposit of $18,400.00 USD.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Tenant",
                "gt_numbers": ["$9,200.00", "$18,400.00"]
            },
            {
                "position": 3,
                "title": "3. LEASE TERM AND RENEWAL NOTICE",
                "text": "3. LEASE TERM AND RENEWAL NOTICE. Lease duration is thirty-six (36) months commencing January 1, 2027, with renewal option on ninety (90) days advance written notice.",
                "gt_category": "Term",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["thirty-six (36) months", "ninety (90) days"]
            },
            {
                "position": 4,
                "title": "4. MAINTENANCE DIVISION OF RESPONSIBILITIES",
                "text": "4. MAINTENANCE DIVISION OF RESPONSIBILITIES. Landlord maintains exterior roof, foundation, and elevators; Tenant maintains interior lighting and plumbing fixtures.",
                "gt_category": "Maintenance",
                "gt_severity": "Safe",
                "gt_party_bound": "Both parties",
                "gt_numbers": []
            }
        ]
    },
    {
        "doc_id": "val_4_executive_employment",
        "title": "EXECUTIVE EMPLOYMENT AGREEMENT",
        "party_a": "Aura Pharmaceuticals Corp. (Company)",
        "party_b": "Marcus Thorne (Executive)",
        "reviewing_party": "Marcus Thorne",
        "clauses": [
            {
                "position": 1,
                "title": "1. BASE SALARY AND INCENTIVE BONUS",
                "text": "1. BASE SALARY AND INCENTIVE BONUS. Company pays Executive an annual base salary of $320,000.00, payable semi-monthly, plus an annual performance bonus target of 40%.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Company",
                "gt_numbers": ["$320,000.00", "40%"]
            },
            {
                "position": 2,
                "title": "2. RESTRICTIVE COVENANTS AND NON-COMPETE",
                "text": "2. RESTRICTIVE COVENANTS AND NON-COMPETE. For twelve (12) months following separation, Executive shall not work for any direct pharmaceutical competitor within North America.",
                "gt_category": "Restrictive Covenants",
                "gt_severity": "High",
                "gt_party_bound": "Executive only",
                "gt_numbers": ["twelve (12) months"]
            },
            {
                "position": 3,
                "title": "3. INTELLECTUAL PROPERTY ASSIGNMENT",
                "text": "3. INTELLECTUAL PROPERTY ASSIGNMENT. All drug formulations, chemical syntheses, and patents developed by Executive during employment are works made for hire belonging solely to Company.",
                "gt_category": "Intellectual Property",
                "gt_severity": "Moderate",
                "gt_party_bound": "Executive only",
                "gt_numbers": []
            },
            {
                "position": 4,
                "title": "4. SEVERANCE UPON TERMINATION WITHOUT CAUSE",
                "text": "4. SEVERANCE UPON TERMINATION WITHOUT CAUSE. If terminated without cause, Executive receives sixty (60) days advance notice and nine (9) months salary continuation.",
                "gt_category": "Termination",
                "gt_severity": "Low",
                "gt_party_bound": "Company",
                "gt_numbers": ["sixty (60) days", "nine (9) months"]
            }
        ]
    },
    {
        "doc_id": "val_5_independent_contractor",
        "title": "INDEPENDENT CONTRACTOR SERVICES AGREEMENT",
        "party_a": "BlueStone Financial LLC (Client)",
        "party_b": "Vektor Infosec Advisory Inc. (Contractor)",
        "reviewing_party": "Vektor Infosec Advisory Inc.",
        "clauses": [
            {
                "position": 1,
                "title": "1. CONSULTING SERVICES AND DELIVERABLES",
                "text": "1. CONSULTING SERVICES AND DELIVERABLES. Contractor delivers cloud penetration testing and risk assessment reports as described in Schedule A Statement of Work.",
                "gt_category": "Scope of Services",
                "gt_severity": "Safe",
                "gt_party_bound": "Contractor",
                "gt_numbers": []
            },
            {
                "position": 2,
                "title": "2. PROFESSIONAL FEES AND INVOICING",
                "text": "2. PROFESSIONAL FEES AND INVOICING. Client remits fixed project fee of $24,000.00 within forty-five (45) days after milestone completion approval.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Client",
                "gt_numbers": ["$24,000.00", "forty-five (45) days"]
            },
            {
                "position": 3,
                "title": "3. CONTRACTOR INDEMNIFICATION BURDEN",
                "text": "3. CONTRACTOR INDEMNIFICATION BURDEN. Contractor shall defend and indemnify Client against all claims, losses, damages, and legal costs arising from Contractor's negligence.",
                "gt_category": "Indemnification",
                "gt_severity": "High",
                "gt_party_bound": "Contractor only",
                "gt_numbers": []
            },
            {
                "position": 4,
                "title": "4. TERMINATION NOTICE FOR CONVENIENCE",
                "text": "4. TERMINATION NOTICE FOR CONVENIENCE. Client may terminate this contract for convenience upon fourteen (14) days advance written notice.",
                "gt_category": "Termination",
                "gt_severity": "Moderate",
                "gt_party_bound": "Client only",
                "gt_numbers": ["fourteen (14) days"]
            }
        ]
    },
    {
        "doc_id": "val_6_commercial_loan",
        "title": "COMMERCIAL CREDIT FACILITY AND TERM LOAN AGREEMENT",
        "party_a": "Keystone Commercial Bank (Lender)",
        "party_b": "Pioneer Heavy Industries Corp. (Borrower)",
        "reviewing_party": "Pioneer Heavy Industries Corp.",
        "clauses": [
            {
                "position": 1,
                "title": "1. PRINCIPAL FACILITY AND DISBURSEMENT",
                "text": "1. PRINCIPAL FACILITY AND DISBURSEMENT. Lender establishes a single-draw term loan facility in the principal amount of $1,500,000.00 USD disbursed on the Closing Date.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["$1,500,000.00"]
            },
            {
                "position": 2,
                "title": "2. INTEREST RATE AND COMPOUNDING LATE CHARGES",
                "text": "2. INTEREST RATE AND COMPOUNDING LATE CHARGES. Interest accrues at 6.75% per annum. Past due payments accrue default interest of 2.5% per month compounded monthly.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Moderate",
                "gt_party_bound": "Borrower",
                "gt_numbers": ["6.75%", "2.5%"]
            },
            {
                "position": 3,
                "title": "3. FINANCIAL COVENANTS AND DSCR RATIO",
                "text": "3. FINANCIAL COVENANTS AND DSCR RATIO. Borrower shall maintain a minimum Debt Service Coverage Ratio (DSCR) of not less than 1.25 to 1.00 at the close of each fiscal quarter.",
                "gt_category": "General / Boilerplate",
                "gt_severity": "Moderate",
                "gt_party_bound": "Borrower",
                "gt_numbers": ["1.25 to 1.00"]
            },
            {
                "position": 4,
                "title": "4. EVENTS OF DEFAULT AND ACCELERATION",
                "text": "4. EVENTS OF DEFAULT AND ACCELERATION. Upon any payment default continuing for ten (10) days, Lender may declare all unpaid principal and accrued interest immediately due.",
                "gt_category": "Termination",
                "gt_severity": "High",
                "gt_party_bound": "Borrower",
                "gt_numbers": ["ten (10) days"]
            }
        ]
    },
    {
        "doc_id": "val_7_manufacturing_supply",
        "title": "MASTER OEM MANUFACTURING AND SUPPLY AGREEMENT",
        "party_a": "Apex Hardware Systems LLC (Buyer)",
        "party_b": "Precision Component Fabrication Inc. (Supplier)",
        "reviewing_party": "Apex Hardware Systems LLC",
        "clauses": [
            {
                "position": 1,
                "title": "1. PURCHASE ORDERS AND DELIVERY LEAD TIMES",
                "text": "1. PURCHASE ORDERS AND DELIVERY LEAD TIMES. Supplier shall manufacture and deliver component units within forty-five (45) days of purchase order receipt.",
                "gt_category": "Scope of Services",
                "gt_severity": "Low",
                "gt_party_bound": "Supplier",
                "gt_numbers": ["forty-five (45) days"]
            },
            {
                "position": 2,
                "title": "2. PRODUCT WARRANTY AND DEFECT REMEDIES",
                "text": "2. PRODUCT WARRANTY AND DEFECT REMEDIES. Supplier warrants all delivered hardware against manufacturing defects for twenty-four (24) months from delivery date.",
                "gt_category": "Warranty",
                "gt_severity": "Low",
                "gt_party_bound": "Supplier",
                "gt_numbers": ["twenty-four (24) months"]
            },
            {
                "position": 3,
                "title": "3. PRODUCT DEFECT INDEMNITY",
                "text": "3. PRODUCT DEFECT INDEMNITY. Supplier shall indemnify and hold harmless Buyer and its customers from all third-party product liability claims arising from defective goods.",
                "gt_category": "Indemnification",
                "gt_severity": "Low",
                "gt_party_bound": "Supplier",
                "gt_numbers": []
            },
            {
                "position": 4,
                "title": "4. EXCLUSIVE SUPPLY AND MINIMUM COMMITMENT",
                "text": "4. EXCLUSIVE SUPPLY AND MINIMUM COMMITMENT. Buyer commits to purchase a minimum volume of 50,000 units annually during the initial three (3) year term.",
                "gt_category": "Term",
                "gt_severity": "Moderate",
                "gt_party_bound": "Buyer",
                "gt_numbers": ["50,000 units", "three (3) year"]
            }
        ]
    },
    {
        "doc_id": "val_8_software_license",
        "title": "ON-PREMISES ENTERPRISE SOFTWARE LICENSE AGREEMENT",
        "party_a": "QuantumSoft Solutions Corp. (Licensor)",
        "party_b": "Meridian Health Systems Inc. (Licensee)",
        "reviewing_party": "Meridian Health Systems Inc.",
        "clauses": [
            {
                "position": 1,
                "title": "1. GRANT OF LICENSE AND USER SEATS",
                "text": "1. GRANT OF LICENSE AND USER SEATS. Licensor grants Licensee a non-exclusive, non-transferable perpetual license for up to two hundred fifty (250) named concurrent users.",
                "gt_category": "Intellectual Property",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["two hundred fifty (250)"]
            },
            {
                "position": 2,
                "title": "2. LICENSE FEES AND ANNUAL MAINTENANCE",
                "text": "2. LICENSE FEES AND ANNUAL MAINTENANCE. Licensee shall pay upfront fee of $75,000.00 and an optional annual support maintenance fee equal to 18% of license fees.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Licensee",
                "gt_numbers": ["$75,000.00", "18%"]
            },
            {
                "position": 3,
                "title": "3. AUDIT RIGHTS AND INSPECTION",
                "text": "3. AUDIT RIGHTS AND INSPECTION. Licensor may audit Licensee's software deployment once annually upon thirty (30) days prior written notice during business hours.",
                "gt_category": "Audit / Inspection",
                "gt_severity": "Low",
                "gt_party_bound": "Licensee",
                "gt_numbers": ["thirty (30) days"]
            },
            {
                "position": 4,
                "title": "4. IP INFRINGEMENT INDEMNITY",
                "text": "4. IP INFRINGEMENT INDEMNITY. Licensor defends and indemnifies Licensee against third-party copyright, patent, or trademark infringement suits regarding the software.",
                "gt_category": "Indemnification",
                "gt_severity": "Low",
                "gt_party_bound": "Licensor",
                "gt_numbers": []
            }
        ]
    },
    {
        "doc_id": "val_9_value_added_reseller",
        "title": "VALUE-ADDED RESELLER AND DISTRIBUTION AGREEMENT",
        "party_a": "CyberShield Core Systems Inc. (Vendor)",
        "party_b": "Summit Channel Partners LLC (Reseller)",
        "reviewing_party": "Summit Channel Partners LLC",
        "clauses": [
            {
                "position": 1,
                "title": "1. APPOINTMENT OF RESELLER AND TERRITORY",
                "text": "1. APPOINTMENT OF RESELLER AND TERRITORY. Vendor appoints Reseller as a non-exclusive distributor of products within the Western European commercial territory.",
                "gt_category": "Scope of Services",
                "gt_severity": "Safe",
                "gt_party_bound": "Both parties",
                "gt_numbers": []
            },
            {
                "position": 2,
                "title": "2. RESELLER DISCOUNTS AND PAYMENT CADENCE",
                "text": "2. RESELLER DISCOUNTS AND PAYMENT CADENCE. Reseller receives a thirty percent (30%) discount off list price, remitting net payment within sixty (60) days of invoice.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Reseller",
                "gt_numbers": ["thirty percent (30%)", "sixty (60) days"]
            },
            {
                "position": 3,
                "title": "3. MINIMUM ANNUAL SALES QUOTA",
                "text": "3. MINIMUM ANNUAL SALES QUOTA. Reseller shall achieve annual sales of $500,000.00 USD to maintain tier-one partner status and preferential pricing.",
                "gt_category": "General / Boilerplate",
                "gt_severity": "Moderate",
                "gt_party_bound": "Reseller",
                "gt_numbers": ["$500,000.00"]
            },
            {
                "position": 4,
                "title": "4. TERMINATION FOR CAUSE OR INACTIVITY",
                "text": "4. TERMINATION FOR CAUSE OR INACTIVITY. Vendor may terminate upon sixty (60) days notice if Reseller fails to meet minimum sales quotas for two consecutive quarters.",
                "gt_category": "Termination",
                "gt_severity": "Moderate",
                "gt_party_bound": "Vendor",
                "gt_numbers": ["sixty (60) days"]
            }
        ]
    },
    {
        "doc_id": "val_10_technical_services",
        "title": "MASTER TECHNICAL AND MANAGED SERVICES AGREEMENT",
        "party_a": "Evergreen Enterprise Advisory LLC (Service Provider)",
        "party_b": "Apex Financial Corporation (Client)",
        "reviewing_party": "Apex Financial Corporation",
        "clauses": [
            {
                "position": 1,
                "title": "1. MANAGED CLOUD INFRASTRUCTURE SCOPE",
                "text": "1. MANAGED CLOUD INFRASTRUCTURE SCOPE. Service Provider delivers 24x7 monitoring, patch management, and cloud architecture optimization under Statements of Work.",
                "gt_category": "Scope of Services",
                "gt_severity": "Safe",
                "gt_party_bound": "Service Provider",
                "gt_numbers": []
            },
            {
                "position": 2,
                "title": "2. SLA UPTIME COMMITMENT AND CREDITS",
                "text": "2. SLA UPTIME COMMITMENT AND CREDITS. Service Provider guarantees 99.95% cloud availability. If uptime falls below 99.0%, Client receives a 20% billing credit.",
                "gt_category": "Payment / Rent",
                "gt_severity": "Low",
                "gt_party_bound": "Service Provider",
                "gt_numbers": ["99.95%", "99.0%", "20%"]
            },
            {
                "position": 3,
                "title": "3. MUTUAL CONFIDENTIALITY OBLIGATIONS",
                "text": "3. MUTUAL CONFIDENTIALITY OBLIGATIONS. Each party protects confidential information with reasonable care, surviving for three (3) years following agreement termination.",
                "gt_category": "Confidentiality",
                "gt_severity": "Low",
                "gt_party_bound": "Both parties",
                "gt_numbers": ["three (3) years"]
            },
            {
                "position": 4,
                "title": "4. MUTUAL DISPUTE RESOLUTION AND ARBITRATION",
                "text": "4. MUTUAL DISPUTE RESOLUTION AND ARBITRATION. Any controversy shall be submitted to binding arbitration in San Francisco, California under AAA commercial arbitration rules.",
                "gt_category": "Dispute Resolution",
                "gt_severity": "Safe",
                "gt_party_bound": "Both parties",
                "gt_numbers": []
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
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=14
    )
    parties_style = ParagraphStyle(
        'PartiesStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
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
    story.append(Spacer(1, 8))
    preamble = f"This Agreement is entered into by and between {doc_spec['party_a']} and {doc_spec['party_b']}."
    story.append(Paragraph(preamble, parties_style))
    story.append(Spacer(1, 8))

    for cl in doc_spec["clauses"]:
        story.append(Paragraph(cl["text"], body_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"Generated Validation PDF: {pdf_path}")

def generate_gt(doc_spec):
    gt_path = GT_DIR / f"{doc_spec['doc_id']}_ground_truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(doc_spec, f, indent=2)
    print(f"Generated Validation Ground Truth: {gt_path}")

def main():
    for doc in VALIDATION_DATA:
        generate_pdf(doc)
        generate_gt(doc)
    print("All 10 validation benchmark contracts generated successfully.")

if __name__ == "__main__":
    main()
