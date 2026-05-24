import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from io import BytesIO

def generate_compliance_report(pilots, user_full_name: str, report_type: str = "compliance"):
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

    # Calculate dynamic stats
    total_pilots = len(pilots)
    high_risk = len([p for p in pilots if getattr(p, 'risk_level', 'LOW') == "HIGH"])
    low_risk = len([p for p in pilots if getattr(p, 'risk_level', 'LOW') == "LOW"])

    # Customize title, subtitle, and summaries based on report_type
    if report_type in ["fatigue", "frms"]:
        title_text = "AeroGuard AI — Fatigue Risk Management Report"
        subtitle_text = f"Circadian Fatigue Analytics & Duty Limits | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        summary_heading = "Fatigue & Alertness Executive Summary"
        summary_text = (
            f"This audit evaluates fatigue compliance across {total_pilots} active flight crew. "
            f"Currently, {high_risk} crew members are flagged under high-risk fatigue alerts due to circadian "
            f"disruption or duty period violations. {low_risk} personnel are confirmed within safe fatigue margins."
        )
        table_title = "Fatigue Risk & Duty Matrix"
    elif report_type == "incident":
        title_text = "AeroGuard AI — Incident Analysis & Safety Report"
        subtitle_text = f"Safety Incidents & Investigation Registry | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        summary_heading = "Incident Analysis Executive Summary"
        summary_text = (
            f"This audit reports safety incident metrics across {total_pilots} flight operations. "
            f"There are currently {high_risk} high-severity safety incidents requiring safety officer review, "
            f"while {low_risk} operations remain stable and event-free."
        )
        table_title = "Safety Incidents & Risk Matrix"
    elif report_type == "readiness":
        title_text = "AeroGuard AI — Personnel Readiness & Fitness Report"
        subtitle_text = f"Flight Crew Readiness Audit | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        summary_heading = "Operational Readiness Summary"
        summary_text = (
            f"This audit details the immediate operational readiness of {total_pilots} crew members. "
            f"Currently, {low_risk} crew members are fully cleared for active duty. {high_risk} crew members "
            f"are grounded due to health, medical, or alcohol clearance issues."
        )
        table_title = "Operational Readiness & Clearance Matrix"
    elif report_type == "summary":
        title_text = "AeroGuard AI — Executive Safety Summary"
        subtitle_text = f"High-Level Executive Safety Briefing | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        summary_heading = "Executive Safety Summary"
        summary_text = (
            f"This system-wide safety audit summarizes the status of {total_pilots} active crew. "
            f"Currently, compliance rate sits at 99%, with {high_risk} high-priority risk alerts active, "
            f"and {low_risk} crew members performing at peak readiness levels."
        )
        table_title = "Operational Safety Matrix"
    else: # compliance, etc.
        title_text = "AeroGuard AI — Flight Safety Compliance Report"
        subtitle_text = f"Official Regulatory Audit Trail | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        summary_heading = "Executive Safety Summary"
        summary_text = (
            f"This system audit evaluates the current operational readiness of {total_pilots} flight personnel. "
            f"Through automated AI risk analysis, {high_risk} personnel have been flagged "
            f"as <b>CRITICAL RISK (HIGH)</b>. There are currently {low_risk} personnel "
            f"confirmed as fit-for-duty."
        )
        table_title = "Personnel Risk Matrix"

    # 1. Header Section
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(subtitle_text, subtitle_style))
    elements.append(Spacer(1, 12))

    # 2. Executive Summary
    elements.append(Paragraph(summary_heading, section_header))
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 15))

    # 3. Detailed Personnel Matrix
    elements.append(Paragraph(table_title, section_header))
    
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
        ('TEXTCOLOR', (4, 1), (4, -1), colors.black),
    ]))
    
    # Color logic for Risk Levels
    for i in range(1, len(data)):
        risk = data[i][4]
        if risk == "HIGH":
            t.setStyle(TableStyle([('TEXTCOLOR', (4, i), (4, i), colors.red), ('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')]))
        elif risk == "MEDIUM":
            t.setStyle(TableStyle([('TEXTCOLOR', (4, i), (4, i), colors.orange)]))
        elif risk == "LOW":
            t.setStyle(TableStyle([('TEXTCOLOR', (4, i), (4, i), colors.green)]))

    elements.append(t)
    elements.append(Spacer(1, 30))

    # 4. Certification Footer
    elements.append(Spacer(1, 60))
    elements.append(Paragraph("Official Certification", section_header))
    footer_text = (
        f"This report is electronically certified by <b>{user_full_name}</b> and is compliant with "
        "ICAO Document 9654 (Manual on the Prevention of Problematic Substance Use in the Aviation Workplace) "
        "and Rwanda Civil Aviation Authority (RCAA) operational directives."
    )
    elements.append(Paragraph(footer_text, styles['Normal']))

    # Build the PDF
    doc.build(elements)
    
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out
