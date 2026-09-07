"""Router for subscription operations — plan changes and MP subscription management."""

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.infrastructure.adapters.http.input.payment_schemas import (
    CreateSubscriptionSchema,
    PlanChangeSchema,
    UpdatePaymentMethodSchema,
)
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    SubscriptionSchema,
)
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    GetChangePlanService,
    GetMercadoPagoService,
    GetSubscriptionRepository,
)
from src.common.domain.exceptions import DomainError
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit


def _to_sub_schema(subscription) -> SubscriptionSchema:
    """Convert a Subscription entity to SubscriptionSchema."""
    return SubscriptionSchema(
        id=subscription.id,
        tenant_id=subscription.tenant_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        next_billing_date=subscription.next_billing_date,
        billing_date=subscription.billing_date,
        gateway_card_id=subscription.gateway_card_id,
        gateway_subscription_id=subscription.gateway_subscription_id,
    )


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
@rate_limit("5/minute")
async def change_plan(
    request: Request,
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
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )
    except (DomainError, ValueError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    sub_schema = _to_sub_schema(subscription)
    return {
        "subscription": sub_schema,
        "checkout_url": checkout_url,
    }


# ── Phase 0b: Subscription management endpoints ───────────────────────────


@subscription_router.post(
    path="/subscriptions",
    status_code=status.HTTP_201_CREATED,
    summary="Create recurring subscription",
    description="Create a MercadoPago subscription with auto-recurring billing. Requires a card_token_id from MercadoPago.js CardForm.",
)
@rate_limit("5/minute")
async def create_subscription(
    request: Request,
    data: CreateSubscriptionSchema,
    current_user: GetCurrentUser,
    mp_service: GetMercadoPagoService,
):
    """Create an MP subscription for the authenticated user's tenant."""
    assert current_user.tenant_id is not None

    try:
        subscription = await mp_service.create_subscription(
            tenant_id=current_user.tenant_id,
            plan_type=data.plan_type,
            card_token_id=data.card_token_id,
            payer_email=current_user.email,
        )
    except PlanNotChangeableError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )
    except ValueError as exc:
        error_msg = str(exc)
        if "already has an active subscription" in error_msg:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": error_msg},
            )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": error_msg},
        )
    except (DomainError,) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    return _to_sub_schema(subscription)


@subscription_router.get(
    path="/subscriptions",
    status_code=status.HTTP_200_OK,
    summary="List subscriptions",
    description="List subscriptions for the current tenant with optional status filter.",
)
async def list_subscriptions(
    current_user: GetCurrentUser,
    sub_repo: GetSubscriptionRepository,
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
):
    """List subscriptions for the authenticated user's tenant."""
    assert current_user.tenant_id is not None

    subs = await sub_repo.list_by_tenant(
        current_user.tenant_id,
        status_filter=status_filter,
    )
    return [_to_sub_schema(sub) for sub in subs]


@subscription_router.get(
    path="/subscriptions/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get subscription by ID",
    description="Return a single subscription by ID with tenant isolation.",
)
async def get_subscription(
    id: str,
    current_user: GetCurrentUser,
    sub_repo: GetSubscriptionRepository,
):
    """Get a subscription by UUID with tenant isolation."""
    assert current_user.tenant_id is not None

    from uuid import UUID

    try:
        sub_id = UUID(id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Subscription not found"},
        )

    sub = await sub_repo.get_by_id(sub_id)
    if sub is None or sub.tenant_id != current_user.tenant_id:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Subscription not found"},
        )

    return _to_sub_schema(sub)


@subscription_router.post(
    path="/subscriptions/{id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel subscription",
    description="Cancel a subscription. Idempotent — cancelling an already cancelled sub returns 200.",
)
@rate_limit("5/minute")
async def cancel_subscription(
    request: Request,
    id: str,
    current_user: GetCurrentUser,
    mp_service: GetMercadoPagoService,
):
    """Cancel a subscription by UUID."""
    assert current_user.tenant_id is not None

    from uuid import UUID

    try:
        sub_id = UUID(id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Subscription not found"},
        )

    try:
        subscription = await mp_service.cancel_subscription(
            subscription_id=sub_id,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    return _to_sub_schema(subscription)


@subscription_router.post(
    path="/subscriptions/{id}/payment-method",
    status_code=status.HTTP_200_OK,
    summary="Update payment method",
    description="Update the card on file for a subscription.",
)
@rate_limit("5/minute")
async def update_payment_method(
    request: Request,
    id: str,
    data: UpdatePaymentMethodSchema,
    current_user: GetCurrentUser,
    mp_service: GetMercadoPagoService,
):
    """Update payment method for a subscription by UUID."""
    assert current_user.tenant_id is not None

    from uuid import UUID

    try:
        sub_id = UUID(id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Subscription not found"},
        )

    try:
        subscription = await mp_service.update_payment_method(
            subscription_id=sub_id,
            tenant_id=current_user.tenant_id,
            card_token_id=data.card_token_id,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    return _to_sub_schema(subscription)
