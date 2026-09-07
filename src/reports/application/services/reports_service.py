"""Application service for report generation with cache-aside caching.

Uses ``IReportsRepository`` for data access and ``ICacheService`` for
read-through caching.  No Unit of Work is needed — reports are read-only.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.common.domain.ports.cache_service import ICacheService
from src.reports.domain.repositories.reports_repository_port import (
    IReportsRepository,
)


class ReportsService:
    """Orchestrates report generation with cache-aside pattern.

    Queries are delegated to ``IReportsRepository`` for SQLAlchemy Core
    aggregation.  Results are cached via ``ICacheService`` with a 5-minute TTL.
    Cache keys follow the pattern ``reports:{tenant_id}:{report_name}[:args]``.
    """

    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "reports"

    def __init__(self, cache: ICacheService) -> None:
        self._cache = cache

    def _cache_key(self, tenant_id: UUID, report: str, *args: str) -> str:
        parts = [self.CACHE_PREFIX, str(tenant_id), report, *args]
        return ":".join(parts)

    async def get_inventory_summary(self, tenant_id: UUID, repository: IReportsRepository) -> dict:
        """Return cached or fresh inventory summary."""
        key = self._cache_key(tenant_id, "inventory")
        return await self._cache.get_or_set(
            key=key,
            ttl=self.CACHE_TTL,
            factory=lambda: repository.get_inventory_summary(tenant_id=tenant_id),
        )

    async def get_sales_summary(
        self,
        tenant_id: UUID,
        from_date: date,
        to_date: date,
        repository: IReportsRepository,
    ) -> dict:
        """Return cached or fresh sales summary for a date range."""
        key = self._cache_key(
            tenant_id,
            "sales",
            from_date.isoformat(),
            to_date.isoformat(),
        )
        return await self._cache.get_or_set(
            key=key,
            ttl=self.CACHE_TTL,
            factory=lambda: repository.get_sales_summary(
                tenant_id=tenant_id,
                from_date=from_date,
                to_date=to_date,
            ),
        )
