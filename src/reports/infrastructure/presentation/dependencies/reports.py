"""FastAPI dependency injection for the reports module.

Wires up ``IReportsRepository`` and ``ReportsService`` for request-scoped
DI.  The service also receives ``ICacheService`` for cache-aside caching.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.cache import GetCacheService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.reports.application.use_cases.export_sales_summary import ExportSalesSummaryUseCase
from src.reports.application.use_cases.get_inventory_summary import GetInventorySummaryUseCase
from src.reports.application.use_cases.get_sales_summary import GetSalesSummaryUseCase

# isort: off
from src.reports.application.services.reports_service import ReportsService
# isort: on


def _get_reports_service(cache: GetCacheService) -> ReportsService:
    return ReportsService(cache=cache)


def _get_inventory_summary_case(uow: GetUnitOfWork, service: GetReportsService) -> GetInventorySummaryUseCase:
    return GetInventorySummaryUseCase(uow, service)


def _get_sales_summary_case(uow: GetUnitOfWork, service: GetReportsService) -> GetSalesSummaryUseCase:
    return GetSalesSummaryUseCase(uow, service)


def _get_export_sales_summary_case(uow: GetUnitOfWork, service: GetReportsService) -> ExportSalesSummaryUseCase:
    return ExportSalesSummaryUseCase(uow, service)


GetReportsService = Annotated[ReportsService, Depends(_get_reports_service)]
GetObtainInventorySummaryCase = Annotated[GetInventorySummaryUseCase, Depends(_get_inventory_summary_case)]
GetObtainSalesSumaryCase = Annotated[GetSalesSummaryUseCase, Depends(_get_sales_summary_case)]
GetExportSalesSummaryCase = Annotated[ExportSalesSummaryUseCase, Depends(_get_export_sales_summary_case)]
