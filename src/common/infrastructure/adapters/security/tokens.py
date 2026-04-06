import jwt
from datetime import timedelta

from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.ports.tokens import ITokenService
from src.common.utils.date_utils import get_current_datetime


class TokenService(ITokenService):
    def __init__(self, secret: str, algorithm: str) -> None:
        self.secret = secret
        self.algorithm = algorithm

    def generate(self, data: dict, exp_minutes: int) -> str:
        payload = data.copy()
        current_datetime = get_current_datetime()
        expire_datetime = current_datetime + timedelta(minutes=exp_minutes)
        payload.update(
            {
                "exp": expire_datetime,
                "iat": current_datetime,
            }
        )
        return jwt.encode(payload, self.secret, self.algorithm)

    def decode(self, token: str):
        try:
            return jwt.decode(token, self.secret, [self.algorithm])
        except jwt.ExpiredSignatureError:
            raise InvalidCredentialError(f"Expired token: {token}")
        except jwt.InvalidTokenError:
            raise InvalidCredentialError(f"Inválid token: {token}")
