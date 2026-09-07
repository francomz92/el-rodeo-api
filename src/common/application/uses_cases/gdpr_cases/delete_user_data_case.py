"""GDPR Delete User Data Use Case.

Anonymizes all user data across bounded contexts for GDPR compliance.
Business records are anonymized (user_id → NULL), account is disabled,
and refresh tokens are revoked. Audit log entries are preserved.
"""

from __future__ import annotations

from uuid import UUID

from src.common.application.ports.gdpr_delete_port import IGDPRDeleteRepository
from src.common.application.ports.uow import IUoW


class GDPRDeleteUserDataCase:
    """Use case for anonymizing all data associated with a user.

    Follows the project pattern: receives IUoW in the constructor,
    obtains repositories via uow.get_repository(), and manages the
    transaction boundary via uow.commit().
    """

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> None:
        """Anonymize all data for the given user within a transaction."""
        async with self.uow as uow:
            repo = uow.get_repository(IGDPRDeleteRepository)
            await repo.delete_user_data(user_id)
            await uow.commit()
