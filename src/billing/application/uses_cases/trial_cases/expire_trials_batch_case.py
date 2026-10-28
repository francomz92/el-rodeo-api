"""ExpireTrialsBatchCase — expires every trial subscription past its end.

System-worker batch: iterates ALL tenants, so it sets ``bypass_filter`` on its
unit of work — the standard cross-tenant signal for any ``TenantAwareRepository``
the UoW builds. The billing repositories scope ``tenant_id`` explicitly per
query and do not inherit ``TenantAwareRepository``, so the flag does not change
their queries (F2-4 map #8). Each subscription is committed individually;
errors are logged per subscription without crashing the batch.
"""

from __future__ import annotations

from dataclasses import replace

from src.billing.domain.constants.plans import PlanTypeEntity
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.application.ports.uow import IUoWFactory
from src.common.utils import log


class ExpireTrialsBatchCase:
    """Use case that transitions every expired TRIAL subscription to EXPIRED/FREE."""

    def __init__(self, uow_factory: IUoWFactory) -> None:
        self.uow_factory = uow_factory

    async def execute(self) -> dict:
        """Expire TRIAL subscriptions whose trial period has ended.

        Finds all subscriptions with status TRIAL and a ``trial_end`` in
        the past, sets their status to EXPIRED, and moves them to the FREE
        plan. This ensures expired tenants have the correct plan and limits.

        Returns:
            A summary dict with ``processed``, ``succeeded``, and ``failed``
            counts for monitoring.
        """
        uow = self.uow_factory()
        # System worker iterating every tenant. No-op for the billing repos
        # (they scope tenant_id per query — F2-4 map #8), but it is the
        # standard signal for any TenantAwareRepository this UoW builds.
        uow.bypass_filter = True

        async with uow:
            sub_repo: ISubscriptionRepository = uow.get_repository(ISubscriptionRepository)
            plan_repo: IPlanRepository = uow.get_repository(IPlanRepository)

            free_plan = await plan_repo.get_by_plan_type(PlanTypeEntity.FREE)
            if free_plan is None:
                log.warning("expire_trials_batch — FREE plan not found, skipping trial expiry")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            subs = await sub_repo.list_expired_trials()

            if not subs:
                log.info("expire_trials_batch — no expired trials to process")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            succeeded = 0
            failed = 0

            for sub in subs:
                try:
                    updated = replace(
                        sub,
                        status=SubscriptionStatus.EXPIRED,
                        plan_id=free_plan.id,
                    )
                    await sub_repo.update(updated)
                    await uow.commit()
                    log.info(
                        "expire_trials_batch — expired trial",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    succeeded += 1
                except Exception:
                    await uow.rollback()
                    log.exception(
                        "expire_trials_batch — failed for subscription",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    failed += 1

            log.info(
                "expire_trials_batch completed",
                processed=len(subs),
                succeeded=succeeded,
                failed=failed,
            )
            return {"processed": len(subs), "succeeded": succeeded, "failed": failed}
