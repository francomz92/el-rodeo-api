from typing import TypedDict


class ErrorDetail(TypedDict):
    field: str | None
    message: str


class ApplicationError(Exception):
    status_code: int
    error_code: str

    def __init__(self, message: str, details: list[ErrorDetail]) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundError(ApplicationError):
    status_code = 404
    error_code = "not_found_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class AlreadyExistsError(ApplicationError):
    status_code = 409
    error_code = "already_exists_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class NotPermissionError(ApplicationError):
    status_code = 403
    error_code = "permissions_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])


class BusinessValidationError(ApplicationError):
    status_code = 422
    error_code = "validation_error"


class ConflictError(ApplicationError):
    status_code = 409
    error_code = "conflict_error"

    def __init__(self, message: str) -> None:
        super().__init__(message, [])
