import asyncio
from uuid import UUID

from celery import Task, shared_task

from src.cattle.application.services.notifications.scheduled_events_reminder_service import (
    ScheduledEventsReminderService,
)
from src.cattle.application.uses_cases.schedule_events_use_cases.notify_upcoming_events_case import (
    NotifyUpcomingEventsCase,
)
from src.common.infrastructure.adapters.workers.email_workers import EmailNotifier
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork
from src.common.utils import log


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_upcoming_events(self: Task, tenant_id: str | None = None) -> None:
    """Notify users about upcoming scheduled events.

    When tenant_id is provided: scope the notification to that tenant.
    When tenant_id is None (Celery Beat scheduled run): iterate all tenants.

    Args:
        tenant_id: Optional UUID string identifying a single tenant.
                   When None, all tenants are processed.
    """
    log.info(
        "notify_upcoming_events called",
        tenant_id=tenant_id or "all-tenants",
    )

    async def _run_single_tenant(tid: UUID | None) -> None:
        async with AsyncSessionMaker() as session:
            uow = UnitOfWork(session=session, tenant_id=tid)
            case = NotifyUpcomingEventsCase(
                uow=uow,
                notifier=EmailNotifier(),
                service=ScheduledEventsReminderService(),
            )
            await case.execute(tenant_id=tid)

    async def _run_all_tenants() -> None:
        """Iterate all tenants and process each one."""
        from src.auth.domain.repositories.tenant_repository_port import ITenantRepository

        async with AsyncSessionMaker() as session:
            uow = UnitOfWork(session=session, bypass_filter=True)
            tenant_repo = uow.get_repository(ITenantRepository)
            tenants = await tenant_repo.list_all()
            tenant_ids = [t.id for t in tenants]

        if not tenant_ids:
            log.warning("No tenants found — skipping upcoming events notification")
            return

        for tid in tenant_ids:
            log.info("Processing tenant", tenant_id=str(tid))
            try:
                await _run_single_tenant(tid)
            except Exception:
                log.exception("Failed to process tenant %s", tid)

    try:
        if tenant_id is not None:
            asyncio.run(_run_single_tenant(UUID(tenant_id)))
        else:
            asyncio.run(_run_all_tenants())
    except Exception as exc:
        log.exception("notify_upcoming_events failed")
        raise self.retry(exc=exc)
