"""SQLAlchemy Core aggregation queries for report data.

Implements ``IReportsRepository`` using SQLAlchemy Core for efficient
GROUP BY aggregations.  All queries accept an explicit ``tenant_id``
parameter — reports aggregate across multiple tables so the single-model
``_filter_tenant`` from ``TenantAwareRepository`` is not used here.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.market.infrastructure.persistence.models._sales import Sale
from src.reports.domain.repositories.reports_repository_port import (
    IReportsRepository,
)


class ReportsRepository(IReportsRepository):
    """Read-only repository for report aggregation queries.

    Uses SQLAlchemy Core (not ORM) for efficient GROUP BY aggregations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_sales_summary(
        self,
        *,
        tenant_id: UUID,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Return sales aggregated by week and by month within a date range."""
        # ── Weekly aggregation ────────────────────────────────────────
        week_stmt = (
            select(
                func.date_trunc("week", Sale.sale_date).label("week_start"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(func.sum(Sale.price), 0).label("revenue"),
                func.coalesce(func.avg(Sale.price_per_kg), 0).label("avg_price_per_kg"),
                func.coalesce(func.sum(Sale.weight), 0).label("total_weight"),
            )
            .where(
                Sale.tenant_id == tenant_id,
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date,
            )
            .group_by("week_start")
            .order_by("week_start")
        )
        week_rows = await self.db.execute(week_stmt)
        weekly = [
            {
                "week_start": (row.week_start.isoformat() if hasattr(row.week_start, "isoformat") else str(row.week_start)),
                "revenue": float(row.revenue),
                "sales_count": row.sales_count,
                "avg_price_per_kg": round(float(row.avg_price_per_kg), 2),
                "total_weight": float(row.total_weight),
            }
            for row in week_rows
        ]

        # ── Monthly aggregation ────────────────────────────────────────
        month_stmt = (
            select(
                func.date_trunc("month", Sale.sale_date).label("month_start"),
                func.count(Sale.id).label("sales_count"),
                func.coalesce(func.sum(Sale.price), 0).label("revenue"),
                func.coalesce(func.avg(Sale.price_per_kg), 0).label("avg_price_per_kg"),
                func.coalesce(func.sum(Sale.weight), 0).label("total_weight"),
            )
            .where(
                Sale.tenant_id == tenant_id,
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date,
            )
            .group_by("month_start")
            .order_by("month_start")
        )
        month_rows = await self.db.execute(month_stmt)
        monthly = [
            {
                "month_start": (row.month_start.isoformat() if hasattr(row.month_start, "isoformat") else str(row.month_start)),
                "revenue": float(row.revenue),
                "sales_count": row.sales_count,
                "avg_price_per_kg": round(float(row.avg_price_per_kg), 2),
                "total_weight": float(row.total_weight),
            }
            for row in month_rows
        ]

        # ── Totals ────────────────────────────────────────────────────
        total_stmt = select(
            func.coalesce(func.sum(Sale.price), 0).label("revenue"),
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.avg(Sale.price_per_kg), 0).label("avg_price_per_kg"),
            func.coalesce(func.sum(Sale.weight), 0).label("total_weight"),
        ).where(
            Sale.tenant_id == tenant_id,
            Sale.sale_date >= from_date,
            Sale.sale_date <= to_date,
        )
        total_row = (await self.db.execute(total_stmt)).one()

        return {
            "weekly": weekly,
            "monthly": monthly,
            "total": {
                "revenue": float(total_row.revenue),
                "sales_count": total_row.sales_count,
                "avg_price_per_kg": round(float(total_row.avg_price_per_kg), 2),
                "total_weight": float(total_row.total_weight),
            },
        }
