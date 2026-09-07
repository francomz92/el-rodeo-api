"""Repository port for GDPR data anonymization across bounded contexts."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IGDPRDeleteRepository(IRepository):
    """Interface for anonymizing user data across bounded contexts.

    Implementations operate within the Unit of Work transaction boundary.
    """

    @abstractmethod
    async def delete_user_data(self, user_id: UUID) -> None:
        """Anonymize all data for the given user.

        Sets user_id = NULL on business records, disables the account,
        and revokes refresh tokens. Audit log entries are preserved.
        """
        raise NotImplementedError
