import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.app.schemas.trip import TripResponse

def generate_trip_pdf(trip: TripResponse) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles matching NaviGo brand
    title_style = ParagraphStyle(
        'NaviGoTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0B1F33'),
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'NaviGoH2',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#13B8A6'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'NaviGoBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#102A43')
    )

    muted_style = ParagraphStyle(
        'NaviGoMuted',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B')
    )

    story = []

    # Brand Header
    story.append(Paragraph("NaviGo — Explore More. Plan Smarter.", muted_style))
    story.append(Paragraph(trip.title, title_style))
    meta_text = f"<b>Destination:</b> {trip.destination_slug.title()} &nbsp;|&nbsp; <b>Origin:</b> {trip.origin} &nbsp;|&nbsp; <b>Duration:</b> {trip.duration_days} Days &nbsp;|&nbsp; <b>Travelers:</b> {trip.travelers_count}"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 14))

    # Daily Timeline
    for day in trip.days:
        story.append(Paragraph(f"{day.day_badge}: {day.theme}", h2_style))
        for stop in day.stops:
            stop_text = f"• <b>{stop.time_of_day}:</b> {stop.place_name} — <i>{stop.activity}</i>"
            story.append(Paragraph(stop_text, body_style))
        if day.notes:
            story.append(Paragraph(f"<i>Note: {day.notes}</i>", muted_style))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))

    # Budget Table
    story.append(Paragraph("Estimated Budget Breakdown", h2_style))
    breakdown = trip.budget_breakdown.get("breakdown", {})
    table_data = [
        ["Category", "Estimated Amount (PKR)"],
        ["Transport", f"Rs. {breakdown.get('transport', 0):,}"],
        ["Accommodation", f"Rs. {breakdown.get('hotel', 0):,}"],
        ["Food & Dining", f"Rs. {breakdown.get('food', 0):,}"],
        ["Activities & Jeeps", f"Rs. {breakdown.get('activities', 0):,}"],
        ["Contingency Buffer", f"Rs. {breakdown.get('contingency', 0):,}"],
        ["Total Estimated", f"Rs. {trip.budget_breakdown.get('total_estimated_pkr', 0):,}"]
    ]

    table = Table(table_data, colWidths=[240, 240])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B1F33')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    # Safety Notice
    story.append(Paragraph("<b>Safety & Travel Notice:</b>", h2_style))
    disclaimer = "Road and weather conditions across Pakistan can shift quickly. All timings and itineraries are advisory. Always verify route clearances with local authorities (Rescue 1122 / KPK Tourism Police 1422)."
    story.append(Paragraph(disclaimer, muted_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
