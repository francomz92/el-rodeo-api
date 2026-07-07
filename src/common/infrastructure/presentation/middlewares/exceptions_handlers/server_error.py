from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorPayloadSchema,
    StandardErrorResponse,
)
from src.common.utils import log
from src.common.utils.date_utils import get_current_datetime


async def server_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    cid = get_correlation_id()
    log.exception(
        "Internal server error — {path}",
        path=str(request.url.path),
        correlation_id=cid,
    )
    error_response = StandardErrorResponse(
        success=False,
        error=ErrorPayloadSchema(
            code="server_error",
            message="Error interno del servidor",
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    error = error_response.model_dump()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error,
    )
