import asyncio

from celery import Task, shared_task

from src.cattle.application.services.notifications.scheduled_events_reminder_service import ScheduledEventsReminderService
from src.cattle.application.uses_cases.schedule_events_use_cases.norifi_upcoming_events_case import NotifyUpcomingEventsCase
from src.common.infrastructure.adapters.workers.email_workers import EmailNotifier
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork


@shared_task
def notify_upcoming_events():
    async def _run_task():
        async with AsyncSessionMaker() as session:
            case = NotifyUpcomingEventsCase(
                uow=UnitOfWork(session=session),
                notifier=EmailNotifier(),
                service=ScheduledEventsReminderService(),
            )
            await case.execute()

    asyncio.run(_run_task())


notify_upcoming_events: Task = notify_upcoming_events
