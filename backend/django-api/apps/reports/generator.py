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

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    elements = []
    elements.append(Paragraph("ClarifAI Document Analysis Report", title_style))
    elements.append(Paragraph(f"<b>Document:</b> {document.original_filename}", body_style))
    elements.append(Paragraph(f"<b>Report ID:</b> {report.id} | <b>Language:</b> {language.upper()}", body_style))
    elements.append(Spacer(1, 12))

    # Summary Section
    summary = getattr(document, 'summary', None)
    if summary:
        elements.append(Paragraph("Executive Overview", heading_style))
        if summary.purpose_text:
            elements.append(Paragraph(f"<b>Purpose:</b> {summary.purpose_text}", body_style))
        if summary.obligations_text:
            elements.append(Paragraph(f"<b>Obligations:</b> {summary.obligations_text}", body_style))
        if summary.key_terms_text:
            elements.append(Paragraph(f"<b>Key Terms:</b> {summary.key_terms_text}", body_style))
        if summary.key_risks_text:
            elements.append(Paragraph(f"<b>Key Risks:</b> {summary.key_risks_text}", body_style))
        elements.append(Spacer(1, 12))


    # Risk-Classified Clauses
    clauses = document.clauses.all().order_by('position')
    if clauses.exists():
        elements.append(Paragraph("Risk-Classified Clauses", heading_style))
        table_data = [["Pos", "Severity", "Category", "Original Text / Summary"]]
        for clause in clauses:
            table_data.append([
                str(clause.position),
                clause.severity.upper(),
                clause.category or "General",
                Paragraph(clause.simplified_text or clause.original_text[:150], body_style)
            ])

        t = Table(table_data, colWidths=[36, 64, 90, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    # Mandatory Legal Framing
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("<i>Notice: ClarifAI provides automated analysis for informational purposes only and does NOT constitute legal advice.</i>", body_style))

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

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    elements = []
    elements.append(Paragraph("ClarifAI Document Comparison Report", title_style))
    doc_a_name = comparison.base_document.original_filename if comparison.base_document else "Deleted Document"
    doc_b_name = comparison.target_document.original_filename if comparison.target_document else "Deleted Document"
    elements.append(Paragraph(f"<b>Base Document (A):</b> {doc_a_name}", body_style))
    elements.append(Paragraph(f"<b>Target Document (B):</b> {doc_b_name}", body_style))
    elements.append(Paragraph(f"<b>Report ID:</b> {report.id} | <b>Language:</b> {language.upper()}", body_style))
    elements.append(Spacer(1, 12))

    results = comparison.results.all()
    if results.exists():
        elements.append(Paragraph("Comparison Matrix & Differences", heading_style))
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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)

    # Mandatory Legal Framing
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("<i>Notice: ClarifAI provides automated analysis for informational purposes only and does NOT constitute legal advice.</i>", body_style))

    doc.build(elements)
    return file_path
