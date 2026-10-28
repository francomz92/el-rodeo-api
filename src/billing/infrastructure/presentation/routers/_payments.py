"""Payment router — paginated payment history."""

from fastapi import APIRouter, Query, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    PaginatedPaymentListSchema,
)
from src.billing.infrastructure.presentation.dependencies.payment_dependencies import (
    GetListPaymentsCase,
)

payment_router = APIRouter(
    prefix="/billing/payments",
    tags=["Billing / Payments"],
    responses={401: {}, 403: {}},
    dependencies=[is_authenticated_current_user],
)


@payment_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List payment history",
    description="Return a paginated list of payments for the authenticated user's tenant.",
    response_model=PaginatedPaymentListSchema,
)
async def list_payments(
    current_user: GetCurrentUser,
    list_payments_case: GetListPaymentsCase,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> dict:
    """Return paginated payments for the current tenant."""
    assert current_user.tenant_id is not None
    payments, total = await list_payments_case.execute(
        tenant_id=current_user.tenant_id,
        page=page,
        per_page=per_page,
    )
    return {
        "payments": payments,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
