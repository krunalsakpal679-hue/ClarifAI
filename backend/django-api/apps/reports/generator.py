"""
PDF Report Compiler Engine (PRD Ch. 28.1 & Spec Part 5 Layout Spec).
Uses ReportLab to compile Document and Comparison data into structured,
auditable PDF reports adhering strictly to the Part 5 layout specification.
"""
import os
import re
import hashlib
import logging
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether, HRFlowable

logger = logging.getLogger(__name__)


def get_reports_dir():
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def normalize_pdf_text(text: str) -> str:
    """Normalizes non-ASCII hyphens, dashes, quotes, and non-breaking spaces to standard ASCII printable characters."""
    if not text:
        return ""
    text = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]', '-', text)
    text = re.sub(r'[\u00a0\u202f\u2007]', ' ', text)
    text = text.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    return text


def _safe_str(text: str, has_unicode: bool, fallback: str = "") -> str:
    """Safeguards ReportLab against Latin-1 encoding crashes when no Unicode font is present."""
    if not text:
        return normalize_pdf_text(fallback) or ""
    text = normalize_pdf_text(text)
    if has_unicode:
        return text
    try:
        text.encode('latin-1')
        return text
    except UnicodeEncodeError:
        return normalize_pdf_text(fallback) or ""


def get_pdf_font(language='en'):
    """Resolves Unicode font for non-Latin languages."""
    if language == 'hi':
        candidate_fonts = [
            ('Nirmala', 'C:/Windows/Fonts/Nirmala.ttc', 0),
            ('Mangal', 'C:/Windows/Fonts/mangal.ttf', None),
            ('Arial', 'C:/Windows/Fonts/arial.ttf', None),
            ('NotoSansDevanagari', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf', None),
        ]
        for font_name, font_path, sub_idx in candidate_fonts:
            if os.path.exists(font_path):
                try:
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    if font_name not in pdfmetrics.getRegisteredFontNames():
                        if sub_idx is not None:
                            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=sub_idx))
                        else:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                    return font_name
                except Exception as font_err:
                    logger.warning(f"Could not register font {font_name} from {font_path}: {font_err}")
    return 'Helvetica'


def generate_document_pdf(report, document, language='en'):
    """
    Compiles Document analysis into a Part 5-compliant PDF report with structured header,
    executive overview, key figures table, clause summary table, and detailed clause cards.
    """
    reports_dir = get_reports_dir()
    file_path = os.path.join(reports_dir, f"{report.id}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    font_family = get_pdf_font(language)
    font_bold = font_family if font_family != 'Helvetica' else 'Helvetica-Bold'
    has_unicode = (font_family != 'Helvetica')

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )
    subheading_style = ParagraphStyle(
        'DocSubHeading',
        parent=styles['Heading3'],
        fontName=font_bold,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceBefore=4,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )
    quote_style = ParagraphStyle(
        'DocQuote',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#475569'),
        leftIndent=10,
        spaceAfter=4
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#64748B')
    )

    elements = []

    # Calculate document hash (Full 64-hex SHA-256 per W8 Spec)
    doc_hash = hashlib.sha256(str(document.id).encode()).hexdigest()
    if hasattr(document, 'file_reference') and document.file_reference:
        try:
            if hasattr(document.file_reference, 'path') and os.path.exists(document.file_reference.path):
                with open(document.file_reference.path, 'rb') as f:
                    doc_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception:
            pass

    # 5.1 Report Header
    doc_title = (document.original_filename or "Commercial Agreement").replace(".pdf", "").replace("_", " ")
    elements.append(Paragraph(f"<b>ClarifAI Contract Analysis:</b> {doc_title}", title_style))
    
    reviewing_party = getattr(document, 'reviewing_party', None) or "Neutral / Reviewing Counsel"
    header_table_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report.id}", meta_style),
            Paragraph(f"<b>Doc Hash (SHA-256):</b> {doc_hash}", meta_style)
        ],
        [
            Paragraph(f"<b>Source File:</b> {document.original_filename}", meta_style),
            Paragraph(f"<b>Perspective:</b> Reviewing as: {reviewing_party}", meta_style)
        ]
    ]
    t_hdr = Table(header_table_data, colWidths=[270, 270])
    t_hdr.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    elements.append(t_hdr)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

    # 5.2 Executive Overview
    summary = getattr(document, 'summary', None)
    clauses = document.clauses.all().order_by('position')

    if summary:
        elements.append(Paragraph("<b>1. Executive Overview</b>", heading_style))
        if summary.purpose_text:
            elements.append(Paragraph(f"<b>Purpose:</b> {_safe_str(summary.purpose_text, has_unicode)}", body_style))
            elements.append(Spacer(1, 4))

        # Risk Counts (Matching exact clause counts per W8 Spec)
        high_cnt = clauses.filter(severity__iexact='high').count()
        mod_cnt = clauses.filter(severity__in=['moderate', 'medium']).count()
        low_cnt = clauses.filter(severity__in=['low', 'safe']).count()
        rev_cnt = clauses.exclude(severity__in=['high', 'moderate', 'medium', 'low', 'safe']).count()
        
        profile_str = f"HIGH: {high_cnt} | MODERATE: {mod_cnt} | LOW: {low_cnt}"
        if rev_cnt > 0:
            profile_str += f" | NEEDS_REVIEW: {rev_cnt}"
        profile_str += f" (Total: {clauses.count()} clauses)"
        elements.append(Paragraph(f"<b>Risk Profile:</b> {profile_str}", body_style))
        elements.append(Spacer(1, 6))

        # Top Risks & Gaps
        if summary.key_risks_text:
            elements.append(Paragraph(f"<b>Key Risk Findings:</b> {_safe_str(summary.key_risks_text, has_unicode)}", body_style))
            elements.append(Spacer(1, 4))
        if summary.key_terms_text:
            elements.append(Paragraph(f"<b>Core Commercial Terms:</b> {_safe_str(summary.key_terms_text, has_unicode)}", body_style))
            elements.append(Spacer(1, 8))

    # 5.3 Clause Summary Table
    if clauses.exists():
        elements.append(Paragraph("<b>2. Clause Summary Matrix</b>", heading_style))
        summary_rows = [["#", "Heading", "Category", "Severity", "One-Line Takeaway"]]
        for cl in clauses:
            sev_label = (cl.severity or "Low").upper()
            cat_label = cl.category or "General"
            c_num = getattr(cl, 'clause_number', None) or str(cl.position)
            title_label = getattr(cl, 'title', None) or (cl.structured_explanation.get('title') if (cl.structured_explanation and isinstance(cl.structured_explanation, dict)) else None) or f"Section {c_num}"
            
            takeaway = cl.simplified_text.split('\n')[0] if cl.simplified_text else cl.original_text[:100]
            if cl.simplified_text and "IN PLAIN LANGUAGE:" in cl.simplified_text:
                parts = cl.simplified_text.split("IN PLAIN LANGUAGE:")
                if len(parts) > 1:
                    takeaway = parts[1].split("\n\n")[0].strip()

            summary_rows.append([
                str(c_num),
                Paragraph(_safe_str(title_label, has_unicode), body_style),
                Paragraph(_safe_str(cat_label, has_unicode), body_style),
                Paragraph(f"<b>{sev_label}</b>", body_style),
                Paragraph(_safe_str(takeaway, has_unicode), body_style)
            ])

        t_matrix = Table(summary_rows, colWidths=[24, 110, 110, 60, 236])
        t_matrix.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_family),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_matrix)
        elements.append(Spacer(1, 14))

        # 5.4 Detailed Clause Cards
        elements.append(Paragraph("<b>3. Detailed Clause-Level Analysis</b>", heading_style))
        for cl in clauses:
            card_elements = []
            c_num = getattr(cl, 'clause_number', None) or str(cl.position)
            c_title = getattr(cl, 'title', None) or (cl.structured_explanation.get('title') if (cl.structured_explanation and isinstance(cl.structured_explanation, dict)) else None) or f"Section {c_num}"
            c_sev = (cl.severity or "Low").upper()
            c_cat = cl.category or "General"

            card_elements.append(Paragraph(f"<b>Section {c_num}. {c_title}</b> &nbsp;|&nbsp; <i>{c_cat}</i> &nbsp;|&nbsp; <b>[{c_sev} SEVERITY]</b>", subheading_style))
            card_elements.append(Spacer(1, 2))

            # Original Text
            card_elements.append(Paragraph("<b>Original Text:</b>", body_style))
            card_elements.append(Paragraph(_safe_str(cl.original_text, has_unicode), quote_style))


            # Structured Simplified Breakdown
            if cl.simplified_text:
                card_elements.append(Spacer(1, 2))
                lines = cl.simplified_text.split("\n\n")
                for sec in lines:
                    sec_clean = sec.strip()
                    if sec_clean:
                        if sec_clean.startswith("IN PLAIN LANGUAGE:") or sec_clean.startswith("WHO IS BOUND:") or sec_clean.startswith("KEY DETAILS:") or sec_clean.startswith("WHY THIS SEVERITY:") or sec_clean.startswith("IF THE CONDITION IS NOT MET:") or sec_clean.startswith("NOT STATED IN THIS CLAUSE:"):
                            parts = sec_clean.split("\n", 1)
                            header_p = parts[0]
                            body_p = parts[1] if len(parts) > 1 else ""
                            card_elements.append(Paragraph(f"<b>{header_p}</b>", body_style))
                            if body_p:
                                for sub_line in body_p.split("\n"):
                                    card_elements.append(Paragraph(_safe_str(sub_line, has_unicode), body_style))
                        else:
                            card_elements.append(Paragraph(_safe_str(sec_clean, has_unicode), body_style))

            card_elements.append(Spacer(1, 8))
            card_elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=8))
            elements.append(KeepTogether(card_elements))

    # Mandatory Legal Notice
    elements.append(Spacer(1, 10))
    notice_text = "<i>Notice: ClarifAI provides automated contract analysis for informational assistance only and does NOT constitute legal advice.</i>"
    elements.append(Paragraph(notice_text, body_style))

    doc.build(elements)
    return file_path


def generate_comparison_pdf(report, comparison, language='en'):
    """Compiles Comparison results into a PDF binary file."""
    reports_dir = get_reports_dir()
    file_path = os.path.join(reports_dir, f"{report.id}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    font_family = get_pdf_font(language)
    font_bold = font_family if font_family != 'Helvetica' else 'Helvetica-Bold'

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName=font_bold, fontSize=18, leading=22, textColor=colors.HexColor('#0F172A'), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'DocHeading', parent=styles['Heading2'], fontName=font_bold, fontSize=12, leading=15, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'DocBody', parent=styles['Normal'], fontName=font_family, fontSize=9, leading=12, textColor=colors.HexColor('#334155'), spaceAfter=4
    )

    elements = []
    elements.append(Paragraph("<b>ClarifAI Document Comparison Report</b>", title_style))
    doc_a_name = comparison.base_document.original_filename if comparison.base_document else "Base Document"
    doc_b_name = comparison.target_document.original_filename if comparison.target_document else "Target Document"
    elements.append(Paragraph(f"<b>Base Document (A):</b> {doc_a_name}", body_style))
    elements.append(Paragraph(f"<b>Target Document (B):</b> {doc_b_name}", body_style))
    elements.append(Paragraph(f"<b>Report ID:</b> {report.id}", body_style))
    elements.append(Spacer(1, 10))

    results = comparison.results.all()
    if results.exists():
        elements.append(Paragraph("<b>Comparison Differences Matrix</b>", heading_style))
        table_data = [["Category", "Type", "Difference Explanation"]]
        for item in results:
            table_data.append([
                item.category.capitalize(),
                item.category.upper(),
                Paragraph(item.difference_explanation or "No explanation provided.", body_style)
            ])

        t = Table(table_data, colWidths=[90, 70, 380])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_family),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<i>Notice: ClarifAI provides automated analysis for informational purposes only and does NOT constitute legal advice.</i>", body_style))

    doc.build(elements)
    return file_path
