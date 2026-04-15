class ApplicationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(ApplicationError):
    pass


class AlreadyExistsError(ApplicationError):
    pass
