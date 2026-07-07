"""Health check endpoint.

Provides a ``GET /health`` endpoint that verifies connectivity to
PostgreSQL and Redis. Returns HTTP 200 when all services are reachable,
HTTP 503 when any service is unreachable.
"""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.utils import log

health_router = APIRouter()


class HealthResponse(BaseModel):
    """Schema for the health check response body."""

    status: str  # "healthy" | "unhealthy"
    database: str  # "ok" | "unreachable"
    redis: str  # "ok" | "unreachable"


@health_router.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {"description": "All services healthy"},
        503: {"description": "One or more services unhealthy", "model": HealthResponse},
    },
    summary="Health check",
    description="Returns connectivity status for database and Redis.",
    tags=["observability"],
)
async def health_check(response: Response) -> HealthResponse:
    """Verify database and Redis connectivity.

    Returns:
        200 with ``status: "healthy"``, ``database: "ok"``, ``redis: "ok"``
        when all services are reachable.

        503 with ``status: "unhealthy"`` and per-service ``"unreachable"``
        status when any service is down.
    """
    cid = get_correlation_id()

    # Lazy imports — use whatever engine/redis the app has at call time
    from src.common.infrastructure.persistence.connections.db import engine
    from src.common.infrastructure.persistence.connections.redis import _redis_client

    # ── Check database ───────────────────────────────────────────────────
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    # ── Check Redis ──────────────────────────────────────────────────────
    redis_status = "ok"
    try:
        await _redis_client.ping()  # type: ignore[misc]
    except Exception:
        redis_status = "unreachable"

    # ── Determine overall health ─────────────────────────────────────────
    all_healthy = db_status == "ok" and redis_status == "ok"
    overall = "healthy" if all_healthy else "unhealthy"

    # ── Set response status ────────────────────────────────────────────
    http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    response.status_code = http_status

    log.info(
        "Health check: {status} (db={db}, redis={redis})",
        status=overall,
        db=db_status,
        redis=redis_status,
        correlation_id=cid,
    )

    return HealthResponse(status=overall, database=db_status, redis=redis_status)
