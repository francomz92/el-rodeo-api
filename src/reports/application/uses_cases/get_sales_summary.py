from datetime import date
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.market.domain.repositories.sales_summary_report_query_port import (
    ISalesSummaryReportQuery,
)
from src.reports.application.services.reports_service import ReportsService


class GetSalesSummaryUseCase:
    def __init__(self, uow: IUoW, service: ReportsService):
        self.uow = uow
        self.service = service

    async def execute(self, tenant_id: UUID | None, from_date: date, to_date: date):
        if not tenant_id:
            raise NotFoundError("No se encontraron resultados")

        async with self.uow as uow:
            repository = uow.get_repository(ISalesSummaryReportQuery)
            return await self.service.get_sales_summary(tenant_id, from_date, to_date, repository)
