"""Repository port for Cattle-owned GDPR unlink and export reads."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class ICattleGDPRDataRepository(IRepository):
    """Cattle-owned GDPR data access.

    Implementations operate inside the caller's Unit of Work transaction
    boundary and never commit.
    """

    @abstractmethod
    async def unlink_user_data(self, user_id: UUID) -> None:
        """Detach the user from Cattle-owned business rows.

        Sets ``user_id`` to NULL on ``Animal`` and ``AnimalProtocols`` rows
        matching the user. Rows are preserved.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_animals(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``Animal`` rows for the user."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_animal_protocols(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``AnimalProtocols`` rows for the user."""
        raise NotImplementedError
