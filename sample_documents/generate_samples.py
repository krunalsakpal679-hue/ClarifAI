import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_msa_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=14
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    story = []

    # Title
    story.append(Paragraph("<b>MASTER SERVICES AGREEMENT</b>", title_style))
    story.append(Paragraph("This Master Services Agreement ('Agreement') is entered into as of October 1, 2026, by and between Apex Global Solutions Inc. ('Customer') and Lumina Tech Services LLC ('Vendor').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=14))

    # Clause 1: Scope of Services
    story.append(Paragraph("<b>1. SCOPE OF SERVICES</b>", heading_style))
    story.append(Paragraph("Vendor shall perform cloud infrastructure management, custom software architecture, and artificial intelligence integration services as outlined in individual Statements of Work executed under this Agreement.", body_style))
    story.append(Spacer(1, 10))

    # Clause 2: Payment Terms
    story.append(Paragraph("<b>2. PAYMENT AND FEES</b>", heading_style))
    story.append(Paragraph("Customer shall remit payment within thirty (30) days of receipt of a valid, undisputed invoice. Any late payments shall accrue interest at a rate of one percent (1.0%) per month or the highest legal permissible limit, whichever is lower.", body_style))
    story.append(Spacer(1, 10))

    # Clause 3: Confidentiality
    story.append(Paragraph("<b>3. CONFIDENTIALITY & PROPRIETARY INFORMATION</b>", heading_style))
    story.append(Paragraph("Each party agrees to maintain in strict confidence all proprietary data, financial projections, source code, and trade secrets disclosed by the other party. Neither party shall disclose Confidential Information to third parties without prior written consent, surviving five (5) years following contract termination.", body_style))
    story.append(Spacer(1, 10))

    # Clause 4: Intellectual Property
    story.append(Paragraph("<b>4. INTELLECTUAL PROPERTY RIGHTS</b>", heading_style))
    story.append(Paragraph("All deliverables, documentation, custom scripts, and code developed exclusively for Customer pursuant to this Agreement shall constitute 'works made for hire' and become the sole and exclusive property of Customer upon full satisfaction of fees.", body_style))
    story.append(Spacer(1, 10))

    # Clause 5: Indemnification (High Risk)
    story.append(Paragraph("<b>5. INDEMNIFICATION</b>", heading_style))
    story.append(Paragraph("Vendor agrees to defend, indemnify, and hold harmless Customer, its officers, affiliates, and employees from and against any third-party claims, liabilities, damages, and expenses arising out of any infringement of intellectual property rights, gross negligence, or willful misconduct by Vendor.", body_style))
    story.append(Spacer(1, 10))

    # Clause 6: Limitation of Liability (High / Medium Risk)
    story.append(Paragraph("<b>6. LIMITATION OF LIABILITY</b>", heading_style))
    story.append(Paragraph("Except for liabilities arising under Section 3 (Confidentiality) or Section 5 (Indemnification), neither party's aggregate monetary liability under this Agreement shall exceed the total amount actually paid by Customer to Vendor in the twelve (12) months preceding the event giving rise to liability.", body_style))
    story.append(Spacer(1, 10))

    # Clause 7: Term and Termination
    story.append(Paragraph("<b>7. TERM AND TERMINATION</b>", heading_style))
    story.append(Paragraph("Either party may terminate this Agreement without cause upon giving sixty (60) calendar days prior written notice to the other party. Either party may terminate immediately if the other party breaches any material term and fails to cure within thirty (30) days of written notice.", body_style))
    story.append(Spacer(1, 10))

    # Clause 8: Governing Law and Dispute Resolution
    story.append(Paragraph("<b>8. GOVERNING LAW & JURISDICTION</b>", heading_style))
    story.append(Paragraph("This Agreement shall be construed, interpreted, and governed in accordance with the substantive laws of the State of Delaware, without giving effect to conflicts of law principles. Any dispute arising hereunder shall be subject to the exclusive jurisdiction of the state and federal courts located in New Castle County, Delaware.", body_style))
    story.append(Spacer(1, 10))

    # Clause 9: Non-Solicitation
    story.append(Paragraph("<b>9. NON-SOLICITATION</b>", heading_style))
    story.append(Paragraph("During the term of this Agreement and for twelve (12) months thereafter, neither party shall knowingly solicit or employ any personnel or contractor of the other party without express written permission.", body_style))

    doc.build(story)
    print(f"Created: {filename}")

def create_nda_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=14
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    story = []

    # Title
    story.append(Paragraph("<b>MUTUAL NON-DISCLOSURE AGREEMENT</b>", title_style))
    story.append(Paragraph("This Mutual Non-Disclosure Agreement ('NDA') is effective as of October 1, 2026, between CyberScale Technologies Corp. and NovaLabs AI Ltd.", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=14))

    # 1. Purpose
    story.append(Paragraph("<b>1. PURPOSE OF DISCLOSURE</b>", heading_style))
    story.append(Paragraph("The parties wish to explore a potential strategic collaboration involving enterprise AI automated compliance and contract analysis systems ('Authorized Purpose').", body_style))
    story.append(Spacer(1, 10))

    # 2. Definition
    story.append(Paragraph("<b>2. DEFINITION OF CONFIDENTIAL INFORMATION</b>", heading_style))
    story.append(Paragraph("'Confidential Information' includes all non-public technical, algorithmic, operational, financial, and business data disclosed by either party, whether in writing, oral, electronic, or visual form.", body_style))
    story.append(Spacer(1, 10))

    # 3. Exclusions
    story.append(Paragraph("<b>3. EXCLUSIONS FROM CONFIDENTIALITY</b>", heading_style))
    story.append(Paragraph("Confidential Information does not include information that: (a) is or becomes publicly known through no breach of this Agreement; (b) was already known to the recipient prior to disclosure; (c) is independently developed without reference to the Discloser's information.", body_style))
    story.append(Spacer(1, 10))

    # 4. Standard of Care
    story.append(Paragraph("<b>4. OBLIGATIONS & STANDARD OF CARE</b>", heading_style))
    story.append(Paragraph("The Recipient agrees to protect Confidential Information using the same degree of care it uses for its own confidential information of like nature, but in no event less than a reasonable standard of care.", body_style))
    story.append(Spacer(1, 10))

    # 5. Non-Circumvention (High Risk)
    story.append(Paragraph("<b>5. NON-CIRCUMVENTION</b>", heading_style))
    story.append(Paragraph("Recipient agrees not to circumvent, avoid, or bypass Discloser directly or indirectly to enter into transactions with Discloser's prospective enterprise clients or partners revealed during the evaluation period.", body_style))
    story.append(Spacer(1, 10))

    # 6. Governing Law
    story.append(Paragraph("<b>6. GOVERNING LAW AND INJUNCTIVE RELIEF</b>", heading_style))
    story.append(Paragraph("This Agreement shall be governed by the laws of California. The parties acknowledge that unauthorized disclosure causes irreparable harm for which damages are inadequate, entitling the Discloser to seek immediate injunctive relief.", body_style))

    doc.build(story)
    print(f"Created: {filename}")

def create_high_risk_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor('#DC2626'),
        spaceAfter=14
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#991B1B'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=8
    )

    story = []

    # Title
    story.append(Paragraph("<b>ENTERPRISE SOFTWARE VENDOR AGREEMENT</b>", title_style))
    story.append(Paragraph("This Commercial Vendor Agreement is entered into between CloudScale Provider LLC ('Vendor') and Enterprise Client ('Customer').", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#EF4444'), spaceAfter=14))

    # 1. Services
    story.append(Paragraph("<b>1. SCOPE OF SERVICES</b>", heading_style))
    story.append(Paragraph("Vendor provides access to proprietary cloud software on an as-is basis without performance warranties.", body_style))
    story.append(Spacer(1, 10))

    # 2. Broad Indemnification (High Risk - R006)
    story.append(Paragraph("<b>2. INDEMNIFICATION AND DEFENSE</b>", heading_style))
    story.append(Paragraph("Customer shall defend and indemnify Vendor, its directors, and agents against any and all claims, damages, lawsuits, and liabilities whatsoever arising out of or related to this Agreement, regardless of whether caused by Vendor's negligence or breach.", body_style))
    story.append(Spacer(1, 10))

    # 3. Complete Liability Disclaimer (High Risk - R005)
    story.append(Paragraph("<b>3. TOTAL DISCLAIMER OF LIABILITY</b>", heading_style))
    story.append(Paragraph("Vendor disclaims all liability whatsoever under this Agreement. Under no circumstances shall Vendor be liable for any direct, indirect, or consequential damages. User assumes all risk and agrees company has no liability whatsoever.", body_style))
    story.append(Spacer(1, 10))

    # 4. Unilateral Modification (High Risk - R007)
    story.append(Paragraph("<b>4. UNILATERAL MODIFICATION OF TERMS</b>", heading_style))
    story.append(Paragraph("Vendor reserves the right to modify, change, and revise these terms and pricing at any time without prior notice in its sole discretion. Continued use constitutes irrevocable acceptance.", body_style))
    story.append(Spacer(1, 10))

    # 5. Immediate Termination & Cancellation Penalty (High Risk - R008 & R002)
    story.append(Paragraph("<b>5. TERMINATION AND EARLY CANCELLATION PENALTY</b>", heading_style))
    story.append(Paragraph("Vendor reserves the absolute right to terminate at any time without cause and immediate termination without notice. If Customer terminates prior to term completion, Customer shall pay an early termination penalty of $25,000 as liquidated damages.", body_style))
    story.append(Spacer(1, 10))

    # 6. Automatic Renewal (High Risk - R001)
    story.append(Paragraph("<b>6. AUTOMATIC RENEWAL</b>", heading_style))
    story.append(Paragraph("This Agreement will automatically renew for consecutive two-year terms unless Customer provides written notice of at least 120 days prior to the expiration date.", body_style))
    story.append(Spacer(1, 10))

    # 7. Global Non-Compete (High Risk - R014)
    story.append(Paragraph("<b>7. RESTRICTIVE COVENANT AND NON-COMPETE</b>", heading_style))
    story.append(Paragraph("Customer and its employees agree to a strict non-compete covenant and shall not engage in competing business, develop similar cloud software, or solicit any personnel worldwide for five (5) years.", body_style))

    doc.build(story)
    print(f"Created: {filename}")

if __name__ == '__main__':
    msa_path = os.path.abspath(os.path.join('sample_documents', 'Sample_Master_Services_Agreement.pdf'))
    nda_path = os.path.abspath(os.path.join('sample_documents', 'Sample_Non_Disclosure_Agreement.pdf'))
    risky_path = os.path.abspath(os.path.join('sample_documents', 'Sample_High_Risk_Predatory_Contract.pdf'))
    create_msa_pdf(msa_path)
    create_nda_pdf(nda_path)
    create_high_risk_pdf(risky_path)

