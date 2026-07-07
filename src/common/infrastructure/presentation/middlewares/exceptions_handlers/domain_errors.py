from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.common.domain.exceptions import DomainError, ErrorCode
from src.common.infrastructure.adapters.correlation import get_correlation_id
from src.common.infrastructure.adapters.http.output.errors import (
    ErrorDetailSchema,
    ErrorPayloadSchema,
    StandardErrorResponse,
    format_error_location,
)
from src.common.utils import log
from src.common.utils.date_utils import get_current_datetime

_status_code_errors: dict[ErrorCode, int] = {
    "domain_error": status.HTTP_400_BAD_REQUEST,
    "conflict_error": status.HTTP_409_CONFLICT,
    "validation_error": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "not_found_error": status.HTTP_404_NOT_FOUND,
    "permission_error": status.HTTP_403_FORBIDDEN,
    "invalid_credentials_error": status.HTTP_401_UNAUTHORIZED,
    "unauthorized_error": status.HTTP_401_UNAUTHORIZED,
    "mercadopago_error": status.HTTP_502_BAD_GATEWAY,
    "quota_exceeded_error": status.HTTP_429_TOO_MANY_REQUESTS,
    "plan_change_error": status.HTTP_400_BAD_REQUEST,
}


def domain_exception_handler(request: Request, exc: DomainError):
    cid = get_correlation_id()
    log.warning(
        "Domain error: {message}",
        message=str(exc),
        correlation_id=cid,
        code=exc.error_code,
    )
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
