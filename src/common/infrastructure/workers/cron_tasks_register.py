from celery import Celery
from celery.schedules import crontab

from src.billing.infrastructure.workers._expire_trials_task import expire_trials_task
from src.billing.infrastructure.workers._monthly_billing_task import monthly_billing_task
from src.calendar.infrastructure.workers.upcoming_events_tasks import notify_upcoming_events
from src.common.infrastructure.workers.event_tasks import outbox_forwarder_task


def register_cron_tasks(app: Celery, **kwargs):
    app.add_periodic_task(
        name="outbox_forwarder",
        schedule=60.0,
        sig=outbox_forwarder_task.s(),
    )

    app.add_periodic_task(
        name="notify_upcoming_events",
        schedule=crontab(hour=0),
        sig=notify_upcoming_events.s(),  # type: ignore[attr-defined]
    )

    app.add_periodic_task(
        name="monthly_billing",
        schedule=crontab(hour=2, minute=0),  # Daily at 02:00 UTC
        sig=monthly_billing_task.s(),
    )

    app.add_periodic_task(
        name="expire_trials",
        schedule=crontab(hour=3, minute=0),  # Daily at 03:00 UTC
        sig=expire_trials_task.s(),
    )
