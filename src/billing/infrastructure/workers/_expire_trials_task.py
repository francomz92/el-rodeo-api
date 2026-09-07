"""Celery task for trial subscription expiry.

Extracted from _billing_tasks.py (task 3.2 of modularizacion-estructura).

Transitions every TRIAL subscription with a past ``trial_end`` to
EXPIRED and moves it to the FREE plan.  Errors are logged per
subscription without crashing the batch.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from celery import shared_task
from loguru import logger

from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import (
    IPlanRepository,
    ISubscriptionRepository,
)
from src.billing.infrastructure.persistence.repositories._plan_repository import PlanRepository
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork


@shared_task
def expire_trials_task() -> dict:
    """Expire TRIAL subscriptions whose trial period has ended.

    Finds all subscriptions with status TRIAL and a ``trial_end`` in the
    past, sets their status to EXPIRED, and moves them to the FREE plan.
    This ensures expired tenants have the correct plan and limits.

    Individual errors are caught and logged so that a single failing
    subscription does not block the rest of the batch.

    Returns:
        A summary dict with ``processed``, ``succeeded``, and ``failed``
        counts for monitoring.
    """
    logger.info("expire_trials_task started")

    async def _run() -> dict:
        async with AsyncSessionMaker() as session:
            uow = UnitOfWork(session=session)
            sub_repo: ISubscriptionRepository = uow.get_repository(
                ISubscriptionRepository  # type: ignore[assignment]
            )
            plan_repo: IPlanRepository = PlanRepository()

            free_plan = await plan_repo.get_by_plan_type(PlanTypeEntity.FREE)
            if free_plan is None:
                logger.warning("FREE plan not found — skipping trial expiry")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            subs = await sub_repo.list_expired_trials()

            if not subs:
                logger.info("expire_trials_task — no expired trials to process")
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
                    logger.info(
                        "expire_trials_task — expired trial",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    succeeded += 1
                except Exception:
                    logger.exception(
                        "expire_trials_task — failed for subscription",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    failed += 1

            logger.info(
                "expire_trials_task completed",
                processed=len(subs),
                succeeded=succeeded,
                failed=failed,
            )
            return {"processed": len(subs), "succeeded": succeeded, "failed": failed}

    try:
        return asyncio.run(_run())
    except Exception:
        logger.exception("expire_trials_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}
