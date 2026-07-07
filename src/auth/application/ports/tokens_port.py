from abc import ABC, abstractmethod
from uuid import UUID

from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)


class ITokenService(ABC):
    @abstractmethod
    def generate(self, data: dict, exp_minutes: int) -> str:
        """Generate a JWT with the given data and expiry period."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, token: str):
        """Decode and validate a JWT. Raises on invalid/expired."""
        raise NotImplementedError

    # ── Refresh Token Methods ─────────────────────────────────────────────────

    @abstractmethod
    def generate_refresh_token(
        self,
        user_id: str,
        family_id: str | None = None,
        tenant_id: str | None = None,
    ) -> str:
        """Generate a refresh token JWT with type='refresh', refresh_token_id,
        family_id, and a long expiry (REFRESH_TOKEN_EXPIRE_DAYS).

        The refresh_token_id claim matches the DB entity's primary key for
        direct lookup without bcrypt hashing.

        When available, tenant_id is included so that rotated access tokens
        can carry the tenant context.
        """
        raise NotImplementedError

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict:
        """Decode and validate a refresh token. Raises InvalidCredentialError
        on invalid/expired tokens or if token type is not 'refresh'."""
        raise NotImplementedError

    @abstractmethod
    async def rotate_refresh_token(
        self,
        old_token: str,
        repo: IRefreshTokenRepository,
    ) -> tuple[str, str]:
        """Rotate an old refresh token, returning a new (access, refresh) pair.

        Decodes old token, checks revocation status in DB, creates new tokens
        in the same family, revokes the old token, persists the new one, and
        returns the new (access_token, refresh_token) strings.

        If the old token is already revoked, revokes the entire family
        (reuse detection) and raises InvalidCredentialError.
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_refresh_token(
        self,
        token: str,
        repo: IRefreshTokenRepository,
    ) -> None:
        """Revoke a specific refresh token by its token string."""
        raise NotImplementedError

    @abstractmethod
    async def revoke_user_refresh_tokens(
        self,
        user_id: UUID,
        repo: IRefreshTokenRepository,
    ) -> None:
        """Revoke ALL refresh tokens for a given user."""
        raise NotImplementedError
