from src.common.application.exceptions import ApplicationError


class InvalidCredentialError(ApplicationError):
    "For authentication errors (401)"

    pass

class UnauthorizedError(ApplicationError):
    "For generic authentication errors (401)"

    pass