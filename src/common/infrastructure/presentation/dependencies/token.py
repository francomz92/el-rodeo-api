from typing import Annotated

from fastapi import Depends

from src.auth.application.ports.tokens_port import ITokenService
from src.common.infrastructure.adapters.security.tokens import TokenService
from src.common.infrastructure.core import settings


def _get_token_service():
    return TokenService(secret=settings.SECRET, algorithm=settings.JWT_ALGORITHM)


GetTokenService = Annotated[ITokenService, Depends(_get_token_service)]
