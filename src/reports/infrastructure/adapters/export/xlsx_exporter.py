"""XLSX report rendering via xlsxwriter, driven by declarative ReportSpec.

``render_xlsx()`` is report-agnostic: it mirrors the PDF layout — a
titled sheet with the period line, then each section as a titled block
with headers and one row per table row.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import ClassVar

import xlsxwriter

from src.reports.application.dto.report_spec import (
    ReportSpec,
    TableSection,
    TotalsSection,
)

MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FILE_EXTENSION = "xlsx"


class XlsxExporter:
    """Renders ReportSpec documents as XLSX workbooks."""

    media_type: ClassVar[str] = MIME_TYPE
    file_extension: ClassVar[str] = FILE_EXTENSION

    def export(self, spec: ReportSpec) -> bytes:
        return render_xlsx(spec)


def render_xlsx(spec: ReportSpec) -> bytes:
    """Render a ``ReportSpec`` as an XLSX workbook.

    Args:
        spec: Declarative report layout with pre-formatted values.

    Returns:
        XLSX workbook as bytes, ready for streaming.
    """
    buf = BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    sheet = workbook.add_worksheet()

    title_fmt = workbook.add_format({"bold": True, "font_size": 14})
    meta_fmt = workbook.add_format({"italic": True, "font_size": 10})
    section_fmt = workbook.add_format({"bold": True, "font_size": 11})
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#E8F0FE", "border": 1})
    cell_fmt = workbook.add_format({"border": 1})

    row = 0
    sheet.write(row, 0, spec.title, title_fmt)
    row += 1
    if spec.period_text is not None:
        sheet.write(row, 0, spec.period_text, meta_fmt)
        row += 1
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sheet.write(row, 0, f"Generado: {generated_at}", meta_fmt)
    row += 2

    for section in spec.sections:
        sheet.write(row, 0, section.title, section_fmt)
        row += 1

        if isinstance(section, TableSection):
            for col_idx, header in enumerate(section.headers):
                sheet.write(row, col_idx, header, header_fmt)
            row += 1

            if section.rows:
                for table_row in section.rows:
                    for col_idx, value in enumerate(table_row):
                        sheet.write(row, col_idx, value, cell_fmt)
                    row += 1
            else:
                sheet.write(row, 0, section.empty_message, meta_fmt)
                row += 1
        elif isinstance(section, TotalsSection):
            for label, value in section.rows:
                sheet.write(row, 0, label, header_fmt)
                sheet.write(row, 1, value, cell_fmt)
                row += 1
        row += 1  # blank line between sections

    workbook.close()
    return buf.getvalue()
