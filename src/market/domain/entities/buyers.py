from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class BuyerEntity:
    id: UUID
    tenant_id: UUID
    created_at: datetime
    name: str
    description: str = field(default_factory=str)
    contact_number: str = field(default_factory=str)
    contact_address: str = field(default_factory=str)
