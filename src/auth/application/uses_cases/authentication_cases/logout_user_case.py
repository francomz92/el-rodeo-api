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

    Degrades gracefully when either credential is missing or invalid:

    1. Revoke the refresh token first (independent of access-token state).
    2. Blacklist the access token's jti for its remaining TTL
       (independent of refresh-token state).
    3. Revoke refresh-token records: all user sessions when
       ``close_all_sessions`` is set, otherwise the single token.
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

    async def execute(self, token: str | None, refresh_token: str, close_all_sessions: bool = False) -> None:
        # 1. Revoke the refresh token — best effort, first. An expired or
        #    garbage access token must never keep the refresh token alive
        #    after an explicit logout.
        refresh_token_id: str | None = None
        refresh_user_id: str | None = None
        if refresh_token:
            try:
                refresh_payload = self.token_service.decode_refresh_token(refresh_token)
            except InvalidCredentialError:
                refresh_payload = None  # missing/malformed/expired → skip revocation
            if refresh_payload is not None:
                refresh_token_id = refresh_payload.get("refresh_token_id") or None
                refresh_user_id = refresh_payload.get("user_id") or None

        # 2. Blacklist the access token — best effort, independent of the
        #    refresh token state.
        access_user_id: str | None = None
        if token:
            try:
                payload = self.token_service.decode(token)
            except InvalidCredentialError:
                payload = None  # already invalid → nothing to blacklist
            if payload is not None:
                access_user_id = payload.get("user_id") or None
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

        # 3. Revoke the refresh-token records. Prefer the refresh payload's
        #    user_id; fall back to the access token's.
        #    TODO: Revoke all devices sessions in necessary.?
        user_id_str: str | None = refresh_user_id or access_user_id
        user_id = UUID(user_id_str) if user_id_str else None
        async with self.uow as uow:
            refresh_repo = uow.get_repository(IRefreshTokenRepository)
            if close_all_sessions and user_id is not None:
                await refresh_repo.revoke_all_user_tokens(user_id)
                await uow.commit()
            elif refresh_token_id:
                refresh_t = await refresh_repo.find_by_id(token_id=UUID(refresh_token_id))
                if refresh_t:
                    await refresh_repo.revoke_token(refresh_t)
                    await uow.commit()
