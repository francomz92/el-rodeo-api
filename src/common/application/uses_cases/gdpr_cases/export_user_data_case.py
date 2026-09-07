"""GDPR Export User Data Use Case.

Collects all user data across bounded contexts for GDPR export.
Returns a structured dictionary suitable for JSON serialization.
"""

from __future__ import annotations

from uuid import UUID

from src.common.application.ports.gdpr_export_port import IGDPRExportRepository
from src.common.application.ports.uow import IUoW


class GDPRExportUserDataCase:
    """Use case for collecting all data associated with a user.

    Follows the project pattern: receives IUoW in the constructor,
    obtains repositories via uow.get_repository().
    """

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> dict | None:
        """Collect all data for the given user.

        Returns None when the user profile is not found.
        """
        async with self.uow as uow:
            repo = uow.get_repository(IGDPRExportRepository)
            user_profile = await repo.fetch_user_profile(user_id)
            if user_profile is None:
                return None

            return {
                "user_profile": user_profile,
                "buyers": await repo.fetch_buyers(user_id),
                "sales": await repo.fetch_sales(user_id),
                "animals": await repo.fetch_animals(user_id),
                "animal_protocols": await repo.fetch_animal_protocols(user_id),
                "purchases": await repo.fetch_purchases(user_id),
                "animal_supplies": await repo.fetch_animal_supplies(user_id),
                "schedule_events": await repo.fetch_schedule_events(user_id),
                "audit_log": await repo.fetch_audit_log(user_id),
            }
