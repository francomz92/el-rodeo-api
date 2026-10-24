from __future__ import annotations

from typing import ClassVar

from src.reports.application.dto.report_spec import ReportSpec
from src.reports.infrastructure.adapters.export.pdf_renderer import render_pdf


class PdfExporter:
    """Renders ReportSpec documents as downloadable PDFs."""

    media_type: ClassVar[str] = "application/pdf"
    file_extension: ClassVar[str] = "pdf"

    def export(self, spec: ReportSpec) -> bytes:
        return render_pdf(spec)
