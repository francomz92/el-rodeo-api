"""Payment router — cursor-paginated payment history."""

from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    PaymentSchema,
)
from src.billing.infrastructure.presentation.dependencies.payment_dependencies import (
    GetListPaymentsCase,
)
from src.common.application.pagination.cursor import encode_cursor
from src.common.infrastructure.adapters.http.input.query_params import (
    StandardQueryParams,
)
from src.common.infrastructure.adapters.http.output.cursor_page import CursorPage

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
    description="Return a cursor-paginated list of payments for the authenticated user's tenant.",
    response_model=CursorPage[PaymentSchema],
)
async def list_payments(
    current_user: GetCurrentUser,
    list_payments_case: GetListPaymentsCase,
    filters: Annotated[StandardQueryParams, Query()],
):
    """Return a cursor-paginated payments page for the current tenant."""
    assert current_user.tenant_id is not None
    items, total, has_next = await list_payments_case.execute(
        tenant_id=current_user.tenant_id,
        limit=filters.limit,
        offset=filters.offset,
        order_by=filters.order_by,
        cursor=filters.cursor,
    )

    # Emit next_cursor whenever there is a next page, regardless of the
    # incoming cursor: the first page must carry the continuation too.
    next_cursor: str | None = None
    if has_next and items:
        next_cursor = encode_cursor(str(items[-1].id))

    # Return cursor-paginated response (bypasses response_model validation)
    validated = [PaymentSchema.model_validate(p) for p in items]
    page = CursorPage[PaymentSchema](
        items=validated,
        cursor=encode_cursor(str(validated[0].id)) if validated else None,
        next_cursor=next_cursor,
        total=total,
    )
    return JSONResponse(
        content=page.model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
