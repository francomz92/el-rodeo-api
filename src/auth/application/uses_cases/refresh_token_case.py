from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.common.application.ports.uow import IUoW


class RefreshTokenCase:
    """Validates a refresh token and rotates it, returning a new token pair.

    Delegates the actual rotation logic (including reuse detection) to
    TokenService.rotate_refresh_token(), which handles JWT decoding,
    DB lookups, and token family management.
    """

    def __init__(
        self,
        token_service: ITokenService,
        uow: IUoW,
    ) -> None:
        self.token_service = token_service
        self.uow = uow

    async def execute(self, refresh_token: str) -> tuple[str, str]:
        """Validate and rotate a refresh token.

        Args:
            refresh_token: The raw refresh token JWT string.

        Returns:
            A tuple of (new_access_token, new_refresh_token).

        Raises:
            InvalidCredentialError: If the token is invalid, expired,
                or part of a revoked family (reuse detection).
        """
        async with self.uow as uow:
            repo = uow.get_repository(IRefreshTokenRepository)
            result = await self.token_service.rotate_refresh_token(
                refresh_token,
                repo,
            )
            await uow.commit()
            return result
