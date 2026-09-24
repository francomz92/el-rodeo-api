from typing import Protocol
from uuid import UUID

from src.common.application.ports.uow import IUoW


class ITrialProvisioner(Protocol):
    """Provision a tenant trial within the caller's unit of work."""

    async def provision_trial(self, tenant_id: UUID, uow: IUoW) -> None:
        """Provision a trial using repositories from the active transaction."""
        ...
