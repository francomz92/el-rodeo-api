from celery import Celery

from src.common.infrastructure.core import settings
from src.common.utils import log

from .cron_tasks_register import register_cron_tasks

app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL,
    log=log,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
app.autodiscover_tasks(
    packages=[
        "src.common.infrastructure.workers.email_tasks",
        "src.cattle.infrastructure.workers.upcoming_events_tasks",
    ]
)

register_cron_tasks(app)
