from src.common.application.exceptions import ApplicationError


class UserAlreadyExistsError(ApplicationError):
    "For registered user error when try to create a one existing (409)"

    pass
