from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.common.infrastructure.adapters.http.output.errors import (
    ErrorPayloadSchema,
    StandardErrorResponse,
)
from src.common.utils import log
from src.common.utils.date_utils import get_current_datetime


async def server_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    error_response = StandardErrorResponse(
        success=False,
        error=ErrorPayloadSchema(
            code="Internal server error",
            message=str(exc),
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    error = error_response.model_dump()
    log.error(error)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error,
    )
