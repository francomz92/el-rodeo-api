from datetime import date
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.reports.application.services.reports_service import ReportsService
from src.reports.domain.repositories.reports_repository_port import IReportsRepository
from src.reports.infrastructure.export.pdf_renderer import generate_sales_report


class ExportSalesSummaryUseCase:
    def __init__(self, uow: IUoW, service: ReportsService):
        self.uow = uow
        self.service = service

    async def execute(self, tenant_id: UUID | None, from_date: date, to_date: date):
        if not tenant_id:
            raise NotFoundError("No se encontraron resultados")

        async with self.uow as uow:
            repository = uow.get_repository(IReportsRepository)
            data = await self.service.get_sales_summary(
                tenant_id,
                from_date,
                to_date,
                repository,
            )

            generate_sales_report(
                tenant_name=tenant_id.hex[:8],
                from_date=from_date,
                to_date=to_date,
                data=data,
            )
