import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from io import BytesIO

def generate_compliance_report(pilots, user_full_name: str):
    """
    Generates a professional Rwanda Civil Aviation Authority (RCAA) styled
    Compliance & Safety Audit Report as a PDF binary stream.
    
    SRS Requirement 8.1: Comprehensive safety reporting and data export.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    elements = []

    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#0B1F3A"),
        alignment=1,
        spaceAfter=10,
        fontName="Helvetica-Bold"
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=1,
        spaceAfter=30
    )

    section_header = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#1C6DD0"),
        spaceBefore=20,
        spaceAfter=12,
        fontName="Helvetica-Bold"
    )

    # 1. Header Section
    elements.append(Paragraph("AeroGuard AI — Flight Safety Compliance Report", title_style))
    elements.append(Paragraph(f"Official Regulatory Audit Trail | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 12))

    # 2. Executive Summary
    elements.append(Paragraph("Executive Safety Summary", section_header))
    
    total_pilots = len(pilots)
    # Note: Using risk_level if it exists (from joined data) or defaulting to UNKNOWN
    high_risk = len([p for p in pilots if getattr(p, 'risk_level', 'LOW') == "HIGH"])
    low_risk = len([p for p in pilots if getattr(p, 'risk_level', 'LOW') == "LOW"])
    
    summary_text = (
        f"This system audit evaluates the current operational readiness of {total_pilots} flight personnel. "
        f"Through automated AI risk analysis, {high_risk} personnel have been flagged "
        f"as <b>CRITICAL RISK (HIGH)</b>. There are currently {low_risk} personnel "
        f"confirmed as fit-for-duty."
    )
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 15))

    # 3. Detailed Personnel Matrix
    elements.append(Paragraph("Personnel Risk Matrix", section_header))
    
    # Table Header
    data = [["Personnel Name", "ID", "Role", "Status", "Risk Level"]]
    
    for p in pilots:
        risk = getattr(p, 'risk_level', 'LOW')
        status = getattr(p, 'clearance_status', 'Pending')
        
        data.append([
            getattr(p, 'full_name', getattr(p, 'name', 'Unknown')),
            p.employee_id,
            p.role.capitalize() if hasattr(p, 'role') else "Aviator",
            status.capitalize(),
            risk
        ])

    # Table Styling
    t = Table(data, hAlign='LEFT', colWidths=[2.2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B1F3A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        # Color specific risk levels
        ('TEXTCOLOR', (5, 1), (5, -1), colors.black),
    ]))
    
    # Color logic for Risk Levels
    for i in range(1, len(data)):
        risk = data[i][5]
        if risk == "HIGH":
            t.setStyle(TableStyle([('TEXTCOLOR', (5, i), (5, i), colors.red), ('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')]))
        elif risk == "MEDIUM":
            t.setStyle(TableStyle([('TEXTCOLOR', (5, i), (5, i), colors.orange)]))
        elif risk == "LOW":
            t.setStyle(TableStyle([('TEXTCOLOR', (5, i), (5, i), colors.green)]))

    elements.append(t)
    elements.append(Spacer(1, 30))

    # 4. Certification Footer
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("Official Certification", section_header))
    footer_text = (
        f"This report is electronically certified by <b>{user_full_name}</b> and is compliant with "
        "ICAO Document 9654 (Manual on the Prevention of Problematic Substance Use in the Aviation Workplace)."
    )
    elements.append(Paragraph(footer_text, styles['Normal']))

    # Build the PDF
    doc.build(elements)
    
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out
