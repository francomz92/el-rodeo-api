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

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.core import settings as app_settings
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
    sensitive = {k.lower() for k in app_settings.SANITIZE_QUERY_KEYS}
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

    def __init__(self, app: Any, settings: Any = None) -> None:
        self.app = app
        self.settings = settings or app_settings

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
            f"Request: {method} {path}",
            correlation_id=cid,
            client_ip=client_ip,
            user_agent=user_agent,
            query_string=safe_query,
        )

        # ── Capture start time and status code ──────────────────────────────
        start = time.perf_counter()
        status_code: list[int] = [0]

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        # ── Process request ─────────────────────────────────────────────────
        await self.app(scope, receive, send_wrapper)

        # ── Log response ────────────────────────────────────────────────────
        duration_ms = (time.perf_counter() - start) * 1000
        status = status_code[0]
        log_msg = f"Response: {method} {path} → {status} ({duration_ms:.0f}ms)"

        if status >= 500:
            log.error(log_msg, correlation_id=cid, status=status, duration_ms=duration_ms)
        elif status >= 400:
            log.warning(log_msg, correlation_id=cid, status=status, duration_ms=duration_ms)
        else:
            log.info(log_msg, correlation_id=cid, status=status, duration_ms=duration_ms)
