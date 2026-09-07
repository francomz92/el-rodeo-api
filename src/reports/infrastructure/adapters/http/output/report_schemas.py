"""Pydantic response schemas for report endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ReportWrapper(BaseModel, Generic[T]):
    """Generic wrapper for all report responses.

    Provides consistent envelope with data, generation timestamp, and period.
    """

    data: T
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period: dict[str, Any] = {}


class StatusCount(BaseModel):
    """Animal count for a single status value."""

    status: str
    count: int


class TypeBreakdown(BaseModel):
    """Animal counts by type, with per-status breakdown."""

    type: str
    by_status: dict[str, int]


class InventorySummaryData(BaseModel):
    """Inventory summary response body."""

    total: int = 0
    by_status: dict[str, int] = {}
    by_type: list[TypeBreakdown] = []


class PeriodSummary(BaseModel):
    """Aggregated sales data for a single period (week or month)."""

    week_start: str | None = None
    month_start: str | None = None
    revenue: float = 0.0
    sales_count: int = 0
    avg_price_per_kg: float = 0.0
    total_weight: float = 0.0


class SalesTotals(BaseModel):
    """Totals row for sales summary."""

    revenue: float = 0.0
    sales_count: int = 0
    avg_price_per_kg: float = 0.0
    total_weight: float = 0.0


class SalesSummaryData(BaseModel):
    """Sales summary response body."""

    weekly: list[PeriodSummary] = []
    monthly: list[PeriodSummary] = []
    total: SalesTotals = SalesTotals()
