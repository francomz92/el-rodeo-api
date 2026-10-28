"""Subscription routers — plan changes and MercadoPago subscription management."""

from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    is_authenticated_current_user,
)
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.infrastructure.adapters.http.input.payment_schemas import (
    CreateSubscriptionSchema,
    PlanChangeSchema,
    UpdatePaymentMethodSchema,
)
from src.billing.infrastructure.adapters.http.output.payment_schemas import (
    PlanChangeResponseSchema,
    SubscriptionSchema,
)
from src.billing.infrastructure.presentation.dependencies.subscription_dependencies import (
    GetCancelSubscriptionCase,
    GetChangePlanCase,
    GetCreateSubscriptionCase,
    GetListSubscriptionsCase,
    GetSubscriptionDetailCase,
    GetUpdatePaymentMethodCase,
)
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

subscription_router = APIRouter(
    prefix="/billing/subscriptions",
    tags=["Billing / Subscriptions"],
    responses={401: {}, 403: {}},
    dependencies=[is_authenticated_current_user],
)


@subscription_router.put(
    path="/plan",
    status_code=status.HTTP_200_OK,
    summary="Change subscription plan",
    description="Change the plan for the current tenant's subscription. "
    "Upgrades to paid plans return a MercadoPago checkout URL. "
    "Downgrades to the FREE plan are rejected (FREE is only the post-trial/post-cancellation state).",
    response_model=PlanChangeResponseSchema,
)
@rate_limit("5/minute")
async def change_plan(
    request: Request,
    data: PlanChangeSchema,
    current_user: GetCurrentUser,
    change_plan_case: GetChangePlanCase,
):
    """Change the subscription plan for the authenticated user's tenant."""
    assert current_user.tenant_id is not None
    subscription, checkout_url = await change_plan_case.execute(
        tenant_id=current_user.tenant_id,
        new_plan_type=data.plan_type,
    )
    return {
        "subscription": subscription,
        "checkout_url": checkout_url,
    }


# ── Subscription management endpoints ────────────────────────────────────


@subscription_router.post(
    path="",
    status_code=status.HTTP_200_OK,
    summary="Activate recurring subscription",
    description="Activate the tenant's existing subscription for MercadoPago auto-recurring billing. Requires a card_token_id from MercadoPago.js CardForm. The subscription row must already exist (trial or previous plan).",
    response_model=SubscriptionSchema,
)
@rate_limit("5/minute")
async def create_subscription(
    request: Request,
    data: CreateSubscriptionSchema,
    current_user: GetCurrentUser,
    create_subscription_case: GetCreateSubscriptionCase,
):
    """Activate the tenant's subscription with MP recurring billing."""
    assert current_user.tenant_id is not None
    return await create_subscription_case.execute(
        tenant_id=current_user.tenant_id,
        plan_type=data.plan_type,
        card_token_id=data.card_token_id,
        payer_email=current_user.email,
    )


@subscription_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List subscriptions",
    description="List subscriptions for the current tenant with optional status filter.",
    response_model=list[SubscriptionSchema],
)
async def list_subscriptions(
    current_user: GetCurrentUser,
    list_subscriptions_case: GetListSubscriptionsCase,
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
):
    """List subscriptions for the authenticated user's tenant."""
    assert current_user.tenant_id is not None
    return await list_subscriptions_case.execute(
        tenant_id=current_user.tenant_id,
        status_filter=status_filter,
    )


@subscription_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get subscription by ID",
    description="Return a single subscription by ID with tenant isolation.",
    response_model=SubscriptionSchema,
)
async def get_subscription(
    id: UUID,
    current_user: GetCurrentUser,
    get_subscription_case: GetSubscriptionDetailCase,
):
    """Get a subscription by UUID with tenant isolation."""
    assert current_user.tenant_id is not None
    return await get_subscription_case.execute(
        subscription_id=id,
        tenant_id=current_user.tenant_id,
    )


@subscription_router.post(
    path="/{id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel subscription",
    description="Cancel a subscription. Idempotent — cancelling an already cancelled sub returns 200.",
    response_model=SubscriptionSchema,
)
@rate_limit("5/minute")
async def cancel_subscription(
    request: Request,
    id: UUID,
    current_user: GetCurrentUser,
    cancel_subscription_case: GetCancelSubscriptionCase,
):
    """Cancel a subscription by UUID."""
    assert current_user.tenant_id is not None
    return await cancel_subscription_case.execute(
        subscription_id=id,
        tenant_id=current_user.tenant_id,
    )


@subscription_router.post(
    path="/{id}/payment-method",
    status_code=status.HTTP_200_OK,
    summary="Update payment method",
    description="Update the card on file for a subscription.",
    response_model=SubscriptionSchema,
)
@rate_limit("5/minute")
async def update_payment_method(
    request: Request,
    id: UUID,
    data: UpdatePaymentMethodSchema,
    current_user: GetCurrentUser,
    update_payment_method_case: GetUpdatePaymentMethodCase,
):
    """Update payment method for a subscription by UUID."""
    assert current_user.tenant_id is not None
    return await update_payment_method_case.execute(
        subscription_id=id,
        tenant_id=current_user.tenant_id,
        card_token_id=data.card_token_id,
    )
