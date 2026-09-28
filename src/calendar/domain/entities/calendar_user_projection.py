from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CalendarUserProjection:
    id: UUID
    name: str
    email: str
