from fastapi import FastAPI

from src.common.infrastructure.core import settings

from .body_size_limit import configure_body_size_limit
from .compresion import configure_compression_body

# Observability middleware — only added when OBSERVABILITY_MIDDLEWARE_ENABLED=True
from .correlation_id import configure_correlation_id_middleware
from .cors import configure_cors
from .rate_limiter import configure_rate_limiter
from .request_logging import configure_request_logging_middleware
from .security_headers import configure_security_headers
from .trusted_host import configure_trusted_host


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
    configure_body_size_limit(app)

    # 3. CORS — handles OPTIONS preflight
    configure_cors(app)

    # 4. Rate Limiter — slowapi middleware (registered inside configure_rate_limiter)
    configure_rate_limiter(app)

    # 5. Security Headers — ASGI-level, runs after Rate Limiter
    configure_security_headers(app)

    # 6. Correlation ID — ASGI-level, runs after Security Headers
    if settings.OBSERVABILITY_MIDDLEWARE_ENABLED:
        configure_correlation_id_middleware(app)

    # 7. Request Logging — ASGI-level, runs after Correlation ID
    if settings.OBSERVABILITY_MIDDLEWARE_ENABLED:
        configure_request_logging_middleware(app)

    # 8. GZip — compression (innermost)
    configure_compression_body(app)
