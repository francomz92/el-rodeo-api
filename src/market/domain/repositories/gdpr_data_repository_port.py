"""Repository port for Market-owned GDPR unlink and export reads."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IMarketGDPRDataRepository(IRepository):
    """Market-owned GDPR data access.

    Implementations operate inside the caller's Unit of Work transaction
    boundary and never commit.
    """

    @abstractmethod
    async def unlink_user_data(self, user_id: UUID) -> None:
        """Detach the user from Market-owned business rows.

        Sets ``user_id`` to NULL on ``Buyer`` and ``Sale`` rows matching the
        user. Rows are preserved.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_buyers(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``Buyer`` rows for the user."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_sales(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``Sale`` rows for the user."""
        raise NotImplementedError
