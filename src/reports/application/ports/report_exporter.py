from __future__ import annotations

from datetime import date
from typing import Protocol


class IReportExporter(Protocol):
    def export_sales_summary(
        self,
        *,
        tenant_name: str,
        from_date: date,
        to_date: date,
        data: dict,
    ) -> bytes:
        """Render a sales summary report as PDF bytes."""
        ...
