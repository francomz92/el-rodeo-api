from src.common.domain.exceptions import DomainError


class InvalidCredentialError(DomainError):
    "For authentication errors (401)"

    error_code = "invalid_credentials_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
