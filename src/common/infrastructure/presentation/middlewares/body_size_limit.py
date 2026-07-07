"""Body size limit ASGI middleware.

Checks the ``Content-Length`` header of incoming HTTP requests against
a configurable maximum. Returns ``413 Payload Too Large`` when the body
exceeds the limit.

Must be placed early in the middleware chain (after TrustedHost, before
body is read by downstream middleware) to reject oversized payloads
before they are processed.
"""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.status import HTTP_413_CONTENT_TOO_LARGE
from starlette.types import ASGIApp, Receive, Scope, Send

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorPayloadSchema,
    StandardErrorResponse,
)
from src.common.infrastructure.core import settings as app_settings
from src.common.utils import log
from src.common.utils.date_utils import get_current_datetime


class BodySizeLimitMiddleware:
    """ASGI middleware that rejects requests with oversized bodies.

    Checks ``Content-Length`` header against a configurable maximum size.
    Returns 413 Payload Too Large with a standard error response format
    when the limit is exceeded.

    Usage::

        app.add_middleware(BodySizeLimitMiddleware, max_size=10_485_760)
    """

    def __init__(self, app: ASGIApp, max_size: int | None = None) -> None:
        self.app = app
        self.max_size = max_size or app_settings.MAX_REQUEST_BODY_SIZE

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_length = headers.get("content-length")

        if content_length is not None and int(content_length) > self.max_size:
            cid = get_correlation_id()
            log.warning(
                "Request body too large: {size} bytes (max {max})",
                size=content_length,
                max=self.max_size,
                path=str(scope.get("path", "")),
                correlation_id=cid,
            )
            response = StandardErrorResponse(
                success=False,
                error=ErrorPayloadSchema(
                    code="request_entity_too_large",
                    message=f"Request body exceeds maximum allowed size of {self.max_size} bytes",
                ),
                timestamp=get_current_datetime().isoformat(),
            )
            json_response = JSONResponse(
                status_code=HTTP_413_CONTENT_TOO_LARGE,
                content=response.model_dump(),
            )
            await json_response(scope, receive, send)
            return

        await self.app(scope, receive, send)
