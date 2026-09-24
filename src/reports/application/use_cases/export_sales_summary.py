from datetime import date
from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError
from src.reports.application.ports.report_exporter import IReportExporter
from src.reports.application.services.reports_service import ReportsService
from src.reports.domain.repositories.reports_repository_port import IReportsRepository


class ExportSalesSummaryUseCase:
    def __init__(self, uow: IUoW, service: ReportsService, exporter: IReportExporter):
        self.uow = uow
        self.service = service
        self.exporter = exporter

    async def execute(self, tenant_id: UUID | None, from_date: date, to_date: date) -> bytes:
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

            return self.exporter.export_sales_summary(
                tenant_name=tenant_id.hex[:8],
                from_date=from_date,
                to_date=to_date,
                data=data,
            )
