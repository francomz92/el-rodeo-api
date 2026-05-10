from src.common.application.exceptions import ApplicationError
from src.common.domain.entities.errors import ErrorDetail
from src.common.domain.exceptions import DomainError


class InvalidCredentialError(DomainError):
    "For authentication errors (401)"

    error_code = "invalid_credentials_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class UnauthorizedError(ApplicationError):
    "For generic authentication errors (401)"

    status_code = 401
    error_code = "unauthorized_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
