"""Repository port for Finance-owned GDPR unlink and export reads."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IFinanceGDPRDataRepository(IRepository):
    """Finance-owned GDPR data access.

    Implementations operate inside the caller's Unit of Work transaction
    boundary and never commit.
    """

    @abstractmethod
    async def unlink_user_data(self, user_id: UUID) -> None:
        """Detach the user from Finance-owned business rows.

        Sets ``user_id`` to NULL on ``Purchase`` and ``AnimalSupply`` rows
        matching the user. Rows are preserved.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_purchases(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``Purchase`` rows for the user."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_animal_supplies(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``AnimalSupply`` rows for the user."""
        raise NotImplementedError
