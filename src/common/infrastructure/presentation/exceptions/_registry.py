from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.exceptions.user import UserAlreadyExistsError
from src.common.application.exceptions import ResourceNotFoundError


exceptions_list: dict[type[Exception], int] = {
    ResourceNotFoundError: 404,
    InvalidCredentialError: 401,
    UserAlreadyExistsError: 409,
}
