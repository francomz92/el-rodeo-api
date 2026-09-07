"""RESTful report endpoints for tenant-scoped analytics.

Three read-only endpoints under ``/reports`` — all require ``ADMIN`` role:

* ``GET /reports/inventory-summary`` — animals grouped by status and type
* ``GET /reports/sales-summary`` — revenue aggregated by week/month
* ``GET /reports/export/sales-summary`` — same data as downloadable PDF
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
    require_role,
)
from src.reports.infrastructure.adapters.http.input.report_schemas import (
    SalesSummaryQuery,
)
from src.reports.infrastructure.adapters.http.output.report_schemas import (
    InventorySummaryData,
    ReportWrapper,
    SalesSummaryData,
    TypeBreakdown,
)
from src.reports.infrastructure.presentation.dependencies.reports import (
    GetExportSalesSummaryCase,
    GetObtainInventorySummaryCase,
    GetObtainSalesSumaryCase,
)

CACHE_TTL = 300

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    dependencies=[
        is_authenticated_current_user,
        require_role(UserRole.ADMIN),
    ],
)


@router.get("/inventory-summary")
async def inventory_summary(
    current_user: GetCurrentUser,
    inventory_summary_case: GetObtainInventorySummaryCase,
    response: Response,
) -> ReportWrapper[InventorySummaryData]:
    """Return animal inventory grouped by status and type."""
    data = await inventory_summary_case.execute(current_user.tenant_id)

    response.headers["Cache-Control"] = f"private, max-age={CACHE_TTL}"

    return ReportWrapper(
        data=InventorySummaryData(
            total=data["total"],
            by_status=data["by_status"],
            by_type=[TypeBreakdown(**t) for t in data["by_type"]],
        ),
        period={"from": None, "to": None},
    )


@router.get("/sales-summary")
async def sales_summary(
    query: SalesSummaryQuery,
    current_user: GetCurrentUser,
    sales_summary_case: GetObtainSalesSumaryCase,
    response: Response,
) -> ReportWrapper[SalesSummaryData]:
    """Return sales aggregated by week and month within a date range."""
    data = await sales_summary_case.execute(current_user.tenant_id, query.from_date, query.to_date)

    response.headers["Cache-Control"] = f"private, max-age={CACHE_TTL}"

    return ReportWrapper(
        data=SalesSummaryData(
            weekly=data["weekly"],
            monthly=data["monthly"],
            total=data["total"],
        ),
        period={"from": query.from_date, "to": query.to_date},
    )


@router.get("/export/sales-summary")
async def export_sales_summary(
    query: SalesSummaryQuery,
    current_user: GetCurrentUser,
    use_case: GetExportSalesSummaryCase,
) -> StreamingResponse:
    """Return sales summary as a downloadable PDF."""
    pdf_bytes = await use_case.execute(current_user.tenant_id, query.from_date, query.to_date)
    filename = f"sales-report-{query.from_date.isoformat()}-{query.to_date.isoformat()}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
