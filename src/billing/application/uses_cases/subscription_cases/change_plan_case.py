"""ChangePlanCase — handles plan upgrade/downgrade for tenant subscriptions.

Provides:
- execute: validates business rules via the domain ChangePlanService,
  delegates upgrades to CreateCheckoutCase, applies downgrades immediately,
  returns (subscription, checkout_url).
"""

from dataclasses import replace
from uuid import UUID

from src.billing.application.uses_cases.plan_cases.create_checkout_case import (
    CreateCheckoutCase,
)
from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.billing.domain.services.subscription_services.change_plan_service import (
    ChangePlanService,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError


class ChangePlanCase:
    """Use case that manages subscription plan changes.

    Encapsulates the rules for upgrading (requires payment) and downgrading
    (immediate plan_id change) while rejecting invalid transitions.
    """

    def __init__(
        self,
        uow: IUoW,
        service: ChangePlanService,
        create_checkout_case: CreateCheckoutCase | None,
    ) -> None:
        self.uow = uow
        self.service = service
        self.create_checkout_case = create_checkout_case

    async def execute(
        self,
        tenant_id: UUID,
        new_plan_type: PlanTypeEntity,
    ) -> tuple[SubscriptionEntity, str | None]:
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
            A tuple of ``(SubscriptionEntity, str | None)`` where the string is the
            MP ``init_point`` URL for upgrades, or ``None`` otherwise.

        Raises:
            PlanNotChangeableError: If the transition is not allowed, the
                target plan does not exist, or an upgrade is attempted while
                the payment gateway is not configured.
            NotFoundError: If no subscription exists for the tenant, or the
                subscription's current plan row is missing.
        """
        async with self.uow as uow:
            sub_repo = uow.get_repository(ISubscriptionRepository)
            plan_repo = uow.get_repository(IPlanRepository)

            # --- Load current subscription ---
            subscription = await sub_repo.get_current_by_tenant(tenant_id)
            if subscription is None:
                raise NotFoundError(f"No existe una suscripción para el tenant {tenant_id}")

            # --- Guards: FREE not selectable, TRIAL/non-ACTIVE cannot change ---
            self.service.assert_change_allowed(subscription, new_plan_type)

            # --- Determine current plan ---
            current_plan = await plan_repo.get_by_id(subscription.plan_id)
            if current_plan is None:
                raise NotFoundError(f"No existe el plan {subscription.plan_id}")

            # --- Same plan → no-op ---
            if self.service.is_same_plan(current_plan, new_plan_type):
                return subscription, None

            # --- Load target plan ---
            new_plan = await plan_repo.get_by_plan_type(new_plan_type)
            if new_plan is None:
                raise PlanNotChangeableError(f"No existe el plan: {new_plan_type.value}")

            # --- Upgrade: paid plan → create MP preference (don't apply yet) ---
            if self.service.requires_payment(new_plan):
                if self.create_checkout_case is None:
                    raise PlanNotChangeableError("La pasarela de pago no está configurada. No se puede procesar el cambio de plan.")
                # The checkout case commits the pending payment record itself.
                init_point = await self.create_checkout_case.execute(tenant_id, new_plan_type)
                return subscription, init_point

            # --- Downgrade / free plan: apply immediately ---
            updated = replace(subscription, plan_id=new_plan.id)
            result = await sub_repo.update(updated)
            await uow.commit()
            return result, None
