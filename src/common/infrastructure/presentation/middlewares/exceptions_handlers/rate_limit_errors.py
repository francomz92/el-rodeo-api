from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorDetailSchema,
    ErrorPayloadSchema,
    StandardErrorResponse,
)
from src.common.infrastructure.presentation.middlewares.ip_utils import get_client_ip
from src.common.utils import log
from src.common.utils.date_utils import get_current_datetime


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom 429 handler that includes a Retry-After header."""
    cid = get_correlation_id()
    log.warning(
        "Rate limit exceeded: {path}",
        path=request.url.path,
        correlation_id=cid,
        client_ip=get_client_ip(request),
    )
    details = [
        ErrorDetailSchema(
            field="rate_limit",
            message="Limite de intentos excedido, intente nuevamente en unos minutos.",
        )
    ]
    error_response = StandardErrorResponse(
        success=False,
        error=ErrorPayloadSchema(
            code="rate_limit_exceeded_error",
            message="Limite de intentos superado",
            details=details,
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    return JSONResponse(
        status_code=429,
        content=error_response.model_dump(),
        headers={"Retry-After": "60"},
    )
