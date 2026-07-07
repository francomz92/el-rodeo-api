from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.common.domain.types import EnvironmentType
from src.common.infrastructure.adapters.http.output.errors import StandardErrorResponse
from src.common.infrastructure.adapters.websocket.subscriber import RedisPubSubSubscriber
from src.common.infrastructure.core import settings
from src.common.infrastructure.core.app import configure_app
from src.common.infrastructure.persistence.connections.db import engine
from src.common.infrastructure.persistence.connections.redis import _redis_client
from src.common.infrastructure.persistence.models import Model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use Alembic migrations when available; fall back to create_all for dev
    if settings.ENVIRONMENT is EnvironmentType.DEVELOPMENT:
        async with engine.begin() as conn:
            has_migrations = await conn.run_sync(lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "alembic_version"))
            if not has_migrations:
                await conn.run_sync(Model.metadata.create_all)

    # ── WebSocket Pub/Sub subscriber ─────────────────────────────────────
    from src.common.infrastructure.presentation.dependencies.websocket import (
        _get_ws_manager,
    )

    ws_manager = _get_ws_manager()
    ws_subscriber = RedisPubSubSubscriber(
        redis_client=_redis_client,
        manager=ws_manager,
    )
    await ws_subscriber.start()

    # Store subscriber in app state for potential lifecycle access
    app.state.ws_subscriber = ws_subscriber

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    await ws_subscriber.stop()
    await ws_manager.close_all()


app = FastAPI(
    version="0.1.0",
    lifespan=lifespan,
    **settings.EXTRA_APP_CONFIG,
    responses={
        422: {"model": StandardErrorResponse},
    },
)
configure_app(app)

# ── Prometheus metrics ──────────────────────────────────────────────────────
# Must be configured AFTER the middleware chain so it wraps the entire app.
if settings.PROMETHEUS_ENABLED:
    from prometheus_fastapi_instrumentator import Instrumentator

    instrumentator = Instrumentator().instrument(app)
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
