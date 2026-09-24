from uuid import UUID

from src.common.domain.events.base import DomainEvent


class TenantRegistered(DomainEvent):
    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ):
        super().__init__(
            event_type="tenant.registered",
            aggregate_id=aggregate_id,
            **kwargs,
        )
