class ApplicationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, identifier: str) -> None:
        self.message = f'{resource} "{identifier}" no encontrado'
        super().__init__(self.message)


class AlreadyExistsError(ApplicationError):
    pass