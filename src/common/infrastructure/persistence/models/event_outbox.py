"""EventOutbox SQLAlchemy model for transactional outbox pattern.

Events are queued in memory during a use-case execution, flushed to this
table inside the UoW commit, and later consumed by a Celery periodic task
that forwards them to webhook subscribers.
"""

from enum import Enum
from uuid import UUID

from sqlalchemy import Index, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.infrastructure.persistence.models.base import Model


class OutboxStatus(str, Enum):
    """Possible states of an outbox event."""

    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class EventOutbox(Model):
    """Transactional outbox table for domain events.

    Events are inserted here during ``UnitOfWork.commit()`` and consumed
    by a background forwarder task.  The ``(status, created_at)`` index
    supports efficient ``get_pending()`` queries.
    """

    __tablename__ = "event_outbox"
    __table_args__ = (
        Index(
            "ix_event_outbox_status_created_at",
            "status",
            "created_at",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="The domain event's unique identifier (for tracing).",
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Discriminator matching DomainEvent.event_type.",
    )
    aggregate_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
        comment="Aggregate that produced the event.",
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Serialized event data forwarded to webhook subscribers.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OutboxStatus.PENDING,
        comment="PENDING | SENT | FAILED",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of delivery attempts.",
    )
