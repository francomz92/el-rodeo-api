"""Correlation ID ASGI middleware.

Reads ``X-Request-ID`` from the incoming request headers. If present and
valid (max 64 chars, alphanumeric + hyphens only) the value is reused;
otherwise a new UUID hex string is generated. The ID is stored in the
``correlation_id`` contextvar so it is available throughout the request
lifecycle and is echoed back in the response ``X-Request-ID`` header.

Must be placed as early as possible in the middleware chain so that all
downstream middleware and route handlers have access to the correlation ID.
"""

import re
from typing import Any

from fastapi import FastAPI

from src.common.infrastructure.adapters.correlation import reset_correlation_id, set_correlation_id

# Validation pattern: alphanumeric + hyphens, max 64 chars.
_VALID_CID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")


class CorrelationIdMiddleware:
    """ASGI middleware that manages request correlation IDs.

    Usage::

        app.add_middleware(CorrelationIdMiddleware)
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ── Extract or generate correlation ID ──────────────────────────────
        headers = {}
        for k, v in scope.get("headers", []):
            try:
                headers[k.decode()] = v.decode()
            except UnicodeDecodeError:
                pass  # Skip malformed header bytes
        raw_request_id = headers.get("x-request-id", "").strip()

        # Validate: only alphanumeric + hyphens, max 64 chars.
        # If invalid or missing, let set_correlation_id() generate a fresh UUID.
        if raw_request_id and _VALID_CID_RE.match(raw_request_id):
            cid, token = set_correlation_id(raw_request_id)
        else:
            cid, token = set_correlation_id()  # generates UUID hex

        # ── Wrap send to inject X-Request-ID into response headers ─────────
        async def send_with_cid(message: dict) -> None:
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-request-id", cid.encode()))
                message["headers"] = resp_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_cid)
        finally:
            reset_correlation_id(token)


def configure_correlation_id_middleware(app: FastAPI) -> None:
    app.add_middleware(CorrelationIdMiddleware)
