from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.common.domain.exceptions import DomainError, ErrorCode
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorDetailSchema,
    ErrorPayloadSchema,
    StandardErrorResponse,
    format_error_location,
)
from src.common.utils.date_utils import get_current_datetime

_status_code_errors: dict[ErrorCode, int] = {
    "conflict_error": status.HTTP_409_CONFLICT,
    "validation_error": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "not_found_error": status.HTTP_404_NOT_FOUND,
    "permission_error": status.HTTP_403_FORBIDDEN,
    "invalid_credentials_error": status.HTTP_401_UNAUTHORIZED,
    "unauthorized_error": status.HTTP_401_UNAUTHORIZED,
}


def domain_exception_handler(request: Request, exc: DomainError):
    status_code = _status_code_errors[exc.error_code]
    details = [
        ErrorDetailSchema(
            field=format_error_location((error.get("field", ""),)),
            message=error.get("message", "Error de validación"),
        )
        for error in exc.details
    ]
    error_response = StandardErrorResponse(
        error=ErrorPayloadSchema(
            code=exc.error_code,
            message=exc.message,
            details=details,
        ),
        timestamp=get_current_datetime().isoformat(),
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )
