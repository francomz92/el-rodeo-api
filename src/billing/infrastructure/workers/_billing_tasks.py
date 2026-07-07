"""Celery tasks for billing: monthly preference creation and trial expiry.

Tasks
-----
monthly_billing_task
    Create MercadoPago Checkout Pro preferences for ACTIVE subscriptions
    whose ``current_period_end`` is within the next 7 days.  Each
    subscription gets a PENDING payment record and an MP preference for
    the same plan they are currently on.  Errors are logged per
    subscription without crashing the batch.

expire_trials_task
    Transition every TRIAL subscription with a past ``trial_end`` to
    EXPIRED and move it to the FREE plan.  Errors are logged per
    subscription without crashing the batch.

Both tasks return a summary dict ``{processed, succeeded, failed}``
that is written to the Celery result backend for monitoring.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from celery import shared_task
from loguru import logger

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import (
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
    ItemData,
)
from src.billing.infrastructure.payment_gateway._client import MercadoPagoHttpClient
from src.billing.infrastructure.persistence.repositories._plan_repository import PlanRepository
from src.common.infrastructure.core._config import settings
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork


@shared_task
def monthly_billing_task() -> dict:
    """Create MercadoPago preferences for ACTIVE subscriptions near period end.

    For every ACTIVE subscription whose ``current_period_end`` falls within
    the next 7 days, a new checkout preference is created for the same plan
    and a PENDING payment record is persisted.

    Individual errors are caught and logged so that a single failing
    subscription does not block the rest of the batch.

    Returns:
        A summary dict with ``processed``, ``succeeded``, and ``failed``
        counts for monitoring.
    """
    logger.info("monthly_billing_task started")

    async def _run() -> dict:
        async with AsyncSessionMaker() as session:
            uow = UnitOfWork(session=session)
            sub_repo: ISubscriptionRepository = uow.get_repository(
                ISubscriptionRepository  # type: ignore[assignment]
            )
            plan_repo: IPlanRepository = PlanRepository()
            payment_repo: IPaymentRepository = uow.get_repository(
                IPaymentRepository  # type: ignore[assignment]
            )

            # Guard: MP client may raise if access token is missing
            try:
                gateway = MercadoPagoHttpClient()
            except Exception as exc:
                logger.error("monthly_billing_task — failed to initialise MP client: {}", exc)
                return {"processed": 0, "succeeded": 0, "failed": 0}

            subs = await sub_repo.list_active_near_period_end(7)

            if not subs:
                logger.info("monthly_billing_task — no subscriptions near period end")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            succeeded = 0
            failed = 0

            for idx, sub in enumerate(subs):
                try:
                    plan = await plan_repo.get_by_id(sub.plan_id)
                    if plan is None:
                        logger.warning(
                            "monthly_billing_task — plan not found",
                            sub_id=str(sub.id),
                            plan_id=str(sub.plan_id),
                        )
                        failed += 1
                        continue

                    # FREE / zero-price plans need no billing
                    if plan.price_monthly is None or plan.price_monthly.amount <= 0:
                        logger.info(
                            "monthly_billing_task — skipping free plan",
                            sub_id=str(sub.id),
                            plan_type=plan.plan_type.value,
                        )
                        succeeded += 1
                        continue

                    # Build checkout payload
                    item = ItemData(
                        title=f"Plan {plan.name} - El Rodeo",
                        quantity=1,
                        unit_price=plan.price_monthly.amount,
                        currency_id="ARS",
                    )

                    external_ref = f"{sub.tenant_id}:{plan.plan_type.value}"

                    result = await gateway.create_preference(
                        items=[item],
                        back_urls={
                            "success": settings.MP_WEBHOOK_URL,
                            "failure": settings.MP_WEBHOOK_URL,
                            "pending": settings.MP_WEBHOOK_URL,
                        },
                        notification_url=settings.MP_WEBHOOK_URL,
                        external_reference=external_ref,
                    )

                    # Persist PENDING payment record
                    payment = Payment(
                        tenant_id=sub.tenant_id,
                        subscription_id=sub.id,
                        status=PaymentStatus.PENDING,
                        amount=plan.price_monthly.amount,
                        mp_preference_id=result.id,
                        description=f"Plan {plan.name} - El Rodeo",
                    )
                    await payment_repo.create(payment)

                    await uow.commit()

                    logger.info(
                        "monthly_billing_task — created preference",
                        tenant_id=str(sub.tenant_id),
                        preference_id=result.id,
                        idx=idx,
                    )
                    succeeded += 1

                except Exception:
                    logger.exception(
                        "monthly_billing_task — failed for subscription",
                        tenant_id=str(sub.tenant_id),
                        sub_id=str(sub.id),
                    )
                    failed += 1

            logger.info(
                "monthly_billing_task completed",
                processed=len(subs),
                succeeded=succeeded,
                failed=failed,
            )
            return {"processed": len(subs), "succeeded": succeeded, "failed": failed}

    try:
        return asyncio.run(_run())
    except Exception:
        logger.exception("monthly_billing_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}


@shared_task
def expire_trials_task() -> dict:
    """Expire TRIAL subscriptions whose trial period has ended.

    Finds all subscriptions with status TRIAL and a ``trial_end`` in the
    past, sets their status to EXPIRED, and moves them to the FREE plan.
    This ensures that expired tenants have the correct plan and limits.

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

            free_plan = await plan_repo.get_by_plan_type(PlanType.FREE)

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

            await uow.commit()

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
