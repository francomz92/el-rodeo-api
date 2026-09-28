from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.common.domain.repository import IRepository


class ISalesSummaryReportQuery(IRepository):
    @abstractmethod
    async def get_sales_summary(
        self,
        *,
        tenant_id: UUID,
        from_date: date,
        to_date: date,
    ) -> dict: ...
