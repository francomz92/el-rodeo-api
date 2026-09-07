"""MercadoPagoService — orchestrates MercadoPago Checkout Pro preferences.

Provides:
- create_checkout_preference: validates price > 0, creates MP preference, saves payment record
- create_subscription: creates MP subscription with auto-recurring
- cancel_subscription: cancels MP subscription
- update_payment_method: updates card token on MP subscription
- get_payment_status: proxies to gateway
- refund_payment: proxies to gateway
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import (
    AutoRecurringData,
    BackUrlsData,
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
    ItemData,
    PaymentResult,
    SubscriptionResult,
)
from src.common.infrastructure.core._config import settings


class MercadoPagoService:
    """Application service that orchestrates MercadoPago Checkout Pro interactions.

    Wraps the IPaymentGateway port with business logic (price validation,
    payment record creation) and exposes convenience methods for status
    lookup and refunds.
    """

    def __init__(
        self,
        gateway: IPaymentGateway,
        payment_repo: IPaymentRepository,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
    ) -> None:
        self._gateway = gateway
        self._payment_repo = payment_repo
        self._subscription_repo = subscription_repo
        self._plan_repo = plan_repo

    async def create_checkout_preference(
        self,
        tenant_id: UUID,
        plan_type: PlanTypeEntity,
    ) -> str:
        """Create an MP Checkout Pro preference for the given tenant and plan.

        Loads the plan, validates it is a paid plan (price > 0), builds the
        preference payload, delegates to the gateway, persists a PENDING
        Payment record, and returns the checkout ``init_point`` URL.

        Args:
            tenant_id: The tenant requesting the checkout.
            plan_type: The target plan type.

        Returns:
            The MercadoPago Checkout Pro ``init_point`` URL.

        Raises:
            PlanNotChangeableError: If the plan is FREE or has no price.
            ValueError: If no subscription exists for the tenant.
        """
        # Load plan from the injected PlanRepository (in-memory seed data)
        plan = await self._plan_repo.get_by_plan_type(plan_type)
        if plan is None:
            raise PlanNotChangeableError(f"Plan not found: {plan_type.value}")

        # GUARD: FREE plan / zero-price plans cannot be purchased
        if plan.price_monthly is None or plan.price_monthly.amount <= Decimal("0"):
            raise PlanNotChangeableError("FREE plan cannot be purchased")

        # Load subscription to obtain the subscription_id for the Payment record
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        # Build the checkout preference payload
        item = ItemData(
            title=f"Plan {plan.name} - El Rodeo",
            quantity=1,
            unit_price=plan.price_monthly.amount,
            currency_id="ARS",
        )

        external_reference = f"{tenant_id}:{plan_type.value}"

        back_urls = BackUrlsData(
            success=settings.MP_WEBHOOK_URL,
            failure=settings.MP_WEBHOOK_URL,
            pending=settings.MP_WEBHOOK_URL,
        )

        result = await self._gateway.create_preference(
            items=[item],
            back_urls=back_urls,
            notification_url=settings.MP_WEBHOOK_URL,
            external_reference=external_reference,
        )

        # Persist a PENDING payment record
        payment = Payment(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            status=PaymentStatus.PENDING,
            amount=plan.price_monthly.amount,
            mp_preference_id=result.id,
            description=f"Plan {plan.name} - El Rodeo",
        )
        await self._payment_repo.create(payment)

        return result.init_point

    async def get_payment_status(self, mp_payment_id: str) -> PaymentResult:
        """Retrieve the current status of a MercadoPago payment.

        Delegates directly to the gateway.
        """
        return await self._gateway.get_payment(mp_payment_id)

    async def refund_payment(
        self,
        mp_payment_id: str,
        amount: Decimal | None = None,
    ) -> bool:
        """Refund a MercadoPago payment, fully or partially.

        Delegates directly to the gateway.
        """
        return await self._gateway.refund(mp_payment_id, amount)

    # ── Subscription methods (Phase 0b) ────────────────────────────────────

    async def create_subscription(
        self,
        tenant_id: UUID,
        plan_type: PlanTypeEntity,
        card_token_id: str,
        payer_email: str,
    ) -> Subscription:
        """Create an MP subscription with auto-recurring billing.

        Validates the plan is paid, checks no active MP-managed subscription
        exists, calls the gateway to create the subscription, and updates
        the local subscription record.

        Args:
            tenant_id: The tenant requesting the subscription.
            plan_type: The target plan type.
            card_token_id: Card token from MercadoPago.js CardForm.
            payer_email: Email of the payer.

        Returns:
            The updated Subscription entity with gateway_subscription_id set.

        Raises:
            PlanNotChangeableError: If the plan is FREE or has no price.
            ValueError: If no subscription exists, or tenant already has an
                active MP-managed subscription.
        """
        # Load plan
        plan = await self._plan_repo.get_by_plan_type(plan_type)
        if plan is None:
            raise PlanNotChangeableError(f"Plan not found: {plan_type.value}")

        # GUARD: FREE plan / zero-price plans cannot have subscriptions
        if plan.price_monthly is None or plan.price_monthly.amount <= Decimal("0"):
            raise PlanNotChangeableError("Cannot create subscription for FREE plan")

        # Load subscription
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        # GUARD: tenant already has a gateway-managed subscription
        if subscription.gateway_subscription_id is not None:
            raise ValueError(f"Tenant {tenant_id} already has an active subscription ({subscription.gateway_subscription_id})")

        # Build auto_recurring config
        auto_recurring = AutoRecurringData(
            frequency=1,
            frequency_type="months",
            transaction_amount=float(plan.price_monthly.amount),
            currency_id="ARS",
        )

        external_reference = f"{tenant_id}:{plan_type.value}"
        back_url = settings.MP_WEBHOOK_URL

        # Call gateway
        result: SubscriptionResult = await self._gateway.create_subscription(
            reason=f"Plan {plan.name} - El Rodeo",
            auto_recurring=auto_recurring,
            payer_email=payer_email,
            card_token_id=card_token_id,
            external_reference=external_reference,
            back_url=back_url,
        )

        # Update local subscription with gateway data
        now = datetime.now(tz=timezone.utc)
        updated = replace(
            subscription,
            status=SubscriptionStatus.ACTIVE,
            gateway_subscription_id=result.id,
            gateway_card_id=result.card_id,
            next_billing_date=result.next_billing_date,
            billing_date=result.billing_date,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        return await self._subscription_repo.update(updated)

    async def cancel_subscription(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
    ) -> Subscription:
        """Cancel an MP subscription.

        Finds the subscription, validates it belongs to the tenant, and:
        - If already CANCELED: no-op (idempotent)
        - Otherwise: calls gateway.cancel_subscription() and updates local status

        Args:
            subscription_id: The local subscription UUID.
            tenant_id: The tenant requesting cancellation.

        Returns:
            The updated Subscription entity with status=CANCELED.

        Raises:
            ValueError: If subscription not found or belongs to another tenant.
        """
        subscription = await self._subscription_repo.get_by_id(subscription_id)
        if subscription is None or subscription.tenant_id != tenant_id:
            raise ValueError(f"Subscription not found: {subscription_id}")

        # Idempotent: already cancelled
        if subscription.status == SubscriptionStatus.CANCELED:
            return subscription

        # Cancel in gateway
        if subscription.gateway_subscription_id:
            await self._gateway.cancel_subscription(subscription.gateway_subscription_id)

        # Update local
        now = datetime.now(tz=timezone.utc)
        updated = replace(
            subscription,
            status=SubscriptionStatus.CANCELED,
            canceled_at=now,
        )
        return await self._subscription_repo.update(updated)

    async def update_payment_method(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
        card_token_id: str,
    ) -> Subscription:
        """Update the payment method (card) for an MP subscription.

        Args:
            subscription_id: The local subscription UUID.
            tenant_id: The tenant requesting the update.
            card_token_id: The new card token from MercadoPago.js CardForm.

        Returns:
            The updated Subscription entity with new gateway_card_id.

        Raises:
            ValueError: If subscription not found or belongs to another tenant.
        """
        subscription = await self._subscription_repo.get_by_id(subscription_id)
        if subscription is None or subscription.tenant_id != tenant_id:
            raise ValueError(f"Subscription not found: {subscription_id}")

        # Update in gateway
        if subscription.gateway_subscription_id:
            result = await self._gateway.update_subscription(
                subscription.gateway_subscription_id,
                {"card_token_id": card_token_id},
            )
            new_card_id = result.card_id
        else:
            new_card_id = None

        # Update local
        updated = replace(
            subscription,
            gateway_card_id=new_card_id,
        )
        return await self._subscription_repo.update(updated)
