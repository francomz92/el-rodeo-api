"""PDF report generation via reportlab.

Generates downloadable PDF renditions of report data.  Currently supports
the sales summary report with header, weekly table, monthly table, and
totals footer.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_sales_report(
    tenant_name: str,
    from_date: date,
    to_date: date,
    data: dict,
) -> bytes:
    """Generate a PDF sales summary report as bytes.

    Args:
        tenant_name: Display name for the tenant header.
        from_date: Start of the report date range.
        to_date: End of the report date range.
        data: Sales summary dict — same shape as returned by
            ``ReportsService.get_sales_summary()`` (keys ``weekly``,
            ``monthly``, ``total``).

    Returns:
        PDF document as bytes, ready for streaming.
    """
    from io import BytesIO

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    elements: list = []

    # ── Header ────────────────────────────────────────────────────────
    elements.append(
        Paragraph(f"Reporte de Ventas — {tenant_name}", styles["Title"]),
    )
    elements.append(Spacer(1, 6 * mm))
    elements.append(
        Paragraph(
            f"Período: {from_date.isoformat()} — {to_date.isoformat()}",
            styles["Normal"],
        ),
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    elements.append(
        Paragraph(f"Generado: {generated_at}", styles["Normal"]),
    )
    elements.append(Spacer(1, 10 * mm))

    # ── Weekly table ──────────────────────────────────────────────────
    elements.append(Paragraph("Resumen Semanal", styles["Heading2"]))
    elements.append(Spacer(1, 3 * mm))
    weekly_data = data.get("weekly", [])
    if weekly_data:
        week_header = ["Semana", "Ingresos", "Ventas", "Precio Prom./Kg", "Peso Total"]
        week_rows = [
            [
                r["week_start"],
                f"${r['revenue']:,.2f}",
                str(r["sales_count"]),
                f"${r['avg_price_per_kg']:,.2f}",
                f"{r['total_weight']:,.1f} kg",
            ]
            for r in weekly_data
        ]
        week_table = Table([week_header] + week_rows, repeatRows=1)
        week_table.setStyle(_table_style())
        elements.append(week_table)
    else:
        elements.append(Paragraph("No hay datos semanales para el período seleccionado.", styles["Normal"]))
    elements.append(Spacer(1, 8 * mm))

    # ── Monthly table ─────────────────────────────────────────────────
    elements.append(Paragraph("Resumen Mensual", styles["Heading2"]))
    elements.append(Spacer(1, 3 * mm))
    monthly_data = data.get("monthly", [])
    if monthly_data:
        month_header = ["Mes", "Ingresos", "Ventas", "Precio Prom./Kg", "Peso Total"]
        month_rows = [
            [
                r["month_start"],
                f"${r['revenue']:,.2f}",
                str(r["sales_count"]),
                f"${r['avg_price_per_kg']:,.2f}",
                f"{r['total_weight']:,.1f} kg",
            ]
            for r in monthly_data
        ]
        month_table = Table([month_header] + month_rows, repeatRows=1)
        month_table.setStyle(_table_style())
        elements.append(month_table)
    else:
        elements.append(Paragraph("No hay datos mensuales para el período seleccionado.", styles["Normal"]))
    elements.append(Spacer(1, 10 * mm))

    # ── Totals footer ─────────────────────────────────────────────────
    elements.append(Paragraph("Totales", styles["Heading2"]))
    elements.append(Spacer(1, 3 * mm))
    total = data.get("total", {})
    total_rows = [
        ["Ingresos Totales", f"${total.get('revenue', 0):,.2f}"],
        ["Cantidad de Ventas", str(total.get("sales_count", 0))],
        ["Precio Promedio por Kg", f"${total.get('avg_price_per_kg', 0):,.2f}"],
        ["Peso Total", f"{total.get('total_weight', 0):,.1f} kg"],
    ]
    total_table = Table(total_rows, colWidths=[120 * mm, 80 * mm])
    total_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0FE")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]
        ),
    )
    elements.append(total_table)

    # ── Build ─────────────────────────────────────────────────────────
    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


def _table_style() -> TableStyle:
    """Return a standardised ``TableStyle`` for report tables."""
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0FE")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
