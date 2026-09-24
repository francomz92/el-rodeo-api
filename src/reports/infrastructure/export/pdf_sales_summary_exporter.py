from __future__ import annotations

from datetime import date

from src.reports.infrastructure.export.pdf_renderer import generate_sales_report


class PdfSalesSummaryExporter:
    def export_sales_summary(
        self,
        *,
        tenant_name: str,
        from_date: date,
        to_date: date,
        data: dict,
    ) -> bytes:
        return generate_sales_report(
            tenant_name=tenant_name,
            from_date=from_date,
            to_date=to_date,
            data=data,
        )
