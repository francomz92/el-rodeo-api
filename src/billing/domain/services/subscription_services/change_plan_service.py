"""ChangePlanService — pure business rules for subscription plan changes.

No I/O: every rule takes already-loaded entities and either raises or
returns a decision. Orchestration lives in ``ChangePlanCase``.
"""

from decimal import Decimal

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.plans import PlanEntity
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.exceptions import PlanNotChangeableError


class ChangePlanService:
    """Business rules for changing the plan of a tenant subscription.

    Encapsulates the rules for upgrading (requires payment) and downgrading
    (immediate plan_id change) while rejecting invalid transitions.
    """

    def assert_change_allowed(self, subscription: SubscriptionEntity, new_plan_type: PlanTypeEntity) -> None:
        """Guard: FREE is not selectable, TRIAL and non-ACTIVE cannot change plan.

        Raises:
            PlanNotChangeableError: If the transition is not allowed.
        """
        # --- GUARD: FREE is not selectable ---
        if new_plan_type == PlanTypeEntity.FREE:
            raise PlanNotChangeableError("No se puede seleccionar el plan FREE")

        # --- GUARD: TRIAL subscriptions cannot change plan ---
        if subscription.status == SubscriptionStatus.TRIAL:
            raise PlanNotChangeableError(
                "Las suscripciones de prueba no pueden cambiar de plan. Completa la prueba o activa la suscripción primero."
            )

        # --- Guard: ACTIVE subscription is required for plan changes ---
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise PlanNotChangeableError(
                f"La suscripción con estado '{subscription.status.value}' no puede cambiar de plan. Solo las suscripciones ACTIVE pueden cambiar de plan."
            )

    def is_same_plan(self, current_plan: PlanEntity, new_plan_type: PlanTypeEntity) -> bool:
        """Same plan → no-op."""
        return current_plan.plan_type == new_plan_type

    def requires_payment(self, new_plan: PlanEntity) -> bool:
        """Paid plan (price > 0) → upgrade via gateway preference; otherwise apply immediately."""
        return new_plan.price_monthly is not None and new_plan.price_monthly.amount > Decimal("0")
