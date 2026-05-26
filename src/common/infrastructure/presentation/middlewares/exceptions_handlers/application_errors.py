from fastapi import Request
from fastapi.responses import JSONResponse

from src.common.application.exceptions import ApplicationError
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorPayloadSchema,
    StandardErrorResponse,
)
from src.common.utils.date_utils import get_current_datetime


async def application_exception_handler(request: Request, exc: ApplicationError):
    error_response = StandardErrorResponse(
        error=ErrorPayloadSchema(
            code=exc.error_code,
            message=exc.message,
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )
