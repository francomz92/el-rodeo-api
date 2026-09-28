"""Read-only animal inventory report query implementation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.repositories.inventory_report_query_port import (
    IAnimalInventoryReportQuery,
)
from src.cattle.infrastructure.persistence.models._animal_models import (
    Animal,
    AnimalType,
)


class AnimalInventoryReportQueryRepository(IAnimalInventoryReportQuery):
    """Read-only inventory aggregation with an explicit tenant boundary."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_inventory_summary(
        self,
        *,
        tenant_id: UUID,
    ) -> dict:
        """Return animal counts grouped by status and by type for a tenant."""
        # ── Total count ──────────────────────────────────────────────
        total_stmt = select(func.count(Animal.id)).where(
            Animal.tenant_id == tenant_id,
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0

        # ── By status — explicit zero for every known status ──────────
        status_stmt = (
            select(
                Animal.status,
                func.count(Animal.id).label("count"),
            )
            .where(Animal.tenant_id == tenant_id)
            .group_by(Animal.status)
        )
        status_rows = await self.db.execute(status_stmt)
        by_status: dict[str, int] = {s.value: 0 for s in AnimalStatus}
        for row in status_rows.all():
            skey = row.status.value if hasattr(row.status, "value") else str(row.status)
            by_status[skey] = row._mapping["count"]

        # ── By type + status ──────────────────────────────────────────
        type_stmt = (
            select(
                AnimalType.name.label("type_name"),
                Animal.status,
                func.count(Animal.id).label("count"),
            )
            .select_from(Animal)
            .join(AnimalType, Animal.type_id == AnimalType.id, isouter=True)
            .where(Animal.tenant_id == tenant_id)
            .group_by(AnimalType.name, Animal.status)
            .order_by(AnimalType.name)
        )
        type_rows = await self.db.execute(type_stmt)

        by_type_map: dict[str, dict[str, int]] = {}
        for row in type_rows.all():
            tname = row.type_name or "unknown"
            if tname not in by_type_map:
                by_type_map[tname] = {s.value: 0 for s in AnimalStatus}
            skey = row.status.value if hasattr(row.status, "value") else str(row.status)
            by_type_map[tname][skey] = row._mapping["count"]

        return {
            "total": total,
            "by_status": by_status,
            "by_type": [{"type": tname, "by_status": statuses} for tname, statuses in sorted(by_type_map.items())],
        }
