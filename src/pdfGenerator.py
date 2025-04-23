from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_pdf_from_data(data_rows, column_headers, output_stream):
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        'cellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        wordWrap='CJK'
    )

    # Build table data with headers
    table_data = [column_headers]
    for row in data_rows:
        table_data.append([Paragraph(str(cell), cell_style) for cell in row])

    # Create the PDF document
    doc = SimpleDocTemplate(
        output_stream,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18
    )

    title_style = ParagraphStyle(
        'titleStyle',
        parent=styles['Title'],
        alignment=1,
        fontSize=16,
        leading=20
    )

    story = []
    story.append(Paragraph("Weekly Retail Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 18))

    col_width = (doc.width - 20) / len(column_headers)
    table = Table(table_data, repeatRows=1, colWidths=[col_width] * len(column_headers))

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
    ]))

    story.append(table)
    doc.build(story)