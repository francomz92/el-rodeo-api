import asyncio

from celery import Celery
from celery.signals import worker_process_init, worker_ready

from src.common.infrastructure.adapters.logger import configure_logger
from src.common.infrastructure.core import settings
from src.common.infrastructure.persistence.connections.db import worker_session_engine

from .cron_tasks_register import register_cron_tasks

app = Celery(
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


app.autodiscover_tasks(
    packages=[
        "src.common.infrastructure.workers.email_tasks",
        "src.common.infrastructure.workers.event_tasks",
        "src.calendar.infrastructure.workers.upcoming_events_tasks",
        "src.billing.infrastructure.workers._expire_trials_task",
        "src.billing.infrastructure.workers._monthly_billing_task",
    ]
)

register_cron_tasks(app)


@worker_ready.connect
def _setup_worker_logging(**kwargs) -> None:
    """Configure structured logging on Celery worker start.

    This uses the same ``configure_logger()`` as the FastAPI app, so
    Celery task logs use the same format (JSON or text) and handlers.
    The ``WorkerReady`` signal fires once per worker process after
    fork, so every child process gets its own Loguru configuration.
    """
    configure_logger()


@worker_process_init.connect(weak=False)
def _setup_engine_recicle(**kwargs) -> None:
    asyncio.run(worker_session_engine.dispose())
