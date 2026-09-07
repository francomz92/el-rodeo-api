"""Auth domain events — UserRegistered."""

from uuid import UUID

from src.common.domain.events.base import DomainEvent


class UserRegistered(DomainEvent):
    """Emitted when a new user registers and a tenant is created."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="user.registered",
            aggregate_id=aggregate_id,
            **kwargs,
        )
