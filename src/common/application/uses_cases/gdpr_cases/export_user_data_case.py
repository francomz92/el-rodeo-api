"""GDPR Export User Data Use Case.

Collects all user data across bounded contexts for GDPR export.
Returns a structured dictionary suitable for JSON serialization.
"""

from __future__ import annotations

from uuid import UUID

from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.calendar.domain.repositories.gdpr_data_repository_port import (
    ICalendarGDPRDataRepository,
)
from src.cattle.domain.repositories.gdpr_data_repository_port import (
    ICattleGDPRDataRepository,
)
from src.common.application.ports.audit_log_query_port import IAuditLogQueryRepository
from src.common.application.ports.uow import IUoW
from src.finance.domain.repositories.gdpr_data_repository_port import (
    IFinanceGDPRDataRepository,
)
from src.market.domain.repositories.gdpr_data_repository_port import (
    IMarketGDPRDataRepository,
)


class GDPRExportUserDataCase:
    """Use case for collecting all data associated with a user.

    Follows the project pattern: receives IUoW in the constructor,
    obtains repositories via uow.get_repository(). All reads run against
    the same Unit of Work session and never commit.
    """

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, user_id: UUID) -> dict | None:
        """Collect all data for the given user.

        Returns None when the user profile is not found.
        """
        async with self.uow as uow:
            user = await uow.get_repository(IUserRepository).get_by_id(user_id)
            if user is None:
                return None

            market = uow.get_repository(IMarketGDPRDataRepository)
            cattle = uow.get_repository(ICattleGDPRDataRepository)
            finance = uow.get_repository(IFinanceGDPRDataRepository)
            calendar = uow.get_repository(ICalendarGDPRDataRepository)
            audit_log = uow.get_repository(IAuditLogQueryRepository)

            return {
                "user_profile": {
                    "id": user.id,
                    "name": user.name,
                    "dni": user.dni,
                    "email": user.email,
                    "role": str(user.role),
                    "created_at": user.created_at,
                },
                "buyers": await market.fetch_buyers(user_id),
                "sales": await market.fetch_sales(user_id),
                "animals": await cattle.fetch_animals(user_id),
                "animal_protocols": await cattle.fetch_animal_protocols(user_id),
                "purchases": await finance.fetch_purchases(user_id),
                "animal_supplies": await finance.fetch_animal_supplies(user_id),
                "schedule_events": await calendar.fetch_schedule_events(user_id),
                "audit_log": await audit_log.fetch_audit_log(user_id),
            }
