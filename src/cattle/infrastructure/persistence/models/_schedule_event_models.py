from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.cattle.domain.constants.animal_scheduled_event import AnimalEventType
from src.common.infrastructure.persistence.models.base import Model
from src.common.utils.date_utils import get_current_datetime


class ScheduledEventParticipant(Model):
    __tablename__ = "scheduled_event_participants"

    id: Mapped[UUID] = mapped_column(Uuid, index=True, default=uuid4, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
    )
    event_id: Mapped[UUID] = mapped_column(ForeignKey("scheduled_events.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    event: Mapped["ScheduledEvent"] = relationship(back_populates="participant_links")
    user: Mapped["User"] = relationship(  # type: ignore  # noqa: F821
        back_populates="event_links"
    )


class ScheduledEvent(Model):
    __tablename__ = "scheduled_events"

    tenant_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(255))
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=True)
    type: Mapped[AnimalEventType] = mapped_column(
        SQLEnum(AnimalEventType, values_callable=lambda enum: [member.value for member in enum]),
        index=True,
    )
    participants: Mapped[list["User"]] = relationship(  # type: ignore    # noqa: F821
        secondary="scheduled_event_participants",
        back_populates="events",
    )
    user: Mapped["User"] = relationship()  # type: ignore   # noqa: F821

    participant_links: Mapped[list["ScheduledEventParticipant"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
