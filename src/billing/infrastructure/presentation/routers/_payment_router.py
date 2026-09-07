"""Router for payment history operations."""

from fastapi import APIRouter, Query, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.domain.entities._payment import Payment
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    PaymentSchema,
)
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    GetPaymentHistoryService,
)

payment_router = APIRouter(
    tags=["Billing / Payments"],
    dependencies=[is_authenticated_current_user],
)


@payment_router.get(
    path="/payments",
    status_code=status.HTTP_200_OK,
    summary="List payment history",
    description="Return a paginated list of payments for the authenticated user's tenant.",
)
async def list_payments(
    current_user: GetCurrentUser,
    payment_history_service: GetPaymentHistoryService,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
):
    """Return paginated payments for the current tenant."""
    assert current_user.tenant_id is not None
    payments, total = await payment_history_service.list_payments(
        tenant_id=current_user.tenant_id,
        page=page,
        per_page=per_page,
    )

    payment_schemas = [_payment_to_schema(p) for p in payments]
    return {
        "payments": payment_schemas,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def _payment_to_schema(payment: Payment) -> PaymentSchema:
    """Convert a Payment domain entity to a PaymentSchema."""
    pm_str: str | None = None
    if payment.payment_method:
        parts = []
        if payment.payment_method.card_brand:
            parts.append(payment.payment_method.card_brand)
        if payment.payment_method.payment_type_id:
            parts.append(payment.payment_method.payment_type_id)
        if parts:
            pm_str = "|".join(parts)

    return PaymentSchema(
        id=payment.id,
        status=payment.status.value,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        payment_method=pm_str,
        paid_at=payment.paid_at,
        created_at=payment.created_at,
    )
