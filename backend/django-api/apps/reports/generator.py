"""
PDF Report Compiler Engine (PRD Ch. 28.1 & Phase 12).
Uses ReportLab (Engineering Implementation Detail) to compile persisted Document
and Comparison data into structured PDF reports on the Django service layer.
"""
import os
import logging
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def get_reports_dir():
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def get_pdf_font(language='en'):
    """
    Resolves Unicode font for non-Latin languages (e.g. Hindi Devanagari)
    to prevent PostScript Type 1 Helvetica character substitution.
    """
    if language == 'hi':
        candidate_fonts = [
            ('Nirmala', 'C:/Windows/Fonts/Nirmala.ttc', 0),
            ('Mangal', 'C:/Windows/Fonts/mangal.ttf', None),
            ('Arial', 'C:/Windows/Fonts/arial.ttf', None),
            ('NotoSansDevanagari', '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf', None),
            ('FreeSans', '/usr/share/fonts/truetype/freefont/FreeSans.ttf', None),
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
    Compiles Document analysis summary and clauses into a PDF binary file.
    Saves file securely under MEDIA_ROOT/reports/<report_id>.pdf.
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

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    elements = []
    doc_title = "ClarifAI Document Analysis Report" if language != 'hi' else "ClarifAI दस्तावेज़ विश्लेषण रिपोर्ट"
    elements.append(Paragraph(doc_title, title_style))
    elements.append(Paragraph(f"<b>Document:</b> {document.original_filename}", body_style))
    elements.append(Paragraph(f"<b>Report ID:</b> {report.id} | <b>Language:</b> {(language or 'EN').upper()}", body_style))
    elements.append(Spacer(1, 12))

    # Summary Section
    summary = getattr(document, 'summary', None)
    if summary:
        purpose = summary.purpose_text
        obligations = summary.obligations_text
        key_terms = summary.key_terms_text
        key_risks = summary.key_risks_text

        if language == 'hi':
            from django.core.cache import cache
            cached_trans = cache.get(f"doc_summary_hi_{document.id}")
            if cached_trans and cached_trans.get("translation_available"):
                purpose = cached_trans.get("purpose_text") or purpose
                obligations = cached_trans.get("obligations_text") or obligations
                key_terms = cached_trans.get("key_terms_text") or key_terms
                key_risks = cached_trans.get("key_risks_text") or key_risks
            elif getattr(summary, 'purpose_text_hi', None):
                purpose = summary.purpose_text_hi
                obligations = getattr(summary, 'obligations_text_hi', obligations)
                key_terms = getattr(summary, 'key_terms_text_hi', key_terms)
                key_risks = getattr(summary, 'key_risks_text_hi', key_risks)

        title_header = "Executive Overview" if language != 'hi' else "कार्यकारी सारांश (Executive Overview)"
        elements.append(Paragraph(title_header, heading_style))
        if purpose:
            label = "Purpose" if language != 'hi' else "उद्देश्य (Purpose)"
            elements.append(Paragraph(f"<b>{label}:</b> {purpose}", body_style))
        if obligations:
            label = "Obligations" if language != 'hi' else "दायित्व (Obligations)"
            elements.append(Paragraph(f"<b>{label}:</b> {obligations}", body_style))
        if key_terms:
            label = "Key Terms" if language != 'hi' else "प्रमुख शर्तें (Key Terms)"
            elements.append(Paragraph(f"<b>{label}:</b> {key_terms}", body_style))
        if key_risks:
            label = "Key Risks" if language != 'hi' else "प्रमुख जोखिम (Key Risks)"
            elements.append(Paragraph(f"<b>{label}:</b> {key_risks}", body_style))
        elements.append(Spacer(1, 12))

    # Risk-Classified Clauses
    clauses = document.clauses.all().order_by('position')
    if clauses.exists():
        header_text = "Risk-Classified Clauses" if language != 'hi' else "जोखिम-वर्गीकृत खंड (Risk-Classified Clauses)"
        elements.append(Paragraph(header_text, heading_style))

        col_pos = "Pos" if language != 'hi' else "क्रमांक"
        col_sev = "Severity" if language != 'hi' else "गंभीरता"
        col_cat = "Category" if language != 'hi' else "श्रेणी"
        col_text = "Original Text / Summary" if language != 'hi' else "मूल पाठ / सरलीकृत सारांश"

        table_data = [[col_pos, col_sev, col_cat, col_text]]

        trans_map = {}
        if language == 'hi':
            from django.core.cache import cache
            cached_clauses = cache.get(f"doc_clauses_hi_{document.id}")
            if cached_clauses and cached_clauses.get("translation_available"):
                trans_map = cached_clauses.get("clauses_map", {})

        for clause in clauses:
            simplified = clause.simplified_text
            if language == 'hi':
                if str(clause.id) in trans_map:
                    simplified = trans_map[str(clause.id)].get('simplified_text_hi') or simplified
                elif getattr(clause, 'simplified_text_hi', None):
                    simplified = clause.simplified_text_hi

            table_data.append([
                str(clause.position),
                (clause.severity or "UNKNOWN").upper(),
                clause.category or "General",
                Paragraph(simplified or clause.original_text[:150], body_style)
            ])

        t = Table(table_data, colWidths=[36, 64, 90, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_family),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    # Mandatory Legal Framing
    elements.append(Spacer(1, 16))
    notice_text = (
        "<i>Notice: ClarifAI provides automated analysis for informational purposes only and does NOT constitute legal advice.</i>"
        if language != 'hi' else
        "<i>सूचना: ClarifAI केवल सूचनात्मक उद्देश्यों के लिए स्वचालित विश्लेषण प्रदान करता है और यह औपचारिक कानूनी सलाह नहीं है।</i>"
    )
    elements.append(Paragraph(notice_text, body_style))

    doc.build(elements)
    return file_path


def generate_comparison_pdf(report, comparison, language='en'):
    """
    Compiles Comparison results into a PDF binary file.
    Saves file securely under MEDIA_ROOT/reports/<report_id>.pdf.
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

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName=font_family,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    elements = []
    comp_title = "ClarifAI Document Comparison Report" if language != 'hi' else "ClarifAI दस्तावेज़ तुलना रिपोर्ट"
    elements.append(Paragraph(comp_title, title_style))
    doc_a_name = comparison.base_document.original_filename if comparison.base_document else "Deleted Document"
    doc_b_name = comparison.target_document.original_filename if comparison.target_document else "Deleted Document"
    label_a = "Base Document (A)" if language != 'hi' else "मूल दस्तावेज़ (A)"
    label_b = "Target Document (B)" if language != 'hi' else "लक्षित दस्तावेज़ (B)"
    elements.append(Paragraph(f"<b>{label_a}:</b> {doc_a_name}", body_style))
    elements.append(Paragraph(f"<b>{label_b}:</b> {doc_b_name}", body_style))
    elements.append(Paragraph(f"<b>Report ID:</b> {report.id} | <b>Language:</b> {(language or 'EN').upper()}", body_style))
    elements.append(Spacer(1, 12))

    results = comparison.results.all()
    if results.exists():
        matrix_header = "Comparison Matrix & Differences" if language != 'hi' else "तुलना मैट्रिक्स और अंतर (Comparison Matrix)"
        elements.append(Paragraph(matrix_header, heading_style))

        col_cat = "Category" if language != 'hi' else "श्रेणी"
        col_type = "Type" if language != 'hi' else "प्रकार"
        col_diff = "Difference Explanation" if language != 'hi' else "अंतर विवरण"

        table_data = [[col_cat, col_type, col_diff]]
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
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    # Mandatory Legal Framing
    elements.append(Spacer(1, 16))
    notice_text = (
        "<i>Notice: ClarifAI provides automated analysis for informational purposes only and does NOT constitute legal advice.</i>"
        if language != 'hi' else
        "<i>सूचना: ClarifAI केवल सूचनात्मक उद्देश्यों के लिए स्वचालित विश्लेषण प्रदान करता है और यह औपचारिक कानूनी सलाह नहीं है।</i>"
    )
    elements.append(Paragraph(notice_text, body_style))

    doc.build(elements)
    return file_path
