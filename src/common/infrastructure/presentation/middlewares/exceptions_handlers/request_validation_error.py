from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.common.infrastructure.adapters.http.output.errors import (
    ErrorDetailSchema,
    ErrorPayloadSchema,
    StandardErrorResponse,
    format_error_location,
)
from src.common.utils.date_utils import get_current_datetime


async def _request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [
        ErrorDetailSchema(
            field=format_error_location(error.get("loc")),
            message=error.get("msg", "Error de validación"),
        )
        for error in exc.errors()
    ]
    error_response = StandardErrorResponse(
        success=False,
        error=ErrorPayloadSchema(
            code="validation_error",
            message="Error de validación",
            details=details,
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": error_response.model_dump()},
    )
