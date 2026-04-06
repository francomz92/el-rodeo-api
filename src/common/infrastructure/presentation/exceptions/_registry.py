from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.common.application.exceptions import ResourceNotFoundError


exceptions_list: dict[type[Exception], int] = {
    ResourceNotFoundError: 404,
    InvalidCredentialError: 401,
}
