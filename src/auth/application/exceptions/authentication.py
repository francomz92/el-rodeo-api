from src.common.application.exceptions import ApplicationError


class InvalidCredentialError(ApplicationError):
    "For authentication errors (401)"

    pass
