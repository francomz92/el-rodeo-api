"""FastAPI dependency injection for the reports module.

Wires the cache-backed ``ReportsService`` to report use cases. Each use case
resolves its owning context's query port through the Unit of Work. Export
use cases receive an ``IReportExporter`` resolved from the ``format`` query
parameter through a registry, so new formats plug in without touching
routers or use cases.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query

from src.common.infrastructure.presentation.dependencies.cache import GetCacheService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.reports.application.ports.report_exporter import IReportExporter
from src.reports.application.uses_cases.export_sales_summary import ExportSalesSummaryUseCase
from src.reports.application.uses_cases.get_inventory_summary import GetInventorySummaryUseCase
from src.reports.application.uses_cases.get_sales_summary import GetSalesSummaryUseCase
from src.reports.infrastructure.adapters.export.pdf_exporter import PdfExporter
from src.reports.infrastructure.adapters.export.xlsx_exporter import XlsxExporter
from src.reports.infrastructure.adapters.http.input.report_schemas import (
    ReportExportFormat,
)

# isort: off
from src.reports.application.services.reports_service import ReportsService
# isort: on

_FORMAT_EXPORTERS: dict[ReportExportFormat, type[IReportExporter]] = {  # type: ignore[assignment]
    ReportExportFormat.PDF: PdfExporter,
    ReportExportFormat.XLSX: XlsxExporter,
}


def _get_reports_service(cache: GetCacheService) -> ReportsService:
    return ReportsService(cache=cache)


def _get_exporter(
    format_query: Annotated[ReportExportFormat, Query(alias="format")] = ReportExportFormat.PDF,
) -> IReportExporter:
    """Resolve the report exporter matching the requested ``format`` query param."""
    return _FORMAT_EXPORTERS[format_query]()


def _get_inventory_summary_case(uow: GetUnitOfWork, service: GetReportsService) -> GetInventorySummaryUseCase:
    return GetInventorySummaryUseCase(uow, service)


def _get_sales_summary_case(uow: GetUnitOfWork, service: GetReportsService) -> GetSalesSummaryUseCase:
    return GetSalesSummaryUseCase(uow, service)


def _get_export_sales_summary_case(
    uow: GetUnitOfWork,
    service: GetReportsService,
    exporter: GetReportExporter,
) -> ExportSalesSummaryUseCase:
    return ExportSalesSummaryUseCase(uow, service, exporter)


GetReportsService = Annotated[ReportsService, Depends(_get_reports_service)]
GetReportExporter = Annotated[IReportExporter, Depends(_get_exporter)]
GetObtainInventorySummaryCase = Annotated[GetInventorySummaryUseCase, Depends(_get_inventory_summary_case)]
GetObtainSalesSumaryCase = Annotated[GetSalesSummaryUseCase, Depends(_get_sales_summary_case)]
GetExportSalesSummaryCase = Annotated[ExportSalesSummaryUseCase, Depends(_get_export_sales_summary_case)]
