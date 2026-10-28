"""Celery task for monthly billing preference creation.

Thin wrapper: all orchestration lives in ``MonthlyBillingCase``
(application layer). The task only wires the gateway, URLs, and the
worker UoW factory, and returns the summary.
"""

from __future__ import annotations

import asyncio

from celery import shared_task

from src.billing.application.uses_cases.subscription_cases.monthly_billing_case import (
    MonthlyBillingCase,
)
from src.billing.infrastructure.adapters.payment_gateway.shared import (
    get_shared_mercadopago_client,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.persistence.uow import UnitOfWorkFactory
from src.common.utils import log


@shared_task
def monthly_billing_task() -> dict:
    """Create MercadoPago preferences for ACTIVE subscriptions near period end.

    Returns:
        A summary dict with ``processed``, ``succeeded``, and ``failed``
        counts for monitoring.
    """
    log.info("monthly_billing_task started")

    async def _run() -> dict:
        # Guard: MP client may raise if access token is missing. The shared
        # client is reused across worker runs (closed only on app shutdown).
        try:
            gateway = get_shared_mercadopago_client()
        except Exception as exc:
            log.error("monthly_billing_task — failed to initialise MP client: {}", exc)
            return {"processed": 0, "succeeded": 0, "failed": 0}

        case = MonthlyBillingCase(
            uow_factory=UnitOfWorkFactory(),
            gateway=gateway,
            frontend_url=settings.FRONTEND_URL,
            webhook_url=settings.MP_WEBHOOK_URL,
        )
        return await case.execute()

    try:
        return asyncio.run(_run())
    except Exception:
        log.exception("monthly_billing_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}
