import time
from uuid import UUID

from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import UnauthorizedError

# Default TTL when the token has no exp claim: 24 hours
# (matches the standard token lifetime used in LoginUserCase)
_DEFAULT_BLACKLIST_TTL = 86400


class LogoutUserCase:
    """Encapsulates the logic for invalidating a JWT token (logout).

    1. Decode the token to extract its unique ID (jti) and expiration.
    2. If the token has a jti, store it in the blacklist for the
       remaining duration of the token's validity.
    3. Revoke all refresh tokens for the authenticated user.
    """

    def __init__(
        self,
        token_service: ITokenService,
        blacklist_service: ITokenBlacklistService,
        uow: IUoW,
    ) -> None:
        self.token_service = token_service
        self.blacklist_service = blacklist_service
        self.uow = uow

    async def execute(self, token: str, refresh_token: str, close_all_sessions: bool = False) -> None:
        try:
            payload = self.token_service.decode(token)
        except InvalidCredentialError:
            return  # Already invalid, logout is a no-op

        try:
            refresh_payload = self.token_service.decode_refresh_token(refresh_token)
            refresh_token_id: str = refresh_payload.get("refresh_token_id", "")
        except InvalidCredentialError:
            return  # Already invalid, logout is a no-op

        # Blacklist the access token
        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedError("No autorizado para realizar esta acción")

        exp = payload.get("exp")
        if exp:
            now = time.time()
            remaining = max(1, int(exp - now))
        else:
            remaining = _DEFAULT_BLACKLIST_TTL

        await self.blacklist_service.blacklist(jti, remaining)

        # Revoke all refresh tokens for the user
        # TODO: Revoke all devices sessions in necessary.?
        user_id_str: str = payload.get("user_id")
        async with self.uow as uow:
            refresh_repo = uow.get_repository(IRefreshTokenRepository)
            if close_all_sessions and user_id_str:
                await refresh_repo.revoke_all_user_tokens(UUID(user_id_str))
                await uow.commit()
            else:
                refresh_t = await refresh_repo.find_by_id(token_id=UUID(refresh_token_id))
                if refresh_t:
                    await refresh_repo.revoke_token(refresh_t)
                    await uow.commit()
