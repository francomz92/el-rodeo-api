from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.common.application.exceptions import (
    NotPermissionError,
    ResourceNotFoundError,
    AlreadyExistsError,
    ValidationError,
)


exceptions_list: dict[type[Exception], int] = {
    ResourceNotFoundError: 404,
    InvalidCredentialError: 401,
    AlreadyExistsError: 409,
    NotPermissionError: 403,
    ValidationError: 422,
}
