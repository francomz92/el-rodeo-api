from src.common.application.exceptions import ApplicationError


class InvalidCredentialError(ApplicationError):
    "For authentication errors (401)"
    
    status_code = 401
    error_code = "invalid_credentials_error"


class UnauthorizedError(ApplicationError):
    "For generic authentication errors (401)"

    status_code = 401
    error_code = "unauthorized_error"
