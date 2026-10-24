"""PDF report rendering via reportlab, driven by declarative ReportSpec.

``render_pdf()`` is report-agnostic: it paints any ``ReportSpec`` with a
header, period line, table sections, totals sections, and a generation
stamp. Report-specific layout lives in application-spec builders, not here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.reports.application.dto.report_spec import (
    ReportSpec,
    TableSection,
    TotalsSection,
)


def render_pdf(spec: ReportSpec) -> bytes:
    """Render a ``ReportSpec`` as a PDF document.

    Args:
        spec: Declarative report layout with pre-formatted values.

    Returns:
        PDF document as bytes, ready for streaming.
    """
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
    elements.append(Paragraph(spec.title, styles["Title"]))
    elements.append(Spacer(1, 6 * mm))
    if spec.period_text is not None:
        elements.append(Paragraph(spec.period_text, styles["Normal"]))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    elements.append(Paragraph(f"Generado: {generated_at}", styles["Normal"]))
    elements.append(Spacer(1, 10 * mm))

    # ── Sections ──────────────────────────────────────────────────────
    for idx, section in enumerate(spec.sections):
        if idx > 0:
            elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(section.title, styles["Heading2"]))
        elements.append(Spacer(1, 3 * mm))

        if isinstance(section, TableSection):
            if section.rows:
                table = Table([section.headers] + section.rows, repeatRows=1)
                table.setStyle(_table_style())
                elements.append(table)
            else:
                elements.append(
                    Paragraph(section.empty_message, styles["Normal"]),
                )
        elif isinstance(section, TotalsSection):
            totals_table = Table(section.rows, colWidths=[120 * mm, 80 * mm])
            totals_table.setStyle(_totals_style())
            elements.append(totals_table)

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


def _totals_style() -> TableStyle:
    """Return the ``TableStyle`` for two-column totals tables."""
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0FE")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]
    )
