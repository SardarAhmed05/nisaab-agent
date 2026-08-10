from datetime import date
import csv
import io
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.crud import get_transactions
from app.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/transactions")
async def transactions(
    limit: int = Query(default=10, ge=1, le=1000),
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    txns = await get_transactions(
        session,
        user_id,
        limit=limit
    )

    return txns


@router.get("/transactions/export")
async def export_transactions_csv(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    txns = await get_transactions(
        session,
        user_id,
        limit=5000
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow(["ID", "Date", "Type", "Category", "Description", "Amount (PKR)", "Source", "Confidence"])

    # Write Data Rows
    for txn in txns:
        writer.writerow([
            txn.id,
            str(txn.date),
            txn.type.capitalize(),
            txn.category,
            txn.description,
            txn.amount,
            txn.source or "",
            txn.confidence
        ])

    csv_data = output.getvalue()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=nisaab_transactions.csv"
        }
    )


@router.get("/transactions/export/pdf")
async def export_transactions_pdf(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    txns = await get_transactions(
        session,
        user_id,
        limit=5000
    )

    pdf_bytes = generate_pdf_report(txns)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=nisaab_transactions.pdf"
        }
    )


def generate_pdf_report(transactions):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor('#0f1512'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#58665e'),
            spaceAfter=14
        )

        elements.append(Paragraph("Nisaab • Financial Transaction Report", title_style))
        elements.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')} | Total Records: {len(transactions)}", subtitle_style))

        data = [["Date", "Type", "Category", "Description", "Amount (PKR)"]]
        for txn in transactions:
            sign = "+" if txn.type == "income" else "-"
            data.append([
                str(txn.date),
                txn.type.capitalize(),
                txn.category,
                txn.description[:35],
                f"{sign} Rs {txn.amount:,.2f}"
            ])

        t = Table(data, colWidths=[75, 65, 95, 180, 125])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f1512')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f7f9f7')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6e2')),
        ]))
        elements.append(t)

        doc.build(elements)
        return buffer.getvalue()
    except ImportError:
        return build_simple_pdf_bytes(transactions)


def build_simple_pdf_bytes(transactions):
    content_stream = []
    content_stream.append("BT")
    content_stream.append("/F2 18 Tf")
    content_stream.append("40 750 Td")
    content_stream.append("(Nisaab - Financial Transaction Report) Tj")
    content_stream.append("ET")

    content_stream.append("BT")
    content_stream.append("/F1 10 Tf")
    content_stream.append("40 732 Td")
    content_stream.append(f"(Generated on {date.today().strftime('%Y-%m-%d')} | Total Records: {len(transactions)}) Tj")
    content_stream.append("ET")

    y = 695
    content_stream.append("BT")
    content_stream.append("/F2 9.5 Tf")
    content_stream.append(f"40 {y} Td")
    content_stream.append("(Date          Type       Category        Description                           Amount) Tj")
    content_stream.append("ET")
    y -= 12

    content_stream.append(f"40 {y} m 560 {y} l S")
    y -= 14

    for txn in transactions[:45]:
        if y < 45:
            break
        sign = "+" if txn.type == "income" else "-"
        date_str = str(txn.date).ljust(12)
        type_str = txn.type.capitalize().ljust(10)
        cat_str = txn.category[:12].ljust(14)
        desc_str = txn.description[:28].ljust(30)
        amt_str = f"{sign}Rs {txn.amount:,.2f}"
        row_line = f"{date_str}{type_str}{cat_str}{desc_str}{amt_str}"
        row_line = row_line.replace("(", "\\(").replace(")", "\\)")

        content_stream.append("BT")
        content_stream.append("/F1 8.5 Tf")
        content_stream.append(f"40 {y} Td")
        content_stream.append(f"({row_line}) Tj")
        content_stream.append("ET")
        y -= 13

    content = "\n".join(content_stream).encode("latin-1", errors="replace")

    objects = []
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n")
    objects.append(f"4 0 obj\n<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"\nendstream\nendobj\n")
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    objects.append("6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")

    buf = bytearray()
    buf.extend(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(buf))
        if isinstance(obj, str):
            buf.extend(obj.encode("latin-1"))
        else:
            buf.extend(obj)

    xref_start = len(buf)
    buf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin-1"))
    for off in offsets[1:]:
        buf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

    buf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("latin-1"))
    return bytes(buf)