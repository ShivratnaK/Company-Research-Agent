from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io, datetime

BRAND = colors.HexColor("#6366f1")
DARK  = colors.HexColor("#18181b")
GRAY  = colors.HexColor("#71717a")
LIGHT = colors.HexColor("#f4f4f5")
WHITE = colors.white


def generate_pdf(company_data, competitors):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontSize=24, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=4, alignment=TA_LEFT)
    sub_style   = ParagraphStyle("sub",   fontSize=11, textColor=colors.HexColor("#c7d2fe"), fontName="Helvetica", spaceAfter=2)
    h2_style    = ParagraphStyle("h2",    fontSize=14, textColor=DARK,  fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6)
    label_style = ParagraphStyle("label", fontSize=8,  textColor=GRAY,  fontName="Helvetica-Bold", spaceAfter=2, leading=10)
    body_style  = ParagraphStyle("body",  fontSize=10, textColor=DARK,  fontName="Helvetica", spaceAfter=4, leading=14)
    link_style  = ParagraphStyle("link",  fontSize=10, textColor=BRAND, fontName="Helvetica", spaceAfter=4)

    elements = []

    # Header banner
    header_data = [[
        Paragraph(f"🔍 {company_data.get('company_name', 'Company Research Report')}", title_style),
        Paragraph(f"Generated {datetime.datetime.now().strftime('%B %d, %Y')}", sub_style)
    ]]
    header_table = Table(header_data, colWidths=[130*mm, 40*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BRAND),
        ("PADDING",    (0,0), (-1,-1), 14),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (1,0), (1,0),   "RIGHT"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))

    def field(label, value):
        elements.append(Paragraph(label.upper(), label_style))
        elements.append(Paragraph(str(value) if value and value != "N/A" else "—", body_style))
        elements.append(Spacer(1, 3*mm))

    # Company info section
    elements.append(Paragraph("Company Information", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=6))

    info_items = [
        ["Company Name", company_data.get("company_name", "N/A")],
        ["Website",      company_data.get("website", "N/A")],
        ["Phone",        company_data.get("phone", "N/A")],
        ["Address",      company_data.get("address", "N/A")],
    ]
    for pairs in [info_items[i:i+2] for i in range(0, len(info_items), 2)]:
        row_data = []
        for label, value in pairs:
            cell = [Paragraph(label.upper(), label_style), Paragraph(str(value), body_style)]
            row_data.append(cell)
        while len(row_data) < 2:
            row_data.append([""])
        t = Table([row_data], colWidths=[85*mm, 85*mm])
        t.setStyle(TableStyle([
            ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",(0,0), (-1,-1), 0),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 2*mm))

    elements.append(Spacer(1, 4*mm))

    # Summary
    elements.append(Paragraph("Company Summary", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=6))
    elements.append(Paragraph(company_data.get("summary", "N/A"), body_style))
    elements.append(Spacer(1, 4*mm))

    # Products & Services
    elements.append(Paragraph("Products & Services", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=6))
    elements.append(Paragraph(company_data.get("products_services", "N/A"), body_style))
    elements.append(Spacer(1, 4*mm))

    # Pain Points
    elements.append(Paragraph("AI-Generated Pain Points", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=6))
    elements.append(Paragraph(company_data.get("pain_points", "N/A"), body_style))
    elements.append(Spacer(1, 6*mm))

    # Competitors
    if competitors:
        elements.append(Paragraph("Competitor Analysis", h2_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND, spaceAfter=6))
        comp_data = [
            [Paragraph("COMPANY NAME", label_style), Paragraph("WEBSITE", label_style)]
        ]
        for c in competitors:
            comp_data.append([
                Paragraph(c.get("name", "—"), body_style),
                Paragraph(c.get("website", "—"), link_style)
            ])
        comp_table = Table(comp_data, colWidths=[85*mm, 85*mm])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0),  LIGHT),
            ("LINEBELOW",   (0,0), (-1,0),  0.5, GRAY),
            ("LINEBELOW",   (0,1), (-1,-1), 0.3, LIGHT),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING",(0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ]))
        elements.append(comp_table)

    # Footer
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("Generated by Company Research Agent — AI-powered business intelligence", 
        ParagraphStyle("footer", fontSize=8, textColor=GRAY, alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer
