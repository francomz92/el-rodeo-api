import time

from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.auth.application.ports.tokens_port import ITokenService
from src.common.domain.exceptions import UnauthorizedError

# Default TTL when the token has no exp claim: 24 hours
# (matches the standard token lifetime used in LoginUserCase)
_DEFAULT_BLACKLIST_TTL = 86400


class LogoutUserCase:
    """Encapsulates the logic for invalidating a JWT token (logout).

    1. Decode the token to extract its unique ID (jti) and expiration.
    2. If the token has a jti, store it in the blacklist for the
       remaining duration of the token's validity.
    3. Tokens without jti (pre-migration) cannot be individually revoked.
    """

    def __init__(
        self,
        token_service: ITokenService,
        blacklist_service: ITokenBlacklistService,
    ) -> None:
        self.token_service = token_service
        self.blacklist_service = blacklist_service

    async def execute(self, token: str) -> None:
        payload = self.token_service.decode(token)

        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedError("No autorizado para realizar esta acción")

        exp = payload.get("exp")
        if exp:
            # Always at least 1s to avoid silent no-op on sub-second expiry.
            now = time.time()
            remaining = max(1, int(exp - now))
        else:
            # Token has no exp — fall back to the standard lifetime.
            remaining = _DEFAULT_BLACKLIST_TTL

        await self.blacklist_service.blacklist(jti, remaining)
