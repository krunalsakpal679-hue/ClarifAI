"""
Script to generate 5 brand-new, unseen evaluation documents for Phase B generalization benchmarking.
Includes:
1. Document 1: Executive Employment Agreement (Executive vs Corporate Employer)
2. Document 2: Commercial Term Loan Agreement (Bank Lender vs Business Borrower)
3. Document 3: Cloud Workspace Terms of Service (SaaS Provider vs Business Customer)
4. Document 4: Unnumbered/Lettered Strategic Supply Agreement (Section A - Section F)
5. Document 5: Scanned / OCR'd Industrial Equipment Lease (Bitmap rendered with noise/rotation)
"""

import os
import io
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DATASET_DIR = Path("evaluation_dataset")
DOCS_DIR = DATASET_DIR / "documents"
GT_DIR = DATASET_DIR / "ground_truth"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
GT_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Heading1'],
    fontSize=16,
    leading=20,
    alignment=1,
    textColor=colors.HexColor('#0F172A'),
    spaceAfter=12
)

heading_style = ParagraphStyle(
    'SectionHeading',
    parent=styles['Heading2'],
    fontSize=11,
    leading=15,
    textColor=colors.HexColor('#1E293B'),
    spaceBefore=12,
    spaceAfter=4,
    keepWithNext=True
)

body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=14,
    textColor=colors.HexColor('#334155'),
    spaceAfter=6
)

# ==============================================================================
# 1. Document 1: Executive Employment Agreement
# ==============================================================================
def create_employment_doc():
    filename = DOCS_DIR / "new_doc_1_employment_agreement.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    story.append(Paragraph("<b>EXECUTIVE EMPLOYMENT AGREEMENT</b>", title_style))
    story.append(Paragraph("This Executive Employment Agreement is entered into as of November 1, 2026, by and between Vanguard Biometrics Inc. ('Company') and Dr. Marcus Vance ('Executive').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    story.append(Paragraph("<b>1. POSITION AND OPERATIONAL DUTIES</b>", heading_style))
    story.append(Paragraph("Executive shall serve as Chief Technology Officer reporting directly to the Chief Executive Officer and the Board of Directors, rendering full-time professional services in biometric cryptography.", body_style))
    
    story.append(Paragraph("<b>2. COMPENSATION AND PERFORMANCE BONUS</b>", heading_style))
    story.append(Paragraph("Company shall pay Executive an annual base salary of two hundred forty thousand dollars ($240,000), payable in semi-monthly installments. Executive is eligible for an annual discretionary performance bonus of up to thirty percent (30%) of base salary upon meeting corporate milestones.", body_style))
    
    story.append(Paragraph("<b>3. INTELLECTUAL PROPERTY ASSIGNMENT</b>", heading_style))
    story.append(Paragraph("All inventions, cryptographic algorithms, source code, and patentable discoveries conceived, developed, or reduced to practice by Executive during the term of employment shall belong exclusively to Company as works made for hire.", body_style))
    
    story.append(Paragraph("<b>4. POST-EMPLOYMENT NON-COMPETE COVENANT</b>", heading_style))
    story.append(Paragraph("During employment and for eighteen (18) months following termination, Executive shall not directly or indirectly engage in, advise, or invest in any competing biometric identity verification business anywhere in North America.", body_style))
    
    story.append(Paragraph("<b>5. TERMINATION AND SEVERANCE ENTITLEMENT</b>", heading_style))
    story.append(Paragraph("Either party may terminate employment without cause upon thirty (30) days written notice. If Company terminates Executive without Cause, Executive shall receive six (6) months of base salary continuation as severance, conditioned upon Executive executing an effective general release of claims.", body_style))
    
    story.append(Paragraph("<b>6. GOVERNING LAW AND JURISDICTION</b>", heading_style))
    story.append(Paragraph("This Agreement shall be construed and governed in accordance with the substantive laws of the Commonwealth of Massachusetts. The state courts located in Suffolk County, Massachusetts shall have exclusive jurisdiction over any controversy.", body_style))
    
    doc.build(story)
    print(f"Generated: {filename}")

# ==============================================================================
# 2. Document 2: Commercial Term Loan Agreement
# ==============================================================================
def create_loan_doc():
    filename = DOCS_DIR / "new_doc_2_commercial_loan_agreement.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    story.append(Paragraph("<b>COMMERCIAL TERM LOAN AGREEMENT</b>", title_style))
    story.append(Paragraph("This Commercial Term Loan Agreement is dated as of October 15, 2026, by and between First Horizon Commercial Bank ('Lender') and Starlight Hospitality Group LLC ('Borrower').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    story.append(Paragraph("<b>1. PRINCIPAL LOAN COMMITMENT</b>", heading_style))
    story.append(Paragraph("Lender agrees to disburse to Borrower a single-draw commercial term loan in the aggregate principal amount of three million five hundred thousand dollars ($3,500,000) for hotel facility expansion.", body_style))
    
    story.append(Paragraph("<b>2. INTEREST RATE AND REPAYMENT SCHEDULE</b>", heading_style))
    story.append(Paragraph("Borrower shall pay interest on unpaid principal at a fixed rate of seven point two five percent (7.25%) per annum, payable in monthly installments over a maturity period of sixty (60) months. Uncured default accrues penalty interest at twelve point zero percent (12.0%) per annum.", body_style))
    
    story.append(Paragraph("<b>3. FINANCIAL COVENANTS AND DEBT SERVICE</b>", heading_style))
    story.append(Paragraph("Borrower covenants to maintain a minimum Debt Service Coverage Ratio (DSCR) of not less than 1.25x tested at the end of each fiscal quarter. Failure to maintain DSCR constitutes an immediate Event of Default.", body_style))
    
    story.append(Paragraph("<b>4. PREPAYMENT PREMIUMS</b>", heading_style))
    story.append(Paragraph("Borrower may prepay the outstanding principal subject to a prepayment fee of three percent (3.0%) in Year 1, two percent (2.0%) in Year 2, one percent (1.0%) in Year 3, and zero percent thereafter.", body_style))
    
    story.append(Paragraph("<b>5. ACCELERATION AND REMEDIES ON DEFAULT</b>", heading_style))
    story.append(Paragraph("Upon the occurrence of any Event of Default, Lender may declare the entire outstanding principal balance, accrued unpaid interest, and all related fees immediately due and payable without presentment or demand.", body_style))
    
    story.append(Paragraph("<b>6. GOVERNING FORUM AND VENUE</b>", heading_style))
    story.append(Paragraph("This Agreement and all promissory obligations shall be governed by the laws of the State of New York, and Borrower consents to personal jurisdiction in the courts of New York County, New York.", body_style))
    
    doc.build(story)
    print(f"Generated: {filename}")

# ==============================================================================
# 3. Document 3: Cloud Workspace Terms of Service
# ==============================================================================
def create_tos_doc():
    filename = DOCS_DIR / "new_doc_3_saas_terms_of_service.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    story.append(Paragraph("<b>CLOUD WORKSPACE TERMS OF SERVICE</b>", title_style))
    story.append(Paragraph("These Terms of Service govern access to the enterprise cloud collaboration platform operated by SyncWave Collaboration Platforms Ltd. ('Provider') by registered business users ('Customer').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    story.append(Paragraph("<b>1. SUBSCRIPTION GRANT AND ACCESS RIGHTS</b>", heading_style))
    story.append(Paragraph("Provider grants Customer a non-exclusive, non-transferable, revocable subscription right to access and use the cloud collaboration software solely for internal business operations.", body_style))
    
    story.append(Paragraph("<b>2. SERVICE AVAILABILITY AND SERVICE CREDITS</b>", heading_style))
    story.append(Paragraph("Provider targets ninety-nine point nine percent (99.9%) monthly service uptime. If monthly availability falls below 99.9%, Customer is eligible for a five percent (5.0%) service credit per 1% of downtime as Customer's sole and exclusive remedy.", body_style))
    
    story.append(Paragraph("<b>3. DISCLAIMER OF CONSEQUENTIAL DAMAGES</b>", heading_style))
    story.append(Paragraph("In no event shall Provider be liable for any indirect, incidental, special, punitive, or consequential damages, including loss of profits, data corruption, or business interruption.", body_style))
    
    story.append(Paragraph("<b>4. AGGREGATE MONETARY LIABILITY LIMITATION</b>", heading_style))
    story.append(Paragraph("Provider's total cumulative monetary liability arising out of or related to this agreement shall not exceed the total subscription fees actually paid by Customer in the six (6) months preceding the claim.", body_style))
    
    story.append(Paragraph("<b>5. UNILATERAL MODIFICATION OF TERMS</b>", heading_style))
    story.append(Paragraph("Provider reserves the right to modify these Terms and subscription pricing upon thirty (30) days notice via email. Continued platform access after the effective date constitutes binding acceptance.", body_style))
    
    story.append(Paragraph("<b>6. BINDING ARBITRATION AND CLASS ACTION WAIVER</b>", heading_style))
    story.append(Paragraph("All disputes arising under these Terms shall be resolved exclusively through final and binding arbitration administered by the American Arbitration Association in San Francisco, California. Both parties waive any right to bring class actions.", body_style))
    
    doc.build(story)
    print(f"Generated: {filename}")

# ==============================================================================
# 4. Document 4: Unnumbered / Lettered Strategic Supply Agreement
# ==============================================================================
def create_lettered_supplier_doc():
    filename = DOCS_DIR / "new_doc_4_lettered_supplier_agreement.pdf"
    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    story.append(Paragraph("<b>STRATEGIC COMPONENT SUPPLY AGREEMENT</b>", title_style))
    story.append(Paragraph("This Component Supply Agreement is entered into by Pinnacle Automotive Systems Corp. ('Buyer') and Kinetix Precision Parts GmbH ('Supplier').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    
    story.append(Paragraph("<b>Section A. Purchase Orders and Lead Times</b>", heading_style))
    story.append(Paragraph("Supplier shall manufacture and deliver precision sensor assemblies pursuant to Buyer purchase orders with a guaranteed production lead time of forty-five (45) business days.", body_style))
    
    story.append(Paragraph("<b>Section B. Price Adjustments and Currency</b>", heading_style))
    story.append(Paragraph("Unit component prices remain fixed for initial twelve months. Annual price increases shall not exceed five percent (5.0%) and require sixty (60) days advance documented cost justification.", body_style))
    
    story.append(Paragraph("<b>Section C. Product Warranty and Defect Remedies</b>", heading_style))
    story.append(Paragraph("Supplier warrants that all delivered components are free from manufacturing defects for twenty-four (24) months from delivery date. Supplier shall repair or replace non-conforming parts within fourteen (14) calendar days.", body_style))
    
    story.append(Paragraph("<b>Section D. Patent Infringement and Product Indemnification</b>", heading_style))
    story.append(Paragraph("Supplier agrees to defend and indemnify Buyer, its affiliates, and customers from and against any third-party claims alleging patent infringement or personal injury arising from component manufacturing defects.", body_style))
    
    story.append(Paragraph("<b>Section E. Agreement Term and Termination Rights</b>", heading_style))
    story.append(Paragraph("Either party may terminate this agreement without cause upon ninety (90) days prior written notice. Either party may terminate immediately without notice upon the insolvency or bankruptcy of the other party.", body_style))
    
    story.append(Paragraph("<b>Section F. Applicable Law and Judicial Jurisdiction</b>", heading_style))
    story.append(Paragraph("This Agreement shall be interpreted and governed in all respects in accordance with the substantive laws of England and Wales, with exclusive jurisdiction in the High Court of Justice in London.", body_style))
    
    doc.build(story)
    print(f"Generated: {filename}")

# ==============================================================================
# 5. Document 5: Scanned / OCR'd Industrial Equipment Lease
# ==============================================================================
def create_scanned_ocr_doc():
    filename = DOCS_DIR / "new_doc_5_scanned_ocr_equipment_lease.pdf"
    
    # Render page as a high-resolution bitmap with slight rotation & realistic noise, then compile into PDF
    img_w, img_h = 1700, 2200
    img = Image.new("RGB", (img_w, img_h), color=(250, 249, 246)) # Off-white paper background
    draw = ImageDraw.Draw(img)
    
    # Use default bitmap font
    y = 120
    draw.text((380, y), "HEAVY INDUSTRIAL EQUIPMENT LEASE AGREEMENT", fill=(20, 20, 20))
    y += 60
    draw.line((120, y, 1580, y), fill=(80, 80, 80), width=3)
    y += 50
    draw.text((120, y), "This Lease Agreement is made between Titan Rigging & Machinery Rentals Inc. ('Lessor')", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "and Crestview Heavy Construction LLC ('Lessee').", fill=(30, 30, 30))
    y += 70
    
    # Clause 1
    draw.text((120, y), "1. LEASED EQUIPMENT AND TERM DURATION", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "Lessor leases to Lessee two (2) CAT 336 Hydraulic Excavators for a fixed operational term", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "of twenty-four (24) months commencing on December 1, 2026.", fill=(30, 30, 30))
    y += 70
    
    # Clause 2
    draw.text((120, y), "2. MONTHLY RENTAL AND SECURITY DEPOSIT", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "Lessee shall pay monthly rent of fourteen thousand five hundred dollars ($14,500) per unit,", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "due on the first day of each month. Lessee shall remit a thirty thousand dollar ($30,000) security deposit.", fill=(30, 30, 30))
    y += 70
    
    # Clause 3
    draw.text((120, y), "3. EQUIPMENT MAINTENANCE AND REPAIRS", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "Lessee assumes full responsibility for all preventive maintenance, lubrication, track repairs,", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "and daily inspections in accordance with manufacturer operating specifications.", fill=(30, 30, 30))
    y += 70
    
    # Clause 4
    draw.text((120, y), "4. INSURANCE AND CASUALTY INDEMNITY", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "Lessee must maintain commercial general liability insurance of not less than two million dollars ($2,000,000)", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "and indemnify Lessor against any workplace property loss or bodily injury claims.", fill=(30, 30, 30))
    y += 70
    
    # Clause 5
    draw.text((120, y), "5. TOTAL CASUALTY LOSS AND REPLACEMENT VALUE", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "In the event of total destruction or theft of any unit, Lessee shall pay Lessor the agreed replacement", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "valuation of three hundred eighty thousand dollars ($380,000) per excavator within thirty (30) days.", fill=(30, 30, 30))
    y += 70
    
    # Clause 6
    draw.text((120, y), "6. GOVERNING LAW AND COURT VENUE", fill=(10, 10, 10))
    y += 40
    draw.text((120, y), "This Lease shall be governed by the laws of the State of Ohio. All legal proceedings shall be litigated", fill=(30, 30, 30))
    y += 40
    draw.text((120, y), "exclusively in the state courts situated in Franklin County, Ohio.", fill=(30, 30, 30))
    
    # Add slight rotation & scan texture
    img_rotated = img.rotate(0.35, resample=Image.BICUBIC, fillcolor=(250, 249, 246))
    img_noisy = img_rotated.filter(ImageFilter.GaussianBlur(radius=0.4))
    
    # Save directly as PDF
    img_noisy.save(str(filename), "PDF", resolution=200.0)
    print(f"Generated scanned PDF: {filename}")


if __name__ == "__main__":
    create_employment_doc()
    create_loan_doc()
    create_tos_doc()
    create_lettered_supplier_doc()
    create_scanned_ocr_doc()
