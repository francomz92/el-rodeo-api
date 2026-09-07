"""Repository port for report aggregation queries.

Defines the contract for report data access. Implementations use SQLAlchemy
Core for efficient GROUP BY aggregations (no ORM overhead).
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import date
from uuid import UUID

from src.common.domain.repository import IRepository


class IReportsRepository(IRepository):
    """Interface for read-only report data access.

    Both methods accept an explicit ``tenant_id`` because reports aggregate
    across multiple tables — the standard ``_filter_tenant`` (tied to a single
    ``_model``) is not sufficient.
    """

    @abstractmethod
    async def get_inventory_summary(self, *, tenant_id: UUID) -> dict:
        """Return animal counts grouped by status and by type.

        Returns a dict with keys:
            total (int): grand total of all animals
            by_status (dict[str, int]): count per status value
            by_type (list[dict]): [{type, by_status: {status: count}}, ...]
        """
        ...

    @abstractmethod
    async def get_sales_summary(
        self,
        *,
        tenant_id: UUID,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Return sales aggregated by week and month within a date range.

        Returns a dict with keys:
            weekly (list[dict]): [{week_start, revenue, sales_count, avg_price_per_kg, total_weight}, ...]
            monthly (list[dict]): [{month_start, revenue, sales_count, avg_price_per_kg, total_weight}, ...]
            total (dict): {revenue, sales_count, avg_price_per_kg, total_weight}
        """
        ...
