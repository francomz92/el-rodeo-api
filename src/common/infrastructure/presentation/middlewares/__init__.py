from fastapi import FastAPI

from src.common.infrastructure.core import settings

from .body_size_limit import BodySizeLimitMiddleware
from .compresion import configure_compression_body
from .cors import configure_cors
from .rate_limiter import configure_rate_limiter
from .security_headers import SecurityHeadersMiddleware
from .trusted_host import configure_trusted_host

# Observability middleware — only added when OBSERVABILITY_MIDDLEWARE_ENABLED=True
try:
    from .correlation_id import CorrelationIdMiddleware  # type: ignore[import-untyped]
    from .request_logging import RequestLoggingMiddleware  # type: ignore[import-untyped]
except ImportError:
    CorrelationIdMiddleware = None  # type: ignore
    RequestLoggingMiddleware = None  # type: ignore


def configure_middlewares(app: FastAPI):
    """Register all middleware in the correct order.

    Order (outermost → innermost):
        1. TrustedHost — validates Host header (before any body processing)
        2. BodySizeLimit — reject oversized payloads before body is read
        3. CORS — handles OPTIONS preflight
        4. Rate Limiter — per-IP+endpoint limits (slowapi)
        5. Security Headers — injects security headers on every response
        6. Correlation ID — set ``X-Request-ID`` contextvar (observability)
        7. Request Logging — log method/path before and duration after
        8. GZip — compresses response body
    """
    # 1. Trusted Host — outermost, validates Host header before anything else
    configure_trusted_host(app)

    # 2. Body Size Limit — rejects oversized payloads before body is read
    app.add_middleware(BodySizeLimitMiddleware)  # type: ignore[arg-type]

    # 3. CORS — handles OPTIONS preflight
    configure_cors(app)

    # 4. Rate Limiter — slowapi middleware (registered inside configure_rate_limiter)
    configure_rate_limiter(app, settings)

    # 5. Security Headers — ASGI-level, runs after Rate Limiter
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)  # type: ignore[arg-type]

    # 6. Correlation ID — ASGI-level, runs after Security Headers
    if settings.OBSERVABILITY_MIDDLEWARE_ENABLED and CorrelationIdMiddleware is not None:
        app.add_middleware(CorrelationIdMiddleware)  # type: ignore[arg-type]

    # 7. Request Logging — ASGI-level, runs after Correlation ID
    if settings.OBSERVABILITY_MIDDLEWARE_ENABLED and RequestLoggingMiddleware is not None:
        app.add_middleware(RequestLoggingMiddleware)  # type: ignore[arg-type]

    # 8. GZip — compression (innermost)
    configure_compression_body(app)
