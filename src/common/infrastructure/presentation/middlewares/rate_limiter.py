"""Rate limiter configuration using slowapi.

Initialises a slowapi Limiter with Redis backend in production/staging
and in-memory backend in development. Defines per-endpoint limits
from application settings and exempts health/static paths.

Endpoints are protected by ``@rate_limit("5/minute")`` decorators that
only apply rate limiting when ``settings.ENABLE_RATE_LIMIT`` is True.
"""

from typing import Any

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware

from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.middlewares.ip_utils import get_client_ip
from src.common.utils import log

# Module-level limiter — initialised on import.
# Uses RATE_LIMIT_DEFAULT as the middleware-level default (100/minute).
# Per-endpoint @rate_limit decorators add/override limits on top.

limiter = Limiter(
    key_func=get_client_ip,
    storage_uri="memory://",
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.ENABLE_RATE_LIMIT else [],
)

# Paths that are exempt from rate limiting.
EXEMPT_PATHS: list[str] = [
    "/health",
    "/metrics",
    "/static",
    "/openapi.json",
    "/docs",
]


def rate_limit(limit_string: str):
    """Decorator that applies a ``@limiter.limit()`` when rate limiting is enabled.

    Only applies the limit when ``settings.ENABLE_RATE_LIMIT`` is True.
    The decorated function must accept ``request: Request`` as a parameter.

    Args:
        limit_string: Rate limit string, e.g. "5/minute".

    Returns:
        Decorator that optionally wraps the function with slowapi's limiter.
    """

    def decorator(func):
        if settings.ENABLE_RATE_LIMIT:
            return limiter.limit(limit_string)(func)
        return func

    return decorator


def get_rate_limit_limits(settings: Any) -> dict[str, str]:
    """Extract per-endpoint rate limit strings from settings.

    Args:
        settings: Application settings with RATE_LIMIT_* fields.

    Returns:
        Dict mapping endpoint names to rate limit strings.
    """
    return {
        "login": settings.RATE_LIMIT_LOGIN,
        "register": settings.RATE_LIMIT_REGISTER,
        "password_change": settings.RATE_LIMIT_PASSWORD_CHANGE,
        "refresh": settings.RATE_LIMIT_REFRESH,
    }


def _maybe_switch_to_redis(settings: Any) -> None:
    """Switch the module-level limiter to Redis storage if possible.

    Checks whether ``settings.REDIS_URL`` is set to a non-memory URL, then
    attempts a ``PING``. On success the module-level ``limiter`` is rebuilt
    with ``storage_uri=settings.REDIS_URL``. On failure a warning is logged
    and the in-memory backend is preserved.

    This is called once at startup from ``configure_rate_limiter``.
    """
    redis_url: str = getattr(settings, "REDIS_URL", "")
    if not redis_url or redis_url == "memory://" or redis_url.startswith("memory://"):
        return  # Keep in-memory backend — no Redis configuration

    global limiter
    try:
        import asyncio

        from redis.asyncio import Redis as AsyncRedis

        # Use a fresh event loop for the startup probe (we are not inside
        # an async context yet).
        loop = asyncio.new_event_loop()
        try:
            probe = AsyncRedis.from_url(redis_url, socket_connect_timeout=2)
            loop.run_until_complete(probe.ping())
            loop.run_until_complete(probe.aclose())
        except Exception as err:
            log.warning(
                "Redis error: {err}",
                err=err,
            )
            raise  # Re-raise so the outer except triggers the in-memory fallback
        finally:
            loop.close()

        # Redis is reachable — switch the limiter to Redis storage.
        limiter = Limiter(
            key_func=get_client_ip,
            storage_uri=redis_url,
            default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.ENABLE_RATE_LIMIT else [],
        )
        log.info(
            "Rate limiter switched to Redis backend: {url}",
            url=redis_url,
        )
    except Exception as exc:
        log.warning(
            "Redis unreachable for rate limiter, falling back to in-memory: {exc}",
            exc=exc,
        )


def configure_rate_limiter(app: Any) -> Limiter:
    """Attach the module-level Limiter to the FastAPI app.

    In development mode uses the default in-memory storage.
    In production/staging, switches to Redis storage when ``REDIS_URL``
    is configured and reachable. Falls back to in-memory on failure.

    Args:
        app: FastAPI application instance.
        settings: Application settings with rate limit config and REDIS_URL.

    Returns:
        The module-level Limiter instance.
    """
    # ── Auto-detect Redis backend ──────────────────────────────────────────
    _maybe_switch_to_redis(settings)

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)  # type: ignore[arg-type]
    return limiter
