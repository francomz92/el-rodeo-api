from celery import Celery
from celery.schedules import crontab

from src.cattle.infrastructure.workers.upcoming_events_tasks import notify_upcoming_events


def register_cron_tasks(app: Celery, **kwargs):
    app.add_periodic_task(
        name="notify_upcoming_events",
        schedule=crontab(hour=0),
        sig=notify_upcoming_events.s(),
    )
