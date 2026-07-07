"""DomainEvent base dataclass.

All domain events inherit from this frozen dataclass, which provides
common fields: event_id (auto-generated UUID), aggregate_id,
event_type, timestamp (UTC now), and metadata (optional dict).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Attributes:
        event_id:    Auto-generated UUID (unique per event instance).
        aggregate_id: UUID of the aggregate that produced the event.
        event_type:  String discriminator (e.g. ``"animal.created"``).
        timestamp:   UTC datetime set at creation time.
        metadata:    Optional key/value bag (defaults to empty dict).
    """

    event_id: UUID = field(default_factory=uuid4)
    aggregate_id: UUID = field(default=UUID(int=0))
    event_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
