from src.common.domain.entities.errors import ErrorCode, ErrorDetail


class DomainError(Exception):
    error_code: ErrorCode

    def __init__(self, message: str, details: list[ErrorDetail]) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class DuplicatedError(DomainError):
    error_code = "conflict_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class NotFoundError(DomainError):
    error_code = "not_found_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class NotPermissionError(DomainError):
    error_code = "permission_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class UnauthorizedError(DomainError):
    error_code = "unauthorized_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class ConflictError(DomainError):
    error_code = "conflict_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class BusinessValidationError(DomainError):
    error_code = "validation_error"
