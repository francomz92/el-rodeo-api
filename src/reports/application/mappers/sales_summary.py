"""Builders that translate report data dicts into declarative ReportSpecs."""

from __future__ import annotations

from datetime import date

from src.reports.application.dto.report_spec import (
    ReportSpec,
    TableSection,
    TotalsSection,
)


def _currency(value: float) -> str:
    return f"${value:,.2f}"


def _count(value: int) -> str:
    return str(value)


def _weight(value: float) -> str:
    return f"{value:,.1f} kg"


def build_sales_summary_spec(
    tenant_name: str,
    from_date: date,
    to_date: date,
    data: dict,
) -> ReportSpec:
    """Build the sales summary report layout from a ReportsService data dict.

    Args:
        tenant_name: Display name for the report header.
        from_date: Start of the report date range.
        to_date: End of the report date range.
        data: Sales summary dict — same shape as returned by
            ``ReportsService.get_sales_summary()`` (keys ``weekly``,
            ``monthly``, ``total``).

    Returns:
        A ``ReportSpec`` ready for any ``IReportExporter`` implementation.
    """
    weekly_rows = [
        [
            r["week_start"],
            _currency(r["revenue"]),
            _count(r["sales_count"]),
            _currency(r["avg_price_per_kg"]),
            _weight(r["total_weight"]),
        ]
        for r in data.get("weekly", [])
    ]

    monthly_rows = [
        [
            r["month_start"],
            _currency(r["revenue"]),
            _count(r["sales_count"]),
            _currency(r["avg_price_per_kg"]),
            _weight(r["total_weight"]),
        ]
        for r in data.get("monthly", [])
    ]

    total = data.get("total", {})
    totals_rows = [
        ["Ingresos Totales", _currency(total.get("revenue", 0))],
        ["Cantidad de Ventas", _count(total.get("sales_count", 0))],
        ["Precio Promedio por Kg", _currency(total.get("avg_price_per_kg", 0))],
        ["Peso Total", _weight(total.get("total_weight", 0))],
    ]

    return ReportSpec(
        title=f"Reporte de Ventas — {tenant_name}",
        period_text=f"Período: {from_date.isoformat()} — {to_date.isoformat()}",
        sections=[
            TableSection(
                title="Resumen Semanal",
                headers=["Semana", "Ingresos", "Ventas", "Precio Prom./Kg", "Peso Total"],
                rows=weekly_rows,
                empty_message="No hay datos semanales para el período seleccionado.",
            ),
            TableSection(
                title="Resumen Mensual",
                headers=["Mes", "Ingresos", "Ventas", "Precio Prom./Kg", "Peso Total"],
                rows=monthly_rows,
                empty_message="No hay datos mensuales para el período seleccionado.",
            ),
            TotalsSection(title="Totales", rows=totals_rows),
        ],
    )
