from abc import abstractmethod
from uuid import UUID

from src.auth.domain.entities import RefreshTokenEntity
from src.common.domain.repository import IRepository


class IRefreshTokenRepository(IRepository):
    @abstractmethod
    async def save(self, token: RefreshTokenEntity) -> None:
        """Persist a new refresh token entity."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, token_id: UUID) -> RefreshTokenEntity | None:
        """Look up a token by its primary key (UUID). Returns None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_token_hash(self, token_hash: str) -> RefreshTokenEntity | None:
        """Look up a token by its bcrypt hash. Returns None if not found."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_family(self, family_id: UUID) -> list[RefreshTokenEntity]:
        """Return all tokens belonging to a family (active or revoked)."""
        raise NotImplementedError

    @abstractmethod
    async def revoke_token(self, token: RefreshTokenEntity) -> None:
        """Revoke a single token."""
        raise NotImplementedError

    @abstractmethod
    async def revoke_family(self, family_id: UUID) -> None:
        """Revoke every token in a family (reuse detection)."""
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke every refresh token belonging to a user (e.g. password change)."""
        raise NotImplementedError
