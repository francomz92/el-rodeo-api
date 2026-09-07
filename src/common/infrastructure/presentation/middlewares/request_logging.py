"""Request logging ASGI middleware.

Logs every incoming HTTP request (method, path, query, client IP, user
agent, correlation ID) at INFO level, then captures the response status
code and duration, logging the result at an appropriate level:

- INFO for 2xx responses
- WARNING for 4xx responses
- ERROR for 5xx responses

Must be placed AFTER the Correlation ID middleware so the correlation ID
is available when logging.

Sensitive query parameters (password, token, secret, key, etc.) are
automatically redacted — their values are replaced with ``"***"``.
"""

import time
from typing import Any
from urllib.parse import parse_qs, urlencode

from fastapi import FastAPI

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.core import settings
from src.common.utils import log


def _sanitize_query_string(raw: str) -> str:
    """Parse and redact sensitive query parameters, returning a safe string.

    Replaces values of sensitive parameter names with ``"***"``.
    Non-sensitive params are kept as-is.
    """
    if not raw:
        return ""
    parsed = parse_qs(raw, keep_blank_values=True)
    sanitized: dict[str, list[str]] = {}
    sensitive = {k.lower() for k in settings.SANITIZE_QUERY_KEYS}
    for param, values in parsed.items():
        if param.lower() in sensitive:
            sanitized[param] = ["***"] * len(values)
        else:
            sanitized[param] = values
    return urlencode(sanitized, doseq=True)


class RequestLoggingMiddleware:
    """ASGI middleware that logs HTTP request/response details.

    Usage::

        app.add_middleware(RequestLoggingMiddleware)
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ── Extract request info ────────────────────────────────────────────
        method = scope["method"]
        path = scope["path"]
        raw_query = scope.get("query_string", b"").decode()
        safe_query = _sanitize_query_string(raw_query)
        client = scope.get("client")
        client_ip = client[0] if client else ""
        raw_headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        user_agent = raw_headers.get("user-agent", "")
        cid = get_correlation_id()

        # ── Log incoming request ────────────────────────────────────────────
        log.info(
            "Request: {method} {path}",
            method=method,
            path=path,
            correlation_id=cid,
            client_ip=client_ip,
            user_agent=user_agent,
            query_string=safe_query,
        )

        # ── Capture start time and status code ──────────────────────────────
        start = time.perf_counter()
        status_code: int = 0

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        # ── Process request ─────────────────────────────────────────────────
        await self.app(scope, receive, send_wrapper)

        # ── Log response ────────────────────────────────────────────────────
        duration_ms = (time.perf_counter() - start) * 1000
        log_msg = f"Response: {method} {path} → {status_code} ({duration_ms:.0f}ms)"
        log_level = "info"
        if status_code >= 500:
            log_level = "error"
        elif status_code >= 400:
            log_level = "warning"
        getattr(log, log_level)(log_msg, correlation_id=cid, status=status_code, duration_ms=duration_ms)


def configure_request_logging_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)
