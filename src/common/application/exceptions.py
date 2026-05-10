from src.common.domain.entities.errors import ErrorDetail


class ApplicationError(Exception):
    status_code: int
    error_code: str

    def __init__(self, message: str, details: list[ErrorDetail]) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class AppValidationError(ApplicationError):
    status_code = 422
    error_code = "validation_error"
