"""TrialService — pure rules for trial subscription lifecycle.

Duration math and entity construction for trials; no I/O.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.plans import PlanEntity
from src.billing.domain.entities.subscriptions import SubscriptionEntity


class TrialService:
    """Builds trial subscriptions from the configured trial duration."""

    def __init__(self, trial_days: int) -> None:
        self.trial_days = trial_days

    def build_trial_subscription(self, tenant_id: UUID, plan: PlanEntity) -> SubscriptionEntity:
        """Create a TRIAL SubscriptionEntity with trial_end = now + trial_days."""
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=self.trial_days)

        return SubscriptionEntity(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=trial_end,
            trial_end=trial_end,
        )
