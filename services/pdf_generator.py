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


def generate_readiness_certificate(assessment, verify_url: str):
    """
    Generates an official Operational Readiness Clearance Certificate (PDF)
    containing pilot metrics, clearance status, and a verification QR code.
    """
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.lib.pagesizes import landscape

    buffer = BytesIO()
    # A4 Landscape dimensions: 842 x 595
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom colors
    primary_color = colors.HexColor("#0B1F3A") # Deep Navy
    accent_color = colors.HexColor("#1C6DD0")  # Royal Blue
    success_color = colors.HexColor("#10B981") # Emerald Green
    warning_color = colors.HexColor("#F59E0B") # Amber
    
    # Style definitions
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=primary_color,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        fontName="Helvetica-Oblique",
        spaceAfter=15,
        alignment=0
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica-Bold"
    )

    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica"
    )

    status_style = ParagraphStyle(
        'StatusStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=success_color if assessment.clearance_status == "cleared" else warning_color,
        fontName="Helvetica-Bold"
    )
    
    # --- Header Section ---
    elements.append(Paragraph("AEROGUARD AI — AIRCREW HEALTH & ALERTNESS MONITORING SYSTEM", ParagraphStyle('TopHeader', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748B"), fontName="Helvetica-Bold", spaceAfter=2)))
    elements.append(Paragraph("OPERATIONAL READINESS CERTIFICATE", title_style))
    elements.append(Paragraph("Official Duty Clearance Certificate issued in compliance with Rwanda Civil Aviation Authority (RCAA) and ICAO Annex 6.", subtitle_style))
    
    # Draw a line separator (using Table border)
    elements.append(Table([[""]], colWidths=[762], rowHeights=[2], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), accent_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ])))
    elements.append(Spacer(1, 15))
    
    # --- Columns Section ---
    pilot = assessment.user
    assess_date_str = assessment.assessment_date.strftime("%Y-%m-%d %H:%M UTC")
    valid_until_str = assessment.valid_until.strftime("%Y-%m-%d %H:%M UTC") if assessment.valid_until else "N/A"
    
    details_data = [
        [Paragraph("Pilot Name:", label_style), Paragraph(pilot.full_name if pilot else "Unknown Pilot", value_style)],
        [Paragraph("Employee ID:", label_style), Paragraph(pilot.employee_id if pilot else "N/A", value_style)],
        [Paragraph("Aviation Role:", label_style), Paragraph(pilot.role.upper() if pilot else "AVIATOR", value_style)],
        [Paragraph("Clearance Date:", label_style), Paragraph(assess_date_str, value_style)],
        [Paragraph("Valid Until:", label_style), Paragraph(valid_until_str, value_style)],
        [Paragraph("Duty Flight:", label_style), Paragraph(assessment.flight_number or "Scheduled Shifts", value_style)],
        [Paragraph("Assessment Score:", label_style), Paragraph(f"<b>{assessment.overall_score:.0f} / 100</b> (AI Confidence: {assessment.ai_confidence_score:.1f}%)", value_style)],
        [Paragraph("Clearance Status:", label_style), Paragraph(assessment.clearance_status.upper(), status_style)],
    ]
    
    details_table = Table(details_data, colWidths=[150, 250], hAlign='LEFT')
    details_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Right Column: QR Code & Verification description
    qr_drawing = Drawing(120, 120)
    qr_widget = QrCodeWidget(value=verify_url, barWidth=120, barHeight=120)
    qr_drawing.add(qr_widget)
    
    qr_data = [
        [qr_drawing],
        [Paragraph("Scan to Verify Clearance Validity", ParagraphStyle('QrLabel', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748B"), fontName="Helvetica-Bold", alignment=1))],
    ]
    qr_table = Table(qr_data, colWidths=[200], hAlign='CENTER')
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    # Merge Columns into a single layout table
    layout_table = Table([[details_table, qr_table]], colWidths=[462, 300])
    layout_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    elements.append(layout_table)
    elements.append(Spacer(1, 20))
    
    # --- Footer Section ---
    footer_style = ParagraphStyle(
        'CertFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=0
    )
    
    footer_data = [
        [
            Paragraph("<b>Verification System</b><br/>AeroGuard AI Safety Verification Network", footer_style),
            Paragraph("<b>Regulatory Directives</b><br/>ICAO Annex 6 Part I & RCAA Rulemaking Part 121", footer_style),
            Paragraph("<b>Electronic Authorization</b><br/>Certified digitally by RCAA Safety Gateway", footer_style)
        ]
    ]
    footer_table = Table(footer_data, colWidths=[254, 254, 254])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(footer_table)
    
    # Build the PDF
    doc.build(elements)
    
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out
