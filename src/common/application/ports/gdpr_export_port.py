"""Repository port for GDPR data export across bounded contexts."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IGDPRExportRepository(IRepository):
    """Interface for exporting all user data across bounded contexts."""

    @abstractmethod
    async def fetch_user_profile(self, user_id: UUID) -> dict | None:
        """Return the user's profile (without password hash), or None."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_buyers(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_sales(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_animals(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_animal_protocols(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_purchases(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_animal_supplies(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_schedule_events(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_audit_log(self, user_id: UUID) -> list[dict]:
        raise NotImplementedError
