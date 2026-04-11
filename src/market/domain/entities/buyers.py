from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.auth.domain.entities import UserEntity


@dataclass
class BuyerEntity:
    id: UUID
    user_id: UUID
    created_at: datetime
    name: str
    description: str = field(default_factory=str)
    contact_number: str = field(default_factory=str)
    contact_address: str = field(default_factory=str)

    user: UserEntity | None = None
