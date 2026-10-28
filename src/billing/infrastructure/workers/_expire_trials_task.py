"""Celery task for trial subscription expiry.

Thin wrapper: all orchestration lives in
``ExpireTrialsBatchCase`` (application layer). The task only wires the
worker UoW factory and returns the summary.
"""

from __future__ import annotations

import asyncio

from celery import shared_task

from src.billing.application.uses_cases.trial_cases.expire_trials_batch_case import (
    ExpireTrialsBatchCase,
)
from src.common.infrastructure.persistence.uow import UnitOfWorkFactory
from src.common.utils import log


@shared_task
def expire_trials_task() -> dict:
    """Expire TRIAL subscriptions whose trial period has ended.

    Returns:
        A summary dict with ``processed``, ``succeeded``, and ``failed``
        counts for monitoring.
    """
    log.info("expire_trials_task started")

    async def _run() -> dict:
        case = ExpireTrialsBatchCase(uow_factory=UnitOfWorkFactory())
        return await case.execute()

    try:
        return asyncio.run(_run())
    except Exception:
        log.exception("expire_trials_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}
