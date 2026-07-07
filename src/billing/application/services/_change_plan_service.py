"""ChangePlanService — handles plan upgrade/downgrade for tenant subscriptions.

Provides:
- change_plan: validates business rules, delegates upgrades to MercadoPagoService,
  applies downgrades immediately, returns (subscription, checkout_url).
"""

from dataclasses import replace
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.application.ports.uow import IUoW

if TYPE_CHECKING:
    from src.billing.application.services._mercadopago_service import (
        MercadoPagoService,
    )


class ChangePlanService:
    """Application service that manages subscription plan changes.

    Encapsulates the rules for upgrading (requires payment) and downgrading
    (immediate plan_id change) while rejecting invalid transitions.
    """

    def __init__(
        self,
        plan_repo: IPlanRepository,
        sub_repo: ISubscriptionRepository,
        mercado_pago_service: "MercadoPagoService | None",
        uow_factory: IUoW,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = sub_repo
        self._mp_service = mercado_pago_service
        self._uow_factory = uow_factory

    async def change_plan(
        self,
        tenant_id: UUID,
        new_plan_type: PlanType,
    ) -> tuple[Subscription, str | None]:
        """Change the subscription plan for a tenant.

        The behaviour depends on the new plan type and the current subscription
        state:

        * **FREE**: Rejected — FREE is only reachable via expiration.
        * **TRIAL subscription**: Rejected — plan changes require activation.
        * **Same plan**: No-op — returns ``(subscription, None)``.
        * **Upgrade** (paid plan): Creates an MP Checkout Pro preference and
          returns ``(subscription, init_point)`` without applying the change.
        * **Downgrade** (price = 0): Immediately updates the subscription's
          ``plan_id`` and returns ``(updated_sub, None)``.

        Args:
            tenant_id: The tenant requesting the change.
            new_plan_type: The target plan type.

        Returns:
            A tuple of ``(Subscription, str | None)`` where the string is the
            MP ``init_point`` URL for upgrades, or ``None`` otherwise.

        Raises:
            PlanNotChangeableError: If the transition is not allowed.
            ValueError: If no subscription exists for the tenant.
        """
        # --- Load current subscription ---
        subscription = await self._sub_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        # --- GUARD: FREE is not selectable ---
        if new_plan_type == PlanType.FREE:
            raise PlanNotChangeableError("FREE plan cannot be selected")

        # --- GUARD: TRIAL subscriptions cannot change plan ---
        if subscription.status == SubscriptionStatus.TRIAL:
            raise PlanNotChangeableError("Trial subscriptions cannot change plan. Complete the trial or activate the subscription first.")

        # --- Guard: ACTIVE subscription is required for plan changes ---
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise PlanNotChangeableError(
                f"Subscription with status '{subscription.status.value}' cannot change plan. Only ACTIVE subscriptions can change."
            )

        # --- Determine current plan ---
        current_plan = await self._plan_repo.get_by_id(subscription.plan_id)
        if current_plan is None:
            raise ValueError(f"Plan {subscription.plan_id} not found")

        # --- Same plan → no-op ---
        if current_plan.plan_type == new_plan_type:
            return subscription, None

        # --- Load target plan ---
        new_plan = await self._plan_repo.get_by_plan_type(new_plan_type)

        # --- Upgrade: paid plan → create MP preference (don't apply yet) ---
        if new_plan.price_monthly is not None and new_plan.price_monthly.amount > Decimal("0"):
            if self._mp_service is None:
                raise PlanNotChangeableError("Payment gateway is not configured. Cannot process upgrade.")
            init_point = await self._mp_service.create_checkout_preference(
                tenant_id,
                new_plan_type,
            )
            return subscription, init_point

        # --- Downgrade / free plan: apply immediately ---
        updated = replace(subscription, plan_id=new_plan.id)
        result = await self._sub_repo.update(updated)
        return result, None
