"""Router for subscription plan change operations."""

import logging

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.infrastructure.adapters.http.input.payment_schemas import (
    PlanChangeSchema,
)
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    SubscriptionSchema,
)
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    GetChangePlanService,
)
from src.common.domain.exceptions import DomainError

logger = logging.getLogger(__name__)

subscription_router = APIRouter(
    tags=["Billing / Subscriptions"],
    dependencies=[is_authenticated_current_user],
)


@subscription_router.put(
    path="/subscriptions/plan",
    status_code=status.HTTP_200_OK,
    summary="Change subscription plan",
    description="Change the plan for the current tenant's subscription. "
    "Upgrades to paid plans return a MercadoPago checkout URL. "
    "Downgrades to free plans apply immediately.",
)
async def change_plan(
    data: PlanChangeSchema,
    current_user: GetCurrentUser,
    change_plan_service: GetChangePlanService,
):
    """Change the subscription plan for the authenticated user's tenant."""
    assert current_user.tenant_id is not None
    try:
        subscription, checkout_url = await change_plan_service.change_plan(
            tenant_id=current_user.tenant_id,
            new_plan_type=data.plan_type,
        )
    except PlanNotChangeableError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )
    except (DomainError, ValueError) as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    sub_schema = SubscriptionSchema(
        id=subscription.id,
        tenant_id=subscription.tenant_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
    )
    return {
        "subscription": sub_schema,
        "checkout_url": checkout_url,
    }
