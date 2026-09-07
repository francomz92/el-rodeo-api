"""Celery periodic task for forwarding pending outbox events to webhook subscribers.

The ``outbox_forwarder_task`` runs every 60 seconds (configured in
``cron_tasks_register.py``), picks up PENDING ``EventOutbox`` rows,
matches them against active ``WebhookSubscription`` records by event
type, and delivers signed HTTP POST requests.
"""

from __future__ import annotations

from celery import shared_task

from src.common.domain.repositories.webhook_subscription_repository_port import (
    IWebhookSubscriptionRepository,
)
from src.common.infrastructure.events.outbox_repository import OutboxRepository
from src.common.infrastructure.events.webhook_dispatcher import WebhookDispatcher
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork
from src.common.infrastructure.security.fernet_engine import FernetEngine
from src.common.utils import log

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
    log.info("outbox_forwarder_task started")

    async def _run() -> dict:
        async with AsyncSessionMaker() as session:
            uow = UnitOfWork(session=session, bypass_filter=True)
            outbox_repo = OutboxRepository(session)
            webhook_repo = uow.get_repository(IWebhookSubscriptionRepository)

            # 1. Fetch pending + retryable failed events (oldest first, limited batch)
            pending = await outbox_repo.get_pending(OUTBOX_BATCH_LIMIT)

            if not pending:
                log.info("outbox_forwarder_task — no pending events")
                return {"processed": 0, "succeeded": 0, "failed": 0}

            # 2. Fetch active webhook subscriptions (cross-tenant via bypass_filter)
            subscriptions = await webhook_repo.list_all_active()

            if not subscriptions:
                log.info("outbox_forwarder_task — no active subscriptions")
                # Mark all as SENT (no subscribers to notify)
                for event in pending:
                    await outbox_repo.mark_sent(event)
                await uow.commit()
                return {
                    "processed": len(pending),
                    "succeeded": len(pending),
                    "failed": 0,
                }

            # 3. Build subscriber index: event_type -> list of subscriptions
            subs_by_event: dict[str, list] = {}
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
                    await outbox_repo.mark_sent(event)
                    succeeded += 1
                    continue

                all_ok = True
                for sub in subscribers:
                    # Decrypt the secret — stored encrypted, used plaintext for HMAC
                    # Falls back to the raw value for backward compatibility with
                    # secrets stored before encryption was added.
                    try:
                        plain_secret = FernetEngine.decrypt_secret(sub.secret)
                    except Exception:
                        plain_secret = sub.secret
                    ok = await dispatcher.dispatch(
                        url=sub.url,
                        secret=plain_secret,
                        payload=event.payload,
                        event_id=str(event.event_id),
                    )
                    if not ok:
                        all_ok = False
                        sub.failure_count += 1
                        if sub.failure_count >= 5:
                            sub.is_active = False
                            await webhook_repo.update(
                                id=sub.id,
                                is_active=False,
                            )
                            log.warning(
                                "Deactivated webhook {} after {} failures",
                                sub.id,
                                sub.failure_count,
                            )

                if all_ok:
                    await outbox_repo.mark_sent(event)
                    succeeded += 1
                else:
                    event.retry_count += 1
                    if event.retry_count >= MAX_OUTBOX_RETRIES:
                        await outbox_repo.mark_failed(event)
                        log.warning(
                            "Outbox event {} (type={}) permanently failed after {} retries",
                            event.id,
                            event.event_type,
                            event.retry_count,
                        )
                    failed += 1

            await uow.commit()

            log.info("outbox_forwarder_task completed")
            return {
                "processed": len(pending),
                "succeeded": succeeded,
                "failed": failed,
            }

    try:
        import asyncio
        import concurrent.futures

        # asyncio.run() requires no running loop — safe under Celery prefork.
        # Under --pool=asyncio or --pool=gevent, the loop is already running
        # so we delegate to a thread pool executor.
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _run()).result()
    except Exception:
        log.exception("outbox_forwarder_task — unexpected failure")
        return {"processed": 0, "succeeded": 0, "failed": 0}
