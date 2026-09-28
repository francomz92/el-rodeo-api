from uuid import UUID

from src.cattle.domain.repositories.inventory_report_query_port import (
    IAnimalInventoryReportQuery,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.reports.application.services.reports_service import ReportsService


class GetInventorySummaryUseCase:
    def __init__(self, uow: IUoW, report_service: ReportsService):
        self.uow = uow
        self.report_service = report_service

    async def execute(self, tenant_id: UUID | None):
        if not tenant_id:
            raise NotFoundError("No se encontraron resultados")
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalInventoryReportQuery)
            return await self.report_service.get_inventory_summary(tenant_id, repository)
