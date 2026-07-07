"""Celery periodic task for forwarding pending outbox events to webhook subscribers.

The ``outbox_forwarder_task`` runs every 60 seconds (configured in
``cron_tasks_register.py``), picks up PENDING ``EventOutbox`` rows,
matches them against active ``WebhookSubscription`` records by event
type, and delivers signed HTTP POST requests.
"""

from __future__ import annotations

from celery import shared_task
from loguru import logger
from sqlalchemy import select

from src.common.infrastructure.events.webhook_dispatcher import WebhookDispatcher
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.models.event_outbox import (
    EventOutbox,
    OutboxStatus,
)
from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)

OUTBOX_BATCH_LIMIT = 50
MAX_OUTBOX_RETRIES = 5


@shared_task
def outbox_forwarder_task() -> dict:
    """Forward pending outbox events to matching webhook subscribers.

    Queries up to ``OUTBOX_BATCH_LIMIT`` PENDING events, finds all active
    WebhookSubscriptions whose ``subscribed_events`` list contains the
    event type, and POSTs a signed payload to each subscriber URL.

    Events are marked SENT only when all deliveries succeed.
    If any delivery fails, the event is marked FAILED and the
    subscriber's ``failure_count`` is incremented (auto-deactivated at 5).

    Returns:
        A summary dict with ``processed``, ``succeeded``, ``failed`` counts.
    """
    logger.info("outbox_forwarder_task started")

    async def _run() -> dict:
        async with AsyncSessionMaker() as session:
            # 1. Fetch pending + retryable failed events (oldest first, limited batch)
            stmt_events = (
                select(EventOutbox)
                .where(
                    (EventOutbox.status == OutboxStatus.PENDING)
                    | ((EventOutbox.status == OutboxStatus.FAILED) & (EventOutbox.retry_count < MAX_OUTBOX_RETRIES))
                )
                .order_by(EventOutbox.created_at)
                .limit(OUTBOX_BATCH_LIMIT)
            )
            result = await session.execute(stmt_events)
            pending = list(result.scalars().all())

            if not pending:
                logger.info("outbox_forwarder_task — no pending events")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            # 2. Fetch active webhook subscriptions
            stmt_subs = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
            result = await session.execute(stmt_subs)
            subscriptions = list(result.scalars().all())

            if not subscriptions:
                logger.info("outbox_forwarder_task — no active subscriptions")
                # Mark all as SENT (no subscribers to notify)
                for event in pending:
                    event.status = OutboxStatus.SENT
                await session.commit()
                return {
                    "processed": len(pending),
                    "succeeded": len(pending),
                    "failed": 0,
                }

            # 3. Build subscriber index: event_type -> list of subscriptions
            subs_by_event: dict[str, list[WebhookSubscription]] = {}
            for sub in subscriptions:
                for evt_type in sub.subscribed_events:
                    subs_by_event.setdefault(evt_type, []).append(sub)

            dispatcher = WebhookDispatcher()
            succeeded = 0
            failed = 0

            # 4. Deliver each event
            for event in pending:
                subscribers = subs_by_event.get(event.event_type, [])
                if not subscribers:
                    # No one subscribed to this event type — mark sent
                    event.status = OutboxStatus.SENT
                    succeeded += 1
                    continue

                all_ok = True
                for sub in subscribers:
                    ok = await dispatcher.dispatch(
                        url=sub.url,
                        secret=sub.secret,
                        payload=event.payload,
                    )
                    if not ok:
                        all_ok = False
                        sub.failure_count += 1
                        if sub.failure_count >= 5:
                            sub.is_active = False
                            logger.warning(
                                "Deactivated webhook {} after {} failures",
                                sub.id,
                                sub.failure_count,
                            )

                if all_ok:
                    event.status = OutboxStatus.SENT
                    succeeded += 1
                else:
                    event.retry_count += 1
                    if event.retry_count >= MAX_OUTBOX_RETRIES:
                        event.status = OutboxStatus.FAILED
                        logger.warning(
                            "Outbox event {} (type={}) permanently failed after {} retries",
                            event.id,
                            event.event_type,
                            event.retry_count,
                        )
                    else:
                        # Keep as PENDING so it's picked up in the next cycle
                        event.status = OutboxStatus.PENDING
                    failed += 1

            await session.commit()

            logger.info(
                "outbox_forwarder_task completed",
                processed=len(pending),
                succeeded=succeeded,
                failed=failed,
            )
            return {
                "processed": len(pending),
                "succeeded": succeeded,
                "failed": failed,
            }

    try:
        import asyncio

        return asyncio.run(_run())
    except Exception:
        logger.exception("outbox_forwarder_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}
