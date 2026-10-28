"""CreateSubscriptionCase — creates an MP subscription with auto-recurring billing."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import (
    AutoRecurringData,
    IPaymentGateway,
    IPlanRepository,
    ISubscriptionRepository,
    SubscriptionResult,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import DuplicatedError, NotFoundError


class CreateSubscriptionCase:
    """Use case that creates an MP subscription with auto-recurring billing.

    Validates the plan is paid, checks no active MP-managed subscription
    exists, calls the gateway to create the subscription, and updates
    the local subscription record.
    """

    def __init__(
        self,
        uow: IUoW,
        gateway: IPaymentGateway,
        webhook_url: str,
    ) -> None:
        self.uow = uow
        self.gateway = gateway
        self.webhook_url = webhook_url

    async def execute(
        self,
        tenant_id: UUID,
        plan_type: PlanTypeEntity,
        card_token_id: str,
        payer_email: str,
    ) -> SubscriptionEntity:
        """Create an MP subscription with auto-recurring billing.

        Args:
            tenant_id: The tenant requesting the subscription.
            plan_type: The target plan type.
            card_token_id: Card token from MercadoPago.js CardForm.
            payer_email: Email of the payer.

        Returns:
            The updated SubscriptionEntity entity with gateway_subscription_id set.

        Raises:
            PlanNotChangeableError: If the plan is FREE, unpriced, or not found.
            NotFoundError: If no subscription exists for the tenant.
            DuplicatedError: If the tenant already has an active
                MP-managed subscription.
        """
        async with self.uow as uow:
            plan_repo = uow.get_repository(IPlanRepository)
            subscription_repo = uow.get_repository(ISubscriptionRepository)

            # Load plan
            plan = await plan_repo.get_by_plan_type(plan_type)
            if plan is None:
                raise PlanNotChangeableError(f"No existe el plan: {plan_type.value}")

            # GUARD: FREE plan / zero-price plans cannot have subscriptions
            if plan.price_monthly is None or plan.price_monthly.amount <= Decimal("0"):
                raise PlanNotChangeableError("No se puede crear una suscripción para el plan FREE")

            # Load subscription
            subscription = await subscription_repo.get_current_by_tenant(tenant_id)
            if subscription is None:
                raise NotFoundError(f"No existe una suscripción para el tenant {tenant_id}")

            # GUARD: tenant already has a gateway-managed subscription
            if subscription.gateway_subscription_id is not None:
                raise DuplicatedError(f"El tenant {tenant_id} ya tiene una suscripción activa ({subscription.gateway_subscription_id})")

            # Build auto_recurring config
            auto_recurring = AutoRecurringData(
                frequency=1,
                frequency_type="months",
                transaction_amount=float(plan.price_monthly.amount),
                currency_id="ARS",
            )

            external_reference = f"{tenant_id}:{plan_type.value}"
            back_url = self.webhook_url

            # Call gateway
            result: SubscriptionResult = await self.gateway.create_subscription(
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
            result_sub = await subscription_repo.update(updated)
            await uow.commit()
            return result_sub
